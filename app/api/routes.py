"""FastAPI route handlers for IP-SAKTI Sahayak with Multilingual Translation, SSE Stage Streaming, Token Streaming, and Corpus Provenance."""

import csv
import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal, AsyncGenerator, Tuple
from urllib.parse import unquote, quote
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator

from app.classification.tree import (
    classify_formulation,
    get_next_question,
    CLASSIFICATION_CITATIONS,
)
from app.retrieval.retrieve import retrieve
from app.llm.client import get_completion, stream_completion
from app.llm.prompts import SYSTEM_PROMPT
from app.translation.bhashini import translate_text as bhashini_translate
from app.db.session_store import get_default_session_store

logger = logging.getLogger("IP-SAKTI.API")

router = APIRouter()

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "manifest.csv"
CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "corpus"
FEEDBACK_LOG_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "feedback_log.csv"


class IncrementalAnswerExtractor:
    """Extracts answer text incrementally from LLM JSON tokens while skipping JSON formatting."""
    def __init__(self):
        self.accumulated = ""
        self.in_answer = False
        self.done_answer = False
        self.escaped = False

    def feed(self, delta: str) -> str:
        if self.done_answer or not delta:
            return ""
        self.accumulated += delta
        if not self.in_answer:
            idx = self.accumulated.find('"answer"')
            if idx != -1:
                colon_idx = self.accumulated.find(":", idx + 8)
                if colon_idx != -1:
                    quote_idx = self.accumulated.find('"', colon_idx + 1)
                    if quote_idx != -1:
                        self.in_answer = True
                        rem = self.accumulated[quote_idx + 1:]
                        self.accumulated = ""
                        return self._process_answer_chunk(rem)
            # If plain text without JSON after 50 chars, pass through as direct text
            if len(self.accumulated) > 50 and not self.accumulated.strip().startswith("{"):
                self.in_answer = True
                rem = self.accumulated
                self.accumulated = ""
                return rem
            return ""
        else:
            return self._process_answer_chunk(delta)

    def _process_answer_chunk(self, chunk: str) -> str:
        out = []
        for char in chunk:
            if self.escaped:
                if char == "n":
                    out.append("\n")
                elif char == "t":
                    out.append("\t")
                elif char == '"':
                    out.append('"')
                elif char == "\\":
                    out.append("\\")
                else:
                    out.append(char)
                self.escaped = False
            elif char == "\\":
                self.escaped = True
            elif char == '"':
                self.in_answer = True
                self.done_answer = True
                break
            else:
                out.append(char)
        return "".join(out)


class CreateConversationRequest(BaseModel):
    """Payload to initialize a new conversation thread."""
    title: str = Field(default="New Inquiry", description="Conversation title")
    jurisdiction: Literal["national", "international"] = Field(default="national")


class ChatMessagePayload(BaseModel):
    """Payload representing a single message in the conversational history."""
    role: str = Field(..., description="'user' | 'assistant' | 'system'")
    content: str = Field(..., description="Message text content")
    citations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Statutory citations if assistant message")
    language: Optional[str] = Field(default=None, description="Language code")
    isError: Optional[bool] = Field(default=False)
    needs_classification: Optional[bool] = Field(default=False)


class AskRequest(BaseModel):
    """Request payload for /ask endpoint."""
    query: str = Field(..., description="User query or legal question")
    jurisdiction: Literal["national", "international"] = Field(
        default="national",
        description="Target legal jurisdiction ('national' or 'international')",
    )
    formulation_answers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Answers to the formulation classification decision tree",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation thread ID",
    )
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of previous conversation messages for multi-turn context and follow-up translations",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace-only.")
        return v.strip()


class FeedbackRequest(BaseModel):
    """Payload for submitting answer feedback (thumbs up / thumbs down)."""
    conversation_id: Optional[str] = Field(default=None, description="Conversation thread ID")
    query: Optional[str] = Field(default=None, description="User question or prompt")
    answer_snippet: Optional[str] = Field(default=None, description="Snippet or text of assistant response")
    citations: Optional[List[Any]] = Field(default_factory=list, description="Citations associated with response")
    rating: Literal["up", "down"] = Field(..., description="Feedback rating: 'up' or 'down'")
    comment: Optional[str] = Field(default=None, description="Optional user comment or reason")


def parse_translation_followup(
    query: str,
    history: Optional[List[Dict[str, Any]]] = None,
    english_query: Optional[str] = None,
) -> Optional[Tuple[str, str, str, List[Dict[str, Any]]]]:
    """Detects if the user query is asking to translate/rephrase the previous assistant response.

    Returns:
        Tuple of (target_lang_code, target_lang_name, text_to_translate, citations) if matched, else None.
    """
    if not history:
        return None

    last_assistant_msg = None
    for msg in reversed(history):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "assistant" and content and not msg.get("isError") and not msg.get("needs_classification"):
            last_assistant_msg = msg
            break

    if not last_assistant_msg:
        return None

    text_to_translate = last_assistant_msg.get("content", "").strip()
    citations = last_assistant_msg.get("citations", [])

    search_texts = [query.lower().strip()]
    if english_query and english_query.lower().strip() != query.lower().strip():
        search_texts.append(english_query.lower().strip())

    # 1. English translation request patterns
    english_patterns = [
        r"(?:convert|translate|give|explain|show|write|rephrase|tell|provide).*(?:above|previous|last|that|it|this|response|answer|message).*(?:in|to|into)\s*(?:english|eng|angrezi)",
        r"(?:in|to|into)\s*(?:english|eng|angrezi)\s*(?:please|plz)?$",
        r"(?:english|angrezi)\s*(?:please|translation|me|mein|version|variant)?$",
        r"translate\s+(?:the\s+)?(?:above|previous|this|that|it)?\s*(?:response|answer)?\s*(?:to|in|into)?\s*english",
        r"convert\s+(?:the\s+)?(?:above|previous|this|that|it)?\s*(?:response|answer)?\s*(?:to|in|into)?\s*english",
        r"अंग्रेजी में",
        r"अंग्रेज़ी में",
        r"अंग्रेजी अनुवाद",
        r"अंग्रेज़ी अनुवाद",
        r"उपरोक्त.*अंग्रेजी",
        r"उपरोक्त.*अंग्रेज़ी",
    ]
    for st in search_texts:
        for pat in english_patterns:
            if re.search(pat, st):
                return ("en", "English", text_to_translate, citations)

    # 2. Hindi translation request patterns
    hindi_patterns = [
        r"(?:convert|translate|give|explain|show|write|rephrase|tell|provide).*(?:above|previous|last|that|it|this|response|answer|message).*(?:in|to|into)\s*(?:hindi|हिंदी|हिन्दी)",
        r"(?:in|to|into)\s*(?:hindi|हिंदी|हिन्दी)\s*(?:please|plz)?$",
        r"(?:hindi|हिंदी|हिन्दी)\s*(?:please|translation|me|mein|version|variant)?$",
        r"translate\s+(?:the\s+)?(?:above|previous|this|that|it)?\s*(?:response|answer)?\s*(?:to|in|into)?\s*hindi",
        r"convert\s+(?:the\s+)?(?:above|previous|this|that|it)?\s*(?:response|answer)?\s*(?:to|in|into)?\s*hindi",
        r"हिंदी में",
        r"हिन्दी में",
        r"हिंदी अनुवाद",
        r"हिन्दी अनुवाद",
        r"उपरोक्त.*हिंदी",
        r"उपरोक्त.*हिन्दी",
    ]
    for st in search_texts:
        for pat in hindi_patterns:
            if re.search(pat, st):
                return ("hi", "Hindi", text_to_translate, citations)

    return None


# ==============================================================================
# In-Memory Multi-Turn Conversation Memory (PROMPT 1)
# ==============================================================================
CONVERSATION_MEMORY: Dict[str, List[Dict[str, Any]]] = {}
MAX_MEMORY_TURNS = 3

FOLLOWUP_PATTERNS = [
    r"(?i)\b(?:what|how)\s+about\b",
    r"(?i)\bwhat\s+if\b",
    r"(?i)\binstead\b",
    r"(?i)\bdoes\s+(?:that|this)\s+also\s+apply\b",
    r"(?i)\band\s+for\b",
    r"(?i)\bcompare\s+(?:that|this|it)\b",
    r"(?i)\bcan\s+(?:it|that|this)\s+be\b",
    r"(?i)\bis\s+(?:it|that|this)\s+(?:also|different)\b",
]


def record_turn_in_memory(
    conversation_id: str,
    query: str,
    answer: str,
    citations: Optional[List[Any]] = None,
) -> None:
    """Stores the last 2-3 turns (query + answer summary) per conversation_id in memory."""
    if not conversation_id:
        return
    if conversation_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[conversation_id] = []

    # Concise summary of answer (first 280 characters / key statutory sentence)
    clean_lines = [line.strip() for line in answer.strip().split("\n") if line.strip()]
    first_line = clean_lines[0] if clean_lines else answer.strip()
    if len(first_line) > 280:
        first_line = first_line[:280] + "..."

    citation_names = []
    if citations:
        for c in citations:
            if isinstance(c, dict) and c.get("section"):
                citation_names.append(c["section"])
            elif isinstance(c, str):
                citation_names.append(c)

    CONVERSATION_MEMORY[conversation_id].append({
        "query": query.strip(),
        "answer_summary": first_line,
        "citations": citation_names[:3],
    })

    # Keep only the last 2-3 turns
    if len(CONVERSATION_MEMORY[conversation_id]) > MAX_MEMORY_TURNS:
        CONVERSATION_MEMORY[conversation_id] = CONVERSATION_MEMORY[conversation_id][-MAX_MEMORY_TURNS:]


def get_memory_context(conversation_id: Optional[str]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Retrieves short context summary of prior turn(s) for the given conversation_id."""
    if not conversation_id:
        return "", None

    turns = CONVERSATION_MEMORY.get(conversation_id, [])

    # If in-memory is empty, fall back to hydrating from SQLite session store
    if not turns:
        try:
            store = get_default_session_store()
            conv = store.get_conversation(conversation_id)
            if conv and conv.get("messages"):
                msgs = conv["messages"]
                # Reconstruct turns from messages
                turn_q = None
                for m in msgs:
                    if m.get("role") == "user":
                        turn_q = m.get("content", "")
                    elif m.get("role") == "assistant" and turn_q:
                        ans = m.get("content", "")
                        clean_lines = [l.strip() for l in ans.strip().split("\n") if l.strip()]
                        summary = clean_lines[0] if clean_lines else ans
                        if len(summary) > 280:
                            summary = summary[:280] + "..."
                        citations = [c.get("section") for c in m.get("citations", []) if isinstance(c, dict) and c.get("section")]
                        turns.append({
                            "query": turn_q,
                            "answer_summary": summary,
                            "citations": citations[:3],
                        })
                        turn_q = None
                if turns:
                    CONVERSATION_MEMORY[conversation_id] = turns[-MAX_MEMORY_TURNS:]
                    turns = CONVERSATION_MEMORY[conversation_id]
        except Exception as e:
            logger.debug(f"Hydrating memory from SQLite skipped: {e}")

    if not turns:
        return "", None

    lines = ["PREVIOUS CONVERSATION CONTEXT (Prior Turns):"]
    for idx, t in enumerate(turns, 1):
        lines.append(f"Turn {idx}:")
        lines.append(f"  User Question: \"{t['query']}\"")
        lines.append(f"  Assistant Summary: \"{t['answer_summary']}\"")
        if t.get("citations"):
            lines.append(f"  Key Legal Provisions: {', '.join(t['citations'])}")
    lines.append("")

    return "\n".join(lines) + "\n", turns[-1]


def contextualize_query_with_memory(
    query: str,
    last_turn: Optional[Dict[str, Any]],
    jurisdiction: str = "national",
) -> str:
    """Enriches an anaphoric or comparative follow-up query with prior legal context without cross-jurisdiction leakage."""
    if not last_turn:
        return query

    q_lower = query.lower().strip()
    words = q_lower.split()
    is_followup = any(re.search(pat, q_lower) for pat in FOLLOWUP_PATTERNS) or (
        len(words) <= 8 and any(w in words for w in ["it", "that", "this", "instead", "same", "different", "also"])
    )

    if is_followup:
        prior_q = last_turn.get("query", "")
        clean_prior = re.sub(r"[?!.,]", "", prior_q).strip()
        if jurisdiction.lower() == "international":
            return f"{query} (Prior subject: protection and patentability of {clean_prior} under international treaties TRIPS CBD Nagoya Protocol WIPO GRATK)"
        else:
            return f"{query} (Prior subject from turn: {clean_prior} patentability criteria comparison)"

    return query


# ==============================================================================
# Manifest Official Registry URL & PDF Resolution (PROMPT 2 + PDF Viewing)
# ==============================================================================
_CACHED_MANIFEST_URLS: Optional[Dict[str, str]] = None


def get_manifest_official_urls() -> Dict[str, str]:
    """Reads manifest.csv and returns normalized mapping of sources/titles/prefixes to official URLs."""
    global _CACHED_MANIFEST_URLS
    if _CACHED_MANIFEST_URLS is not None:
        return _CACHED_MANIFEST_URLS

    urls: Dict[str, str] = {}
    if not MANIFEST_PATH.exists():
        return urls

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("official_url", "").strip()
                if not url:
                    continue
                title = row.get("title", "").strip().lower()
                prefix = row.get("citation_prefix", "").strip().lower()
                doc_id = row.get("id", "").strip().lower()
                filename = row.get("filename", "").strip().lower()
                if title:
                    urls[title] = url
                if prefix:
                    urls[prefix] = url
                if doc_id:
                    urls[doc_id] = url
                if filename:
                    urls[filename] = url
        _CACHED_MANIFEST_URLS = urls
    except Exception as e:
        logger.warning(f"Error loading manifest URLs: {e}")
    return urls


def find_pdf_file(requested: str) -> Optional[Path]:
    """Finds matching statutory or treaty PDF file in data/corpus/."""
    if not CORPUS_DIR.exists():
        return None

    clean_name = unquote(requested).strip()

    # 1. Direct path check
    direct = CORPUS_DIR / clean_name
    if direct.is_file() and direct.suffix.lower() == ".pdf":
        return direct

    # 2. Check in national and international subfolders
    for sub in ["national", "international"]:
        cand = CORPUS_DIR / sub / clean_name
        if cand.is_file():
            return cand

    # 3. Match by basename
    base_name = Path(clean_name).name.lower()
    for p in CORPUS_DIR.rglob("*.pdf"):
        if p.name.lower() == base_name:
            return p

    # 4. Keyword / statute nickname resolution
    norm = clean_name.lower()
    kw_to_file = [
        ("pct", "PCT (Patent Cooperation Treaty).pdf"),
        ("patent", "Patents Act, 1970.pdf"),
        ("gratk", "WIPO GRATK Treaty (2024).pdf"),
        ("nagoya", "Nagoya Protocol.pdf"),
        ("trips", "trips_agreement.pdf"),
        ("cbd", "Convention on Biological Diversity (CBD).pdf"),
        ("magic remedies", "Drugs and Magic Remedies (Objectionable Advertisements) Act.pdf"),
        ("dmr", "Drugs and Magic Remedies (Objectionable Advertisements) Act.pdf"),
        ("aahara", "Gazette_Notification_Ayurveda_Aahara.pdf"),
        ("fssai", "Gazette_Notification_Ayurveda_Aahara.pdf"),
        ("phytopharmaceutical", "Phytopharmaceutical-Drugs-General-Guidance-for-Development.pdf"),
        ("ipc", "Phytopharmaceutical-Drugs-General-Guidance-for-Development.pdf"),
        ("2025", "The Biological Diversity (Amendment) Rules, 2025.pdf"),
        ("bd rules", "The Biological Diversity Rules, 2024.pdf"),
        ("biological diversity", "Biological Diversity (Amendment) Act, 2023.pdf"),
        ("bda", "Biological Diversity (Amendment) Act, 2023.pdf"),
        ("biodiversity", "Biological Diversity (Amendment) Act, 2023.pdf"),
        ("drug", "2016DrugsandCosmeticsAct1940Rules1945.pdf"),
        ("cosmetic", "2016DrugsandCosmeticsAct1940Rules1945.pdf"),
        ("d&c", "2016DrugsandCosmeticsAct1940Rules1945.pdf"),
        ("trademark", "The Trade Marks Act, 1999.pdf"),
        ("trade mark", "The Trade Marks Act, 1999.pdf"),
        ("copyright", "The Copyright Act, 1957.pdf"),
        ("geographical", "Geographical Indications of Goods.pdf"),
        ("gi act", "Geographical Indications of Goods.pdf"),
        ("design", "The Designs Act, 2000 (Act No. 16 of 2000).pdf"),
    ]
    for kw, fname in kw_to_file:
        if kw in norm:
            for p in CORPUS_DIR.rglob(fname):
                if p.is_file():
                    return p

    return None


def resolve_citation_pdf(
    source_str: str,
    section_str: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    """Resolves (pdf_filename, pdf_url) for a given citation from chunks or text lookup."""
    # 1. Direct match in retrieved chunks
    if chunks:
        sec_norm = section_str.lower().strip()
        for ch in chunks:
            ch_sec = str(ch.get("section", "")).lower().strip()
            if ch_sec and (ch_sec in sec_norm or sec_norm in ch_sec):
                fn = ch.get("filename")
                if fn:
                    p = find_pdf_file(fn)
                    if p:
                        return p.name, f"http://localhost:8000/pdf/{quote(p.name)}"

    # 2. Text match from source and section
    combined = f"{source_str} {section_str}"
    p = find_pdf_file(combined)
    if p:
        return p.name, f"http://localhost:8000/pdf/{quote(p.name)}"

    # 3. Default fallback to Patents Act, 1970
    return "Patents Act, 1970.pdf", f"http://localhost:8000/pdf/{quote('Patents Act, 1970.pdf')}"


def resolve_citation_url(source_str: str, section_str: str, chunks: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """Resolves the official registry URL for a given citation from manifest and retrieved chunks."""
    manifest_urls = get_manifest_official_urls()

    # 1. Check direct match in retrieved chunks
    if chunks:
        sec_norm = section_str.lower().strip()
        for ch in chunks:
            ch_sec = str(ch.get("section", "")).lower().strip()
            if ch_sec and (ch_sec in sec_norm or sec_norm in ch_sec):
                ch_title = str(ch.get("title", "")).lower().strip()
                if ch_title in manifest_urls:
                    return manifest_urls[ch_title]
                ch_prefix = str(ch.get("citation_prefix", "")).lower().strip()
                if ch_prefix in manifest_urls:
                    return manifest_urls[ch_prefix]

    # 2. Match against source_str
    s_lower = source_str.lower().strip()
    if s_lower in manifest_urls:
        return manifest_urls[s_lower]

    # 3. Match against known statutory keyword patterns
    keyword_map = [
        ("pct", "https://www.wipo.int/pct/en/texts/"),
        ("patent", "https://www.indiacode.nic.in/handle/123456789/1392"),
        ("gratk", "https://www.wipo.int/gratk/en/"),
        ("nagoya", "https://www.cbd.int/abs/text/"),
        ("trips", "https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm"),
        ("cbd", "https://www.cbd.int/convention/text/"),
        ("magic remedies", "https://www.indiacode.nic.in/handle/123456789/1429"),
        ("dmr", "https://www.indiacode.nic.in/handle/123456789/1429"),
        ("biological diversity rules", "http://nbaindia.org/"),
        ("biological diversity", "https://www.indiacode.nic.in/handle/123456789/2056"),
        ("bda", "https://www.indiacode.nic.in/handle/123456789/2056"),
        ("cosmetics", "https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/"),
        ("drug", "https://cdsco.gov.in/opencms/opencms/en/Acts-and-rules/"),
        ("aahara", "https://www.fssai.gov.in/"),
        ("phytopharmaceutical", "https://ipc.gov.in/"),
        ("trademark", "https://www.indiacode.nic.in/handle/123456789/1993"),
        ("trade mark", "https://www.indiacode.nic.in/handle/123456789/1993"),
        ("copyright", "https://copyright.gov.in/"),
        ("geographical indication", "https://ipindia.gov.in/geographical-indications.htm"),
        ("design", "https://ipindia.gov.in/designs.htm"),
    ]

    for kw, kw_url in keyword_map:
        if kw in s_lower or kw in section_str.lower():
            return kw_url

    return None


def enrich_citations(raw_citations: List[Any], chunks: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Enriches citation dictionaries with direct PDF URLs and official registry URLs."""
    enriched = []
    for cit in raw_citations:
        if isinstance(cit, dict):
            source = cit.get("source") or cit.get("title") or "Statutory Authority"
            section = cit.get("section", "")
            pdf_name, pdf_url = resolve_citation_pdf(source, section, chunks)
            official_url = cit.get("official_url") or resolve_citation_url(source, section, chunks)
            new_cit = dict(cit)
            new_cit["source"] = source
            new_cit["section"] = section
            new_cit["pdf_filename"] = pdf_name
            new_cit["pdf_url"] = pdf_url
            new_cit["official_url"] = official_url
            # Primary url opens the PDF directly
            new_cit["url"] = pdf_url
            enriched.append(new_cit)
        elif isinstance(cit, str):
            pdf_name, pdf_url = resolve_citation_pdf(cit, cit, chunks)
            official_url = resolve_citation_url(cit, cit, chunks)
            enriched.append({
                "source": cit,
                "section": cit,
                "pdf_filename": pdf_name,
                "pdf_url": pdf_url,
                "official_url": official_url,
                "url": pdf_url,
            })
    return enriched


def translate_previous_response(text: str, target_lang: str) -> str:
    """Translates previous assistant response to target language while preserving statutory citations and legal structure."""
    if target_lang == "en":
        system_prompt = (
            "You are a professional legal translator specializing in Indian and international intellectual property law. "
            "Translate the following legal response into clear, precise, authoritative English. "
            "CRITICAL INSTRUCTIONS:\n"
            "1. Preserve all statutory citations, Act names (e.g. 'Patents Act, 1970', 'Drugs and Cosmetics Rules, 1945', 'Rule 161', 'Section 3(p)'), and section numbers in standard English.\n"
            "2. Translate all explanatory text and legal reasoning accurately.\n"
            "3. End the answer with: 'This is informational guidance, not legal advice.'\n"
            "4. Output ONLY the translated text without commentary, conversational preamble, or markdown code blocks."
        )
    else:
        system_prompt = (
            f"You are a legal translator specializing in Indian Ayurveda and IP law. "
            f"Translate the following legal answer into natural, fluent '{target_lang}'. "
            f"CRITICAL INSTRUCTIONS:\n"
            f"1. Keep all statutory citations, Act/Treaty names, and section/rule numbers in English/untranslated.\n"
            f"2. Translate the legal explanation accurately into natural, fluent '{target_lang}'.\n"
            f"3. Translate the disclaimer: 'This is informational guidance, not legal advice.'\n"
            f"4. Output ONLY the translated text, no conversational filler or markdown fences."
        )

    res = get_completion(system_prompt=system_prompt, user_prompt=text, max_tokens=1024)
    return res.get("text", text).strip()


def detect_language(text: str) -> str:
    """Detects query language using langdetect. Defaults to 'en' on failure."""
    try:
        from langdetect import detect
        lang = detect(text)
        return lang if lang else "en"
    except Exception as e:
        logger.warning(f"Language detection failed ({e}), defaulting to 'en'")
        return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    """Translates query to English for legal retrieval using Bhashini with LLM fallback."""
    if source_lang == "en":
        return text

    # 1. Attempt Bhashini translation first
    bhashini_result = bhashini_translate(text, source_lang=source_lang, target_lang="en")
    if bhashini_result:
        logger.info(f"[Translate to English] Translated using Bhashini API: '{source_lang}' -> 'en'")
        return bhashini_result

    # 2. Fallback to legal LLM translation
    logger.info(f"Translating query from '{source_lang}' to 'en' via LLM fallback")
    system_prompt = (
        f"You are a professional legal and technical translator for Indian and international law. "
        f"Translate the following user inquiry from language code '{source_lang}' into clear, precise legal English. "
        f"Output ONLY the translated English text with no quotes, commentary, or markdown formatting."
    )
    try:
        res = get_completion(
            system_prompt=system_prompt,
            user_prompt=text,
            max_tokens=256,
        )
        translated = res.get("text", "").strip()
        return translated if translated else text
    except Exception as e:
        logger.error(f"Translation to English failed: {e}")
        return text


def translate_from_english(text: str, target_lang: str) -> str:
    """Translates synthesized answer back to user's native language using Bhashini with LLM fallback."""
    if target_lang == "en":
        return text

    # 1. Attempt Bhashini translation first
    bhashini_result = bhashini_translate(text, source_lang="en", target_lang=target_lang)
    if bhashini_result:
        logger.info(f"[Translate from English] Translated using Bhashini API: 'en' -> '{target_lang}'")
        return bhashini_result

    # 2. Fallback to legal LLM translation (preserving citations)
    logger.info(f"Translating final grounded answer from 'en' to '{target_lang}' via LLM fallback")
    system_prompt = (
        f"You are a legal translator specializing in Indian Ayurveda and IP law. "
        f"Translate the following legal answer into the language corresponding to language code '{target_lang}'. "
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. Keep all statutory citations, Act/Treaty names (e.g., 'Patents Act, 1970', 'Drugs and Cosmetics Act, 1940', 'Rule 158-B', 'Section 3(p)', 'Section 3(a)') and section/rule numbers in English/untranslated.\n"
        f"2. Translate the legal explanation accurately into natural, fluent '{target_lang}'.\n"
        f"3. Translate the disclaimer: 'This is informational guidance, not legal advice.'\n"
        f"4. Output ONLY the translated text, no conversational filler or markdown fences."
    )
    try:
        res = get_completion(
            system_prompt=system_prompt,
            user_prompt=text,
            max_tokens=1024,
        )
        translated = res.get("text", "").strip()
        return translated if translated else text
    except Exception as e:
        logger.error(f"Translation from English failed: {e}")
        return text


def is_formulation_specific_query(query: str) -> bool:
    """Determines whether a user query is asking about a specific formulation/product/invention

    that requires the D&C Act / Patents Act regulatory classification decision tree.
    Direct statutory queries (e.g., 'What does Section 3(p) say?', 'Explain Rule 158-B')
    do NOT require classification.
    """
    q = query.lower()

    # If the query explicitly references a statutory section, rule, article or general act provision, answer directly
    statutory_patterns = [
        r"section\s+\d+",
        r"rule\s+\d+",
        r"article\s+\d+",
        r"what does\s+section",
        r"what is\s+section",
        r"what does\s+rule",
        r"what is\s+rule",
        r"provisions of",
        r"what does\s+the\s+patents act",
        r"what does\s+the\s+drugs and cosmetics",
        r"what is\s+the\s+nagoya protocol",
        r"what is\s+the\s+trips",
        r"explain\s+section",
        r"explain\s+rule",
        r"explain\s+article",
    ]
    for pattern in statutory_patterns:
        if re.search(pattern, q):
            return False

    # Positive formulation/product intent indicators
    formulation_indicators = [
        "my formulation",
        "our formulation",
        "this formulation",
        "my product",
        "our product",
        "my oil",
        "our oil",
        "my medicine",
        "our medicine",
        "my extract",
        "our extract",
        "my syrup",
        "grandmother",
        "grandfather",
        "family recipe",
        "my recipe",
        "our recipe",
        "traditional recipe",
        "new recipe",
        "want to sell",
        "want to manufacture",
        "want to commercialize",
        "want to patent my",
        "protect my",
        "can i patent my",
        "can i sell my",
        "which category does my",
        "how to classify my",
        "licensing required for my",
        "novel formulation",
        "new formulation",
        "developed a formulation",
        "made a formulation",
        "herbal product of mine",
        "classified as a drug",
        "classified as cosmetic",
        "classified as nutraceutical",
    ]

    for ind in formulation_indicators:
        if ind in q:
            return True

    return False


def _clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """Robustly extracts and parses JSON from LLM output."""
    cleaned = raw_text.strip()
    # Strip markdown fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                parsed = json.loads(cleaned[start_idx : end_idx + 1])
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

    return {
        "answer": raw_text,
        "citations": [],
        "confidence": "medium",
        "abstained": False,
    }


@router.get("/corpus", tags=["Provenance"])
async def get_corpus_provenance() -> Dict[str, Any]:
    """Dynamically loads and returns the legal corpus manifest grouped by jurisdiction."""
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=500, detail="Corpus manifest file not found.")

    national_docs = []
    intl_docs = []

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = row.get("filename", "").strip()
            pdf_link = f"http://localhost:8000/pdf/{quote(fn)}" if fn else ""
            doc_item = {
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "authority": row.get("authority", ""),
                "category": row.get("category", ""),
                "jurisdiction": row.get("jurisdiction", ""),
                "document_type": row.get("document_type", ""),
                "year": row.get("year", ""),
                "citation_prefix": row.get("citation_prefix", ""),
                "official_url": row.get("official_url", ""),
                "pdf_filename": fn,
                "pdf_url": pdf_link,
                "url": pdf_link,
            }
            if row.get("jurisdiction", "").lower() == "national":
                national_docs.append(doc_item)
            else:
                intl_docs.append(doc_item)

    return {
        "total_documents": len(national_docs) + len(intl_docs),
        "national_count": len(national_docs),
        "international_count": len(intl_docs),
        "national": national_docs,
        "international": intl_docs,
    }


@router.api_route("/pdf/{file_path:path}", methods=["GET", "HEAD"], tags=["Corpus"])
async def serve_corpus_pdf(file_path: str):
    """Serves the primary statutory and treaty PDF documents from data/corpus/."""
    pdf_path = find_pdf_file(file_path)
    if not pdf_path or not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"PDF document '{file_path}' not found in legal corpus."
        )
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={
            "Content-Disposition": f"inline; filename=\"{pdf_path.name}\"",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/conversations", tags=["Sessions"])
async def list_conversations_endpoint(limit: int = 50) -> Dict[str, Any]:
    """Lists saved conversation sessions with message counts and timestamps."""
    store = get_default_session_store()
    convs = store.list_conversations(limit=limit)
    return {"conversations": convs, "count": len(convs)}


@router.post("/conversations", tags=["Sessions"])
async def create_conversation_endpoint(req: CreateConversationRequest) -> Dict[str, Any]:
    """Creates a new conversation session."""
    store = get_default_session_store()
    created = store.create_conversation(title=req.title, jurisdiction=req.jurisdiction)
    return created


@router.get("/conversations/{conversation_id}", tags=["Sessions"])
async def get_conversation_endpoint(conversation_id: str) -> Dict[str, Any]:
    """Retrieves a conversation thread and all its stored messages with dynamically enriched citations."""
    store = get_default_session_store()
    conv = store.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found.")
    for msg in conv.get("messages", []):
        if msg.get("citations"):
            msg["citations"] = enrich_citations(msg["citations"])
    return conv


@router.delete("/conversations/{conversation_id}", tags=["Sessions"])
async def delete_conversation_endpoint(conversation_id: str) -> Dict[str, Any]:
    """Deletes a conversation session and all its messages."""
    store = get_default_session_store()
    success = store.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found.")
    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/admin/audit", tags=["Audit"])
@router.get("/audit/logs", tags=["Audit"])
async def get_admin_audit_logs_endpoint(limit: int = 50) -> Dict[str, Any]:
    """Retrieves the last 50 statutory query audit logs in JSON format, demonstrating DPDP data minimization."""
    store = get_default_session_store()
    logs = store.get_audit_logs(limit=limit)
    return {
        "status": "success",
        "count": len(logs),
        "limit": limit,
        "dpdp_alignment": {
            "regime": "Digital Personal Data Protection (DPDP) Act, 2023",
            "principles": [
                "Data Minimization: Scoped strictly to query text, classification, latency, provider, and abstention status.",
                "Zero PII: Absolutely no IP addresses, device identifiers, or biometric/fingerprinting captured.",
                "Purpose Limitation: Used exclusively for regulatory auditability, model provenance, and SLA monitoring."
            ],
            "pii_collected": False,
            "storage_locations": [
                "/data/audit_log.csv",
                "/data/audit_log",
                "SQLite: data/ip_sakti.db (audit_logs table)"
            ],
            "hackathon_scope_notice": (
                "Foundational audit log implementation. Production DPDP readiness requires "
                "enterprise encryption-at-rest, automated retention/expunction schedules, "
                "and cryptographically enforced RBAC access control."
            ),
        },
        "audit_logs": logs,
    }


@router.get("/admin/audit/view", tags=["Audit"], response_class=HTMLResponse)
async def get_admin_audit_html_view(limit: int = 50) -> HTMLResponse:
    """Renders a read-only administrative inspection dashboard for the statutory audit trail."""
    store = get_default_session_store()
    logs = store.get_audit_logs(limit=limit)

    total_count = len(logs)
    avg_latency = round(sum(l.get("latency_ms", 0.0) for l in logs) / total_count, 1) if total_count > 0 else 0.0
    abstained_count = sum(1 for l in logs if l.get("abstained"))
    providers = sorted(list(set(l.get("provider_used") or "none" for l in logs)))
    providers_str = ", ".join(providers) if providers else "N/A"

    rows_html = []
    for idx, item in enumerate(logs, start=1):
        ts = item.get("timestamp", "")
        ts_short = ts.replace("T", " ").split(".")[0] if ts else "-"
        jurisdiction = (item.get("jurisdiction") or "national").lower()
        jurisdiction_badge = (
            '<span class="badge badge-national">India (National)</span>'
            if jurisdiction == "national"
            else '<span class="badge badge-international">Global (Treaties)</span>'
        )
        query_text = (item.get("query") or "").strip()
        classification = item.get("classification") or item.get("formulation_type") or "general_statutory"
        provider = item.get("provider_used") or "none"
        lat = float(item.get("latency_ms", 0.0))
        lat_class = "latency-fast" if lat < 2000 else ("latency-mid" if lat < 5000 else "latency-slow")
        abstained = bool(item.get("abstained", False))
        status_badge = (
            '<span class="badge badge-abstained">Abstained</span>'
            if abstained
            else '<span class="badge badge-answered">Answered</span>'
        )
        conv_id = item.get("conversation_id") or "-"
        conv_short = conv_id[:8] + "..." if len(conv_id) > 8 else conv_id

        rows_html.append(f"""
        <tr>
            <td class="col-id">{idx}</td>
            <td class="col-ts" title="{ts}">{ts_short}</td>
            <td>{jurisdiction_badge}</td>
            <td class="col-query" title="{query_text}">{query_text}</td>
            <td><span class="badge badge-class">{classification}</span></td>
            <td><span class="badge badge-provider">{provider}</span></td>
            <td><span class="{lat_class}">{lat:,.1f} ms</span></td>
            <td>{status_badge}</td>
            <td class="col-conv" title="{conv_id}">{conv_short}</td>
        </tr>
        """)

    table_body = "\\n".join(rows_html) if rows_html else '<tr><td colspan="9" style="text-align:center; padding:30px; color:#888;">No audit entries logged yet.</td></tr>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP-SAKTI Sahayak — Statutory Query Audit Trail</title>
    <style>
        :root {{
            --bg-primary: #07090e;
            --bg-card: #0f141f;
            --border-color: rgba(217, 119, 6, 0.25);
            --text-primary: #f8fafc;
            --text-muted: #94a3b8;
            --amber-primary: #f59e0b;
            --emerald: #10b981;
            --rose: #f43f5e;
            --blue: #38bdf8;
            --purple: #c084fc;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding: 24px 32px;
            min-height: 100vh;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 24px;
        }}
        .header-title {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .header-icon {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, rgba(245,158,11,0.25), rgba(0,0,0,0.6));
            border: 1px solid var(--amber-primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }}
        h1 {{
            font-size: 22px;
            font-weight: 700;
            color: #fef3c7;
            letter-spacing: 0.5px;
        }}
        .subtitle {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .dpdp-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #6ee7b7;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        .nav-links {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-outline {{
            background: rgba(255,255,255,0.04);
            color: #f1f5f9;
            border: 1px solid rgba(255,255,255,0.15);
        }}
        .btn-outline:hover {{
            background: rgba(255,255,255,0.1);
            border-color: rgba(255,255,255,0.3);
        }}
        .btn-amber {{
            background: rgba(245,158,11,0.15);
            color: #fde68a;
            border: 1px solid rgba(245,158,11,0.4);
        }}
        .btn-amber:hover {{
            background: rgba(245,158,11,0.25);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 16px;
        }}
        .stat-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #fff;
        }}
        .stat-desc {{
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }}
        .table-container {{
            background: var(--bg-card);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            overflow-x: auto;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 13px;
        }}
        th {{
            background: rgba(0,0,0,0.4);
            color: #cbd5e1;
            padding: 12px 14px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            white-space: nowrap;
        }}
        td {{
            padding: 12px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            color: #e2e8f0;
            vertical-align: middle;
        }}
        tr:hover td {{
            background: rgba(245,158,11,0.03);
        }}
        .col-id {{ color: #64748b; width: 40px; font-weight: 600; }}
        .col-ts {{ color: #94a3b8; font-size: 12px; white-space: nowrap; }}
        .col-query {{ max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; color: #f8fafc; }}
        .col-conv {{ color: #64748b; font-family: monospace; font-size: 11px; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }}
        .badge-national {{ background: rgba(56,189,248,0.12); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.3); }}
        .badge-international {{ background: rgba(192,132,252,0.12); color: #e9d5ff; border: 1px solid rgba(192,132,252,0.3); }}
        .badge-class {{ background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); }}
        .badge-provider {{ background: rgba(245,158,11,0.1); color: #fcd34d; border: 1px solid rgba(245,158,11,0.25); }}
        .badge-answered {{ background: rgba(16,185,129,0.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }}
        .badge-abstained {{ background: rgba(244,63,94,0.12); color: #fda4af; border: 1px solid rgba(244,63,94,0.3); }}
        .latency-fast {{ color: #34d399; font-weight: 600; font-size: 12px; }}
        .latency-mid {{ color: #fbbf24; font-weight: 600; font-size: 12px; }}
        .latency-slow {{ color: #f87171; font-weight: 600; font-size: 12px; }}
        .dpdp-box {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 12px;
            padding: 18px 22px;
            font-size: 12.5px;
            line-height: 1.6;
            color: #94a3b8;
        }}
        .dpdp-box h3 {{
            color: #6ee7b7;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .dpdp-box strong {{ color: #f1f5f9; }}
        .dpdp-box code {{ background: rgba(0,0,0,0.4); padding: 2px 6px; border-radius: 4px; color: #fde68a; font-size: 12px; }}
    </style>
</head>
<body>
    <header>
        <div>
            <div class="header-title">
                <div class="header-icon">⚖️</div>
                <div>
                    <h1>IP-SAKTI Sahayak — Statutory Query Audit Trail</h1>
                    <div class="subtitle">Real-time regulatory compliance & query metadata logging dashboard</div>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <span class="dpdp-pill">🛡️ DPDP Act 2023 Aligned • Zero PII / Zero Fingerprinting</span>
            </div>
        </div>
        <div class="nav-links">
            <button onclick="window.location.reload()" class="btn btn-outline">🔄 Refresh</button>
            <a href="/admin/audit" class="btn btn-outline" target="_blank">📄 JSON API</a>
            <a href="http://localhost:3000" class="btn btn-amber">← Return to Assistant</a>
        </div>
    </header>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Queries Logged (Window)</div>
            <div class="stat-value">{total_count}</div>
            <div class="stat-desc">Displaying last {limit} inquiries</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg Response Latency</div>
            <div class="stat-value">{avg_latency} <span style="font-size:14px; font-weight:400; color:#94a3b8;">ms</span></div>
            <div class="stat-desc">End-to-end pipeline turnaround</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Abstention Rate</div>
            <div class="stat-value">{abstained_count} <span style="font-size:14px; font-weight:400; color:#94a3b8;">/ {total_count}</span></div>
            <div class="stat-desc">Grounding guardrail escalations</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Inference Providers</div>
            <div class="stat-value" style="font-size:16px; margin-top:6px; color:#fde68a;">{providers_str}</div>
            <div class="stat-desc">Groq Primary / Mistral Fallback</div>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Timestamp (UTC)</th>
                    <th>Jurisdiction</th>
                    <th>Query Text</th>
                    <th>Classification</th>
                    <th>LLM Provider</th>
                    <th>Latency</th>
                    <th>Status</th>
                    <th>Session ID</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </div>

    <div class="dpdp-box">
        <h3>🛡️ DPDP Alignment & Scope Notice</h3>
        <p>
            <strong>Data Minimization Compliance</strong>: Under Sections 4 & 6 of India's Digital Personal Data Protection (DPDP) Act 2023,
            this audit log strictly records query and response metadata necessary for statutory auditing, latency monitoring, and model governance.
            <strong>Zero Personally Identifiable Information (PII)</strong> is captured—no IP addresses, device fingerprints, cookies, or user agent headers are retained.
            Logs are persisted append-only to <code>data/audit_log.csv</code>, <code>data/audit_log</code>, and SQLite table <code>audit_logs</code>.
        </p>
        <p style="margin-top: 8px; font-size: 11.5px; color: #64748b;">
            <em>Hackathon Scope Note: This represents a foundational audit-trail implementation. Production deployment requires institutional encryption at rest (AES-256), cryptographic role-based access control (RBAC), and automated retention/expunction schedules.</em>
        </p>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@router.post("/feedback", tags=["Feedback"])
async def submit_feedback_endpoint(req: FeedbackRequest) -> Dict[str, Any]:
    """Records user feedback ('up'/'down') with optional comment to both SQLite and append-only CSV log."""
    store = get_default_session_store()
    entry = store.log_feedback(
        rating=req.rating,
        conversation_id=req.conversation_id,
        query=req.query,
        answer_snippet=req.answer_snippet,
        citations=req.citations,
        comment=req.comment,
    )

    # Append row to CSV log in /data/feedback_log.csv
    try:
        FEEDBACK_LOG_CSV.parent.mkdir(parents=True, exist_ok=True)
        file_exists = FEEDBACK_LOG_CSV.exists()
        with open(FEEDBACK_LOG_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "timestamp",
                    "id",
                    "conversation_id",
                    "rating",
                    "comment",
                    "query",
                    "answer_snippet",
                    "citations",
                ])
            cit_items = []
            for c in (req.citations or []):
                if isinstance(c, dict):
                    src = c.get("source", "").strip()
                    sec = c.get("section", "").strip()
                    cit_items.append(f"{src} ({sec})" if src and sec else (src or sec))
                else:
                    cit_items.append(str(c))
            cit_summary = "; ".join(cit_items)
            writer.writerow([
                entry["timestamp"],
                entry["id"],
                req.conversation_id or "",
                req.rating,
                req.comment or "",
                req.query or "",
                (req.answer_snippet or "").replace("\n", " ")[:300],
                cit_summary,
            ])
    except Exception as e:
        logger.error(f"Failed to append to feedback CSV log: {e}")

    return {
        "status": "ok",
        "feedback_id": entry["id"],
        "rating": req.rating,
        "message": "Feedback recorded successfully",
    }


@router.get("/feedback", tags=["Feedback"])
async def list_feedback_endpoint(limit: int = 50) -> Dict[str, Any]:
    """Retrieves recent user feedback logs."""
    store = get_default_session_store()
    logs = store.get_feedback_logs(limit=limit)
    return {"feedback": logs, "count": len(logs)}


@router.post("/ask", tags=["Assistant"])
async def ask_endpoint(request: AskRequest) -> Dict[str, Any]:
    """Grounded RAG inquiry endpoint with query validation, FP16 reranker, stage timing, and translation."""
    t_start = time.perf_counter()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    store = get_default_session_store()

    # 0. Query validation
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty or whitespace-only.")

    # 1. Detect query language & translate to English if needed
    t_lang_s = time.perf_counter()
    detected_lang = detect_language(request.query)
    search_query = translate_to_english(request.query, source_lang=detected_lang)
    t_lang_ms = (time.perf_counter() - t_lang_s) * 1000

    # Persist user inquiry in session store
    store.add_message(conversation_id, {
        "role": "user",
        "content": request.query,
        "language": detected_lang,
        "jurisdiction": request.jurisdiction,
    })

    # 1.5 Conversational Translation Follow-up Check
    trans_followup = parse_translation_followup(request.query, request.history, search_query)
    if trans_followup is not None:
        target_code, target_name, text_to_trans, prev_citations = trans_followup
        t_trans_s = time.perf_counter()
        translated_answer = translate_previous_response(text_to_trans, target_lang=target_code)
        t_trans_ms = (time.perf_counter() - t_trans_s) * 1000
        t_total_ms = (time.perf_counter() - t_start) * 1000

        timing_data = {
            "retrieval": 0.0,
            "llm": round(t_trans_ms, 2),
            "total": round(t_total_ms, 2),
        }
        store.add_message(conversation_id, {
            "role": "assistant",
            "content": translated_answer,
            "citations": prev_citations,
            "classification": "conversational_translation",
            "classification_citation": f"Translated to {target_name}",
            "confidence": "high",
            "abstained": False,
            "language": target_code,
            "provider_used": "groq",
            "timing_ms": timing_data,
        })
        store.log_audit_event(
            conversation_id=conversation_id,
            query=request.query,
            detected_lang=detected_lang,
            jurisdiction=request.jurisdiction,
            formulation_type="conversational_translation",
            provider_used="groq",
            abstained=False,
            latency_ms=t_total_ms,
        )
        return {
            "needs_classification": False,
            "classification": "conversational_translation",
            "classification_citation": f"Translated to {target_name}",
            "answer": translated_answer,
            "citations": prev_citations,
            "confidence": "high",
            "abstained": False,
            "language": target_code,
            "provider_used": "groq",
            "conversation_id": conversation_id,
            "timing_ms": timing_data,
        }

    # 2. Gated formulation classification check
    should_classify = bool(request.formulation_answers) or is_formulation_specific_query(search_query)

    if should_classify:
        next_question = get_next_question(request.formulation_answers)
        if next_question is not None:
            t_total_ms = (time.perf_counter() - t_start) * 1000
            store.log_audit_event(
                conversation_id=conversation_id,
                query=request.query,
                detected_lang=detected_lang,
                jurisdiction=request.jurisdiction,
                formulation_type="classification_question",
                provider_used="rule_engine",
                abstained=False,
                latency_ms=t_total_ms,
            )
            store.add_message(conversation_id, {
                "role": "assistant",
                "content": f"Classification Question: {next_question.get('question')}",
                "classification": "classification_question",
                "language": detected_lang,
            })
            return {
                "needs_classification": True,
                "question": next_question,
                "language": detected_lang,
                "conversation_id": conversation_id,
            }
        formulation_type = classify_formulation(request.formulation_answers)
        classification_citation = CLASSIFICATION_CITATIONS.get(formulation_type, "")
    else:
        formulation_type = "general_statutory"
        classification_citation = "General Statutory Interpretation"

    # 2.5 Retrieve prior conversation memory context & contextualize retrieval query
    memory_context, last_turn = get_memory_context(conversation_id)
    retrieval_query = contextualize_query_with_memory(search_query, last_turn, jurisdiction=request.jurisdiction)

    # 3. Retrieve relevant statutory context chunks
    t_ret_s = time.perf_counter()
    retrieval_res = retrieve(
        query=retrieval_query,
        jurisdiction=request.jurisdiction,
    )
    chunks = retrieval_res.get("results", [])
    t_ret_ms = (time.perf_counter() - t_ret_s) * 1000

    # 4. If retrieve() returns no results, return explicit abstention without LLM call
    if not chunks:
        abstention_en = (
            "No relevant statutory provisions found in the verified legal corpus for this query. "
            "Escalation to a qualified human IP facilitator is recommended. "
            "This is informational guidance, not legal advice."
        )
        final_answer = translate_from_english(abstention_en, target_lang=detected_lang)
        store.add_message(conversation_id, {
            "role": "assistant",
            "content": final_answer,
            "citations": [],
            "classification": formulation_type,
            "classification_citation": classification_citation,
            "confidence": "low",
            "abstained": True,
            "language": detected_lang,
        })
        store.log_audit_event(
            conversation_id=conversation_id,
            query=request.query,
            detected_lang=detected_lang,
            jurisdiction=request.jurisdiction,
            formulation_type=formulation_type,
            provider_used=None,
            abstained=True,
            latency_ms=(time.perf_counter() - t_start) * 1000,
        )
        record_turn_in_memory(
            conversation_id=conversation_id,
            query=request.query,
            answer=final_answer,
            citations=[],
        )
        return {
            "needs_classification": False,
            "classification": formulation_type,
            "classification_citation": classification_citation,
            "answer": final_answer,
            "citations": [],
            "confidence": "low",
            "abstained": True,
            "language": detected_lang,
            "conversation_id": conversation_id,
        }

    # 5. Build user prompt combining history + query + retrieved context chunks
    context_lines = []
    for idx, c in enumerate(chunks, start=1):
        source_title = c.get("title", "Statutory Source")
        citation_prefix = c.get("citation_prefix", "")
        section = c.get("section", "")
        text = c.get("text", "").strip()
        context_lines.append(
            f"--- Source [{idx}] ---\n"
            f"Act/Treaty: {source_title}\n"
            f"Citation Prefix: {citation_prefix}\n"
            f"Section/Article: {section}\n"
            f"Content: {text}"
        )

    context_formatted = "\n\n".join(context_lines)
    history_context = ""
    if request.history:
        history_snippets = []
        for h in request.history[-4:]:
            h_role = "User" if h.get("role") == "user" else "Assistant"
            h_text = h.get("content", "").strip()
            if h_text:
                history_snippets.append(f"{h_role}: {h_text}")
        if history_snippets:
            history_context = "PREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(history_snippets) + "\n\n"
    elif memory_context:
        history_context = memory_context + "\n"

    user_prompt = (
        f"{history_context}"
        f"User Inquiry: {search_query}\n"
        f"Jurisdiction Scope: {request.jurisdiction.capitalize()}\n"
        f"Classified Formulation Category: {formulation_type} (Legal Basis: {classification_citation})\n\n"
        f"RETRIEVED STATUTORY CONTEXT CHUNKS:\n"
        f"{context_formatted}\n\n"
        f"Please provide your legally grounded JSON response adhering strictly to all system rules."
    )

    # 6. Call LLM completion (Groq primary with Mistral fallback)
    t_llm_s = time.perf_counter()
    completion_res = get_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1024,
    )
    t_llm_ms = (time.perf_counter() - t_llm_s) * 1000
    raw_text = completion_res.get("text", "")
    provider_used = completion_res.get("provider_used", "unknown")

    # 7. Parse LLM JSON output & translate back if non-English
    parsed = _clean_and_parse_json(raw_text)
    raw_answer = parsed.get("answer", raw_text)
    final_answer = translate_from_english(raw_answer, target_lang=detected_lang)
    t_total_ms = (time.perf_counter() - t_start) * 1000

    timing_info = {
        "retrieval": round(t_ret_ms, 2),
        "llm": round(t_llm_ms, 2),
        "total": round(t_total_ms, 2),
    }

    logger.info(
        f"[Latency Profile] Query: '{request.query[:40]}...' | "
        f"Lang: {t_lang_ms:.1f}ms | Retrieval: {t_ret_ms:.1f}ms | "
        f"LLM ({provider_used}): {t_llm_ms:.1f}ms | Total: {t_total_ms:.1f}ms"
    )

    enriched_citations = enrich_citations(parsed.get("citations", []), chunks)

    record_turn_in_memory(
        conversation_id=conversation_id,
        query=request.query,
        answer=final_answer,
        citations=enriched_citations,
    )

    store.add_message(conversation_id, {
        "role": "assistant",
        "content": final_answer,
        "citations": enriched_citations,
        "classification": formulation_type,
        "classification_citation": classification_citation,
        "confidence": parsed.get("confidence", "medium"),
        "abstained": parsed.get("abstained", False),
        "language": detected_lang,
        "provider_used": provider_used,
        "timing_ms": timing_info,
    })
    store.log_audit_event(
        conversation_id=conversation_id,
        query=request.query,
        detected_lang=detected_lang,
        jurisdiction=request.jurisdiction,
        formulation_type=formulation_type,
        provider_used=provider_used,
        abstained=parsed.get("abstained", False),
        latency_ms=t_total_ms,
    )

    return {
        "needs_classification": False,
        "classification": formulation_type,
        "classification_citation": classification_citation,
        "answer": final_answer,
        "citations": enriched_citations,
        "confidence": parsed.get("confidence", "medium"),
        "abstained": parsed.get("abstained", False),
        "language": detected_lang,
        "provider_used": provider_used,
        "conversation_id": conversation_id,
        "timing_ms": timing_info,
    }


@router.post("/ask/stream", tags=["Assistant"])
async def ask_stream_endpoint(request: AskRequest):
    """Server-Sent Events (SSE) stream endpoint transmitting real-time pipeline execution milestones and live token streaming."""
    
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty or whitespace-only.")

    async def event_generator() -> AsyncGenerator[str, None]:
        t_stream_start = time.perf_counter()
        conversation_id = request.conversation_id or str(uuid.uuid4())
        store = get_default_session_store()

        try:
            # Stage 1: Language Detection
            yield f"data: {json.dumps({'stage': 'detect_language', 'message': 'Detecting inquiry language...', 'conversation_id': conversation_id})}\n\n"
            detected_lang = detect_language(request.query)

            # Persist user inquiry in session store
            store.add_message(conversation_id, {
                "role": "user",
                "content": request.query,
                "language": detected_lang,
                "jurisdiction": request.jurisdiction,
            })

            # Stage 2: Query Translation (if non-English)
            if detected_lang != "en":
                yield f"data: {json.dumps({'stage': 'translating_query', 'message': f'Translating inquiry from {detected_lang} to English...'})}\n\n"
            search_query = translate_to_english(request.query, source_lang=detected_lang)

            # Stage 2.5: Check for Conversational Translation Follow-up
            trans_followup = parse_translation_followup(request.query, request.history, search_query)
            if trans_followup is not None:
                target_code, target_name, text_to_trans, prev_citations = trans_followup
                yield f"data: {json.dumps({'stage': 'translating_answer', 'message': f'Translating previous legal response to {target_name}...'})}\n\n"
                t_trans_s = time.perf_counter()

                if target_code == "en":
                    trans_sys_prompt = (
                        "You are a professional legal translator specializing in Indian and international intellectual property law. "
                        "Translate the following legal response into clear, precise, authoritative English. "
                        "CRITICAL INSTRUCTIONS:\n"
                        "1. Preserve all statutory citations, Act names (e.g. 'Patents Act, 1970', 'Drugs and Cosmetics Rules, 1945', 'Rule 161', 'Section 3(p)'), and section numbers in standard English.\n"
                        "2. Translate all explanatory text and legal reasoning accurately.\n"
                        "3. End the answer with: 'This is informational guidance, not legal advice.'\n"
                        "4. Output ONLY the translated text without commentary, conversational preamble, or markdown code blocks."
                    )
                else:
                    trans_sys_prompt = (
                        f"You are a legal translator specializing in Indian Ayurveda and IP law. "
                        f"Translate the following legal answer into natural, fluent '{target_code}'. "
                        f"CRITICAL INSTRUCTIONS:\n"
                        f"1. Keep all statutory citations, Act/Treaty names, and section/rule numbers in English/untranslated.\n"
                        f"2. Translate the legal explanation accurately into natural, fluent '{target_code}'.\n"
                        f"3. Translate the disclaimer: 'This is informational guidance, not legal advice.'\n"
                        f"4. Output ONLY the translated text, no conversational filler or markdown fences."
                    )

                collected_trans = []
                provider_used = "groq"
                for chunk_item in stream_completion(
                    system_prompt=trans_sys_prompt,
                    user_prompt=text_to_trans,
                    max_tokens=1024,
                ):
                    delta = chunk_item.get("delta", "")
                    provider_used = chunk_item.get("provider", "groq")
                    collected_trans.append(delta)
                    yield f"data: {json.dumps({'stage': 'llm_token', 'delta': delta, 'answer_delta': delta})}\n\n"

                translated_answer = "".join(collected_trans).strip()
                t_trans_ms = (time.perf_counter() - t_trans_s) * 1000
                t_total_ms = (time.perf_counter() - t_stream_start) * 1000

                timing_data = {
                    "retrieval": 0.0,
                    "llm": round(t_trans_ms, 2),
                    "total": round(t_total_ms, 2),
                }

                store.add_message(conversation_id, {
                    "role": "assistant",
                    "content": translated_answer,
                    "citations": prev_citations,
                    "classification": "conversational_translation",
                    "classification_citation": f"Translated to {target_name}",
                    "confidence": "high",
                    "abstained": False,
                    "language": target_code,
                    "provider_used": provider_used,
                    "timing_ms": timing_data,
                })
                store.log_audit_event(
                    conversation_id=conversation_id,
                    query=request.query,
                    detected_lang=detected_lang,
                    jurisdiction=request.jurisdiction,
                    formulation_type="conversational_translation",
                    provider_used=provider_used,
                    abstained=False,
                    latency_ms=t_total_ms,
                )

                final_payload = {
                    "needs_classification": False,
                    "classification": "conversational_translation",
                    "classification_citation": f"Translated to {target_name}",
                    "answer": translated_answer,
                    "citations": prev_citations,
                    "confidence": "high",
                    "abstained": False,
                    "language": target_code,
                    "provider_used": provider_used,
                    "conversation_id": conversation_id,
                    "timing_ms": timing_data,
                }
                yield f"data: {json.dumps({'stage': 'complete', 'data': final_payload})}\n\n"
                return

            # Stage 3: Gated Formulation Classification
            should_classify = bool(request.formulation_answers) or is_formulation_specific_query(search_query)

            if should_classify:
                yield f"data: {json.dumps({'stage': 'classification_check', 'message': 'Verifying formulation classification tree...'})}\n\n"
                next_question = get_next_question(request.formulation_answers)
                if next_question is not None:
                    t_total_ms = (time.perf_counter() - t_stream_start) * 1000
                    store.log_audit_event(
                        conversation_id=conversation_id,
                        query=request.query,
                        detected_lang=detected_lang,
                        jurisdiction=request.jurisdiction,
                        formulation_type="classification_question",
                        provider_used="rule_engine",
                        abstained=False,
                        latency_ms=t_total_ms,
                    )
                    store.add_message(conversation_id, {
                        "role": "assistant",
                        "content": f"Classification Question: {next_question.get('question')}",
                        "classification": "classification_question",
                        "language": detected_lang,
                    })
                    final_payload = {
                        "needs_classification": True,
                        "question": next_question,
                        "language": detected_lang,
                        "conversation_id": conversation_id,
                    }
                    yield f"data: {json.dumps({'stage': 'complete', 'data': final_payload})}\n\n"
                    return

                formulation_type = classify_formulation(request.formulation_answers)
                classification_citation = CLASSIFICATION_CITATIONS.get(formulation_type, "")
            else:
                formulation_type = "general_statutory"
                classification_citation = "General Statutory Interpretation"

            # Stage 4: Fast FP16 Legal Retrieval
            t_ret_s = time.perf_counter()
            memory_context, last_turn = get_memory_context(conversation_id)
            retrieval_query = contextualize_query_with_memory(search_query, last_turn, jurisdiction=request.jurisdiction)
            yield f"data: {json.dumps({'stage': 'retrieval', 'message': f'Searching {request.jurisdiction} statutory corpus & treaties (FP16 Accelerated)...'})}\n\n"
            retrieval_res = retrieve(
                query=retrieval_query,
                jurisdiction=request.jurisdiction,
            )
            chunks = retrieval_res.get("results", [])
            t_ret_ms = (time.perf_counter() - t_ret_s) * 1000

            if not chunks:
                abstention_en = (
                    "No relevant statutory provisions found in the verified legal corpus for this query. "
                    "Escalation to a qualified human IP facilitator is recommended. "
                    "This is informational guidance, not legal advice."
                )
                final_answer = translate_from_english(abstention_en, target_lang=detected_lang)
                store.add_message(conversation_id, {
                    "role": "assistant",
                    "content": final_answer,
                    "citations": [],
                    "classification": formulation_type,
                    "classification_citation": classification_citation,
                    "confidence": "low",
                    "abstained": True,
                    "language": detected_lang,
                })
                store.log_audit_event(
                    conversation_id=conversation_id,
                    query=request.query,
                    detected_lang=detected_lang,
                    jurisdiction=request.jurisdiction,
                    formulation_type=formulation_type,
                    provider_used=None,
                    abstained=True,
                    latency_ms=(time.perf_counter() - t_stream_start) * 1000,
                )
                record_turn_in_memory(
                    conversation_id=conversation_id,
                    query=request.query,
                    answer=final_answer,
                    citations=[],
                )
                final_payload = {
                    "needs_classification": False,
                    "classification": formulation_type,
                    "classification_citation": classification_citation,
                    "answer": final_answer,
                    "citations": [],
                    "confidence": "low",
                    "abstained": True,
                    "language": detected_lang,
                    "conversation_id": conversation_id,
                }
                yield f"data: {json.dumps({'stage': 'complete', 'data': final_payload})}\n\n"
                return

            # Stage 5: Context Formatting
            yield f"data: {json.dumps({'stage': 'reranking', 'message': 'Cross-Encoder semantic reranking complete...'})}\n\n"
            context_lines = []
            for idx, c in enumerate(chunks, start=1):
                source_title = c.get("title", "Statutory Source")
                citation_prefix = c.get("citation_prefix", "")
                section = c.get("section", "")
                text = c.get("text", "").strip()
                context_lines.append(
                    f"--- Source [{idx}] ---\n"
                    f"Act/Treaty: {source_title}\n"
                    f"Citation Prefix: {citation_prefix}\n"
                    f"Section/Article: {section}\n"
                    f"Content: {text}"
                )

            context_formatted = "\n\n".join(context_lines)
            history_context = ""
            if request.history:
                history_snippets = []
                for h in request.history[-4:]:
                    h_role = "User" if h.get("role") == "user" else "Assistant"
                    h_text = h.get("content", "").strip()
                    if h_text:
                        history_snippets.append(f"{h_role}: {h_text}")
                if history_snippets:
                    history_context = "PREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(history_snippets) + "\n\n"
            elif memory_context:
                history_context = memory_context + "\n"

            user_prompt = (
                f"{history_context}"
                f"User Inquiry: {search_query}\n"
                f"Jurisdiction Scope: {request.jurisdiction.capitalize()}\n"
                f"Classified Formulation Category: {formulation_type} (Legal Basis: {classification_citation})\n\n"
                f"RETRIEVED STATUTORY CONTEXT CHUNKS:\n"
                f"{context_formatted}\n\n"
                f"Please provide your legally grounded JSON response adhering strictly to all system rules."
            )

            # Stage 6: Grounded Synthesis with Live Incremental LLM Streaming
            t_llm_s = time.perf_counter()
            yield f"data: {json.dumps({'stage': 'synthesis', 'message': 'Synthesizing verified statutory answer with citations...'})}\n\n"
            collected_chunks = []
            provider_used = "groq"
            extractor = IncrementalAnswerExtractor()

            for chunk_item in stream_completion(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=1024,
            ):
                delta = chunk_item.get("delta", "")
                provider_used = chunk_item.get("provider", "groq")
                collected_chunks.append(delta)
                answer_delta = extractor.feed(delta)
                yield f"data: {json.dumps({'stage': 'llm_token', 'delta': delta, 'answer_delta': answer_delta})}\n\n"

            raw_text = "".join(collected_chunks)
            t_llm_ms = (time.perf_counter() - t_llm_s) * 1000

            parsed = _clean_and_parse_json(raw_text)
            raw_answer = parsed.get("answer", raw_text)

            # Stage 7: Native Language Translation (if non-English)
            if detected_lang != "en":
                yield f"data: {json.dumps({'stage': 'translating_answer', 'message': f'Translating explanation back to native language ({detected_lang})...'})}\n\n"
                # Check Bhashini first
                bhashini_result = bhashini_translate(raw_answer, source_lang="en", target_lang=detected_lang)
                if bhashini_result:
                    final_answer = bhashini_result
                    yield f"data: {json.dumps({'stage': 'llm_token', 'delta': final_answer, 'answer_delta': final_answer, 'is_translated': True})}\n\n"
                else:
                    # Stream LLM translation tokens
                    collected_trans = []
                    trans_sys_prompt = (
                        f"You are a legal translator specializing in Indian Ayurveda and IP law. "
                        f"Translate the following legal answer into the language corresponding to language code '{detected_lang}'. "
                        f"CRITICAL INSTRUCTIONS:\n"
                        f"1. Keep all statutory citations, Act/Treaty names (e.g., 'Patents Act, 1970', 'Drugs and Cosmetics Act, 1940', 'Rule 158-B', 'Section 3(p)', 'Section 3(a)') and section/rule numbers in English/untranslated.\n"
                        f"2. Translate the legal explanation accurately into natural, fluent '{detected_lang}'.\n"
                        f"3. Translate the disclaimer: 'This is informational guidance, not legal advice.'\n"
                        f"4. Output ONLY the translated text, no conversational filler or markdown fences."
                    )
                    for chunk_item in stream_completion(
                        system_prompt=trans_sys_prompt,
                        user_prompt=raw_answer,
                        max_tokens=1024,
                    ):
                        delta = chunk_item.get("delta", "")
                        collected_trans.append(delta)
                        yield f"data: {json.dumps({'stage': 'llm_token', 'delta': delta, 'answer_delta': delta, 'is_translated': True})}\n\n"
                    final_answer = "".join(collected_trans).strip() or raw_answer
            else:
                final_answer = raw_answer

            t_total_ms = (time.perf_counter() - t_stream_start) * 1000

            timing_data = {
                "retrieval": round(t_ret_ms, 2),
                "llm": round(t_llm_ms, 2),
                "total": round(t_total_ms, 2),
            }

            logger.info(
                f"[Stream Latency Profile] Query: '{request.query[:40]}...' | "
                f"Retrieval: {t_ret_ms:.1f}ms | LLM ({provider_used}): {t_llm_ms:.1f}ms | Total: {t_total_ms:.1f}ms"
            )

            enriched_citations = enrich_citations(parsed.get("citations", []), chunks)

            record_turn_in_memory(
                conversation_id=conversation_id,
                query=request.query,
                answer=final_answer,
                citations=enriched_citations,
            )

            store.add_message(conversation_id, {
                "role": "assistant",
                "content": final_answer,
                "citations": enriched_citations,
                "classification": formulation_type,
                "classification_citation": classification_citation,
                "confidence": parsed.get("confidence", "medium"),
                "abstained": parsed.get("abstained", False),
                "language": detected_lang,
                "provider_used": provider_used,
                "timing_ms": timing_data,
            })
            store.log_audit_event(
                conversation_id=conversation_id,
                query=request.query,
                detected_lang=detected_lang,
                jurisdiction=request.jurisdiction,
                formulation_type=formulation_type,
                provider_used=provider_used,
                abstained=parsed.get("abstained", False),
                latency_ms=t_total_ms,
            )

            final_payload = {
                "needs_classification": False,
                "classification": formulation_type,
                "classification_citation": classification_citation,
                "answer": final_answer,
                "citations": enriched_citations,
                "confidence": parsed.get("confidence", "medium"),
                "abstained": parsed.get("abstained", False),
                "language": detected_lang,
                "provider_used": provider_used,
                "conversation_id": conversation_id,
                "timing_ms": timing_data,
            }
            yield f"data: {json.dumps({'stage': 'complete', 'data': final_payload})}\n\n"

        except Exception as e:
            logger.error(f"Stream generation error: {e}", exc_info=True)
            yield f"data: {json.dumps({'stage': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
