"""Grounded Answer Generation for IP-SAKTI Sahayak."""

import os
import logging
from typing import List, Dict, Any, Optional
from app.llm.prompts import SYSTEM_PROMPT_GROUNDED_RAG, DISCLAIMER_TEXT

logger = logging.getLogger(__name__)


def generate_grounded_answer(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    confidence_threshold: float = 0.30,
) -> Dict[str, Any]:
    """Generates a legally grounded answer from retrieved context with citations and abstention check."""
    if not retrieved_chunks:
        return {
            "answer": "No relevant statutory provisions found in the verified legal corpus for this query.",
            "citations": [],
            "abstained": True,
            "confidence": 0.0,
            "disclaimer": DISCLAIMER_TEXT,
        }

    # Check top candidate score
    top_score = retrieved_chunks[0].get("score", 0.0)
    if top_score < confidence_threshold:
        return {
            "answer": "Authoritative statutory or regulatory sources could not be confirmed with sufficient confidence in the verified corpus for this specific inquiry.",
            "citations": [f"[{c.get('title')}] {c.get('section')}" for c in retrieved_chunks[:2]],
            "abstained": True,
            "confidence": round(float(top_score), 4),
            "disclaimer": DISCLAIMER_TEXT,
        }

    # Format context for grounding
    context_lines = []
    citations = []
    for idx, c in enumerate(retrieved_chunks, start=1):
        title = c.get("title", "Statutory Source")
        section = c.get("section", "Section")
        text = c.get("text", "")
        citation_str = f"[{title}] {section}"
        citations.append(citation_str)
        context_lines.append(f"Source [{idx}] ({citation_str}):\n{text}")

    context_block = "\n\n".join(context_lines)

    # Deterministic statutory summary response
    primary_citation = citations[0] if citations else "the relevant statute"
    lead_text = retrieved_chunks[0].get("text", "").strip()
    if len(lead_text) > 300:
        lead_text = lead_text[:297] + "..."

    structured_answer = (
        f"According to {primary_citation}:\n"
        f"\"{lead_text}\"\n\n"
        f"Additional applicable authorities include: {', '.join(citations[1:3]) if len(citations) > 1 else 'None'}.\n\n"
        f"{DISCLAIMER_TEXT}"
    )

    return {
        "answer": structured_answer,
        "citations": citations,
        "abstained": False,
        "confidence": round(float(top_score), 4),
        "disclaimer": DISCLAIMER_TEXT,
        "context_used": context_block,
    }
