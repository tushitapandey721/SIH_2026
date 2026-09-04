"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Scale,
  Shield,
  BookOpen,
  Send,
  Sparkles,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  Bot,
  User,
  Globe2,
  FileCheck,
  Check,
  Loader2,
  Info,
  Database,
  Layers,
  FileText,
  ChevronDown,
  X,
  History,
  Trash2,
  Plus,
  ThumbsUp,
  ThumbsDown,
  Leaf,
  Sprout,
  Building2,
  ArrowLeftRight,
  Columns2,
  ShieldCheck,
  Languages,
} from "lucide-react";

interface Citation {
  source: string;
  section: string;
  url?: string;
  pdf_url?: string;
  official_url?: string;
  pdf_filename?: string;
}

interface QuestionData {
  id: string;
  question: string;
  options: boolean[];
  help_text?: string;
}

interface ABSResult {
  requires_nba_approval: boolean;
  requires_sbb_intimation: boolean;
  applicable_provision: string;
  exact_statutory_text?: string;
  next_steps: string[];
  relevant_forms: string[];
  sbb_state?: string;
  summary?: string;
}

interface ABSQuestionOption {
  label: string;
  value: boolean;
}

interface ABSQuestion {
  id: string;
  question: string;
  options: ABSQuestionOption[];
  help_text?: string;
}

interface ABSComplianceData {
  triggered: boolean;
  status: "needs_input" | "completed" | "not_triggered";
  answers: Record<string, boolean>;
  next_question?: ABSQuestion | null;
  result?: ABSResult | null;
}

interface TKDLIpcClass {
  code: string;
  description: string;
}

interface TKDLHints {
  formulation_category: string;
  formulation_description: string;
  therapeutic_area: string;
  ipc_classes: TKDLIpcClass[];
  classical_source_texts: string[];
  search_keywords: string[];
  is_simulated_search: boolean;
}

interface TKDLPriorArtWorkflowStep {
  step: string;
  detail: string;
}

interface HistoricalCaseItem {
  title: string;
  patent_number?: string;
  jurisdiction?: string;
  year_granted?: string;
  year_revoked?: string;
  facts?: string;
}

interface HistoricalCaseStudyData {
  triggered: boolean;
  title: string;
  subtitle?: string;
  turmeric_case: HistoricalCaseItem;
  neem_case: HistoricalCaseItem;
  closing_line: string;
  source_footnote: string;
}

interface TKDLPointerData {
  triggered: boolean;
  title: string;
  subtitle?: string;
  official_portal_url: string;
  statutory_provision: string;
  statutory_text: string;
  why_relevant: string;
  access_notice: string;
  hints: TKDLHints;
  patent_examiner_workflow: TKDLPriorArtWorkflowStep[];
  recommended_next_steps: string[];
  case_study?: HistoricalCaseStudyData;
}

interface ComparisonJurisdictionResult {
  answer: string;
  citations: Citation[];
  confidence: "high" | "medium" | "low" | string;
  abstained: boolean;
  classification?: string;
  classification_citation?: string;
  language?: string;
  provider_used?: string;
  abs_compliance?: ABSComplianceData;
  tkdl_pointer?: TKDLPointerData;
  timing_ms?: {
    retrieval?: number;
    llm?: number;
    total?: number;
  };
}

interface JurisdictionComparisonData {
  query: string;
  conversation_id: string;
  national: ComparisonJurisdictionResult;
  international: ComparisonJurisdictionResult;
  shared_citations_count: number;
  shared_sources: string[];
  is_zero_overlap: boolean;
  latency_ms: number;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  needs_classification?: boolean;
  question?: QuestionData;
  classification?: string;
  classification_citation?: string;
  citations?: Citation[];
  confidence?: "high" | "medium" | "low" | string;
  abstained?: boolean;
  language?: string;
  provider_used?: string;
  pending_formulation_answers?: Record<string, boolean>;
  abs_compliance?: ABSComplianceData;
  tkdl_pointer?: TKDLPointerData;
  case_study?: HistoricalCaseStudyData;
  is_comparison?: boolean;
  comparison_data?: JurisdictionComparisonData;
  timestamp: string;
  isError?: boolean;
  isStreaming?: boolean;
  originalContent?: string;
  activeLanguage?: string;
  translations?: Record<string, string>;
  isTranslating?: boolean;
  showTranslation?: boolean;
  activeTranslationText?: string;
  isSimplified?: boolean;
  simplifiedContent?: string;
  originalFormalContent?: string;
  isSimplifying?: boolean;
  showSimplified?: boolean;
}

interface ConversationItem {
  id: string;
  title: string;
  jurisdiction: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_time?: string;
}

interface SamplePrompt {
  title: string;
  query: string;
  jurisdiction: "national" | "international";
  answers: Record<string, boolean>;
  is_compare?: boolean;
}

interface CorpusDocument {
  id: string;
  title: string;
  authority: string;
  category: string;
  jurisdiction: string;
  document_type: string;
  year: string;
  citation_prefix: string;
  official_url?: string;
  pdf_filename?: string;
  pdf_url?: string;
  url?: string;
}

interface CorpusProvenance {
  total_documents: number;
  national_count: number;
  international_count: number;
  national: CorpusDocument[];
  international: CorpusDocument[];
}

const SAMPLE_PROMPTS: SamplePrompt[] = [
  {
    title: "Compare: Traditional Knowledge Patenting",
    query: "Can I patent traditional knowledge?",
    jurisdiction: "national",
    answers: {},
    is_compare: true,
  },
  {
    title: "TKDL Classical Joint Oil",
    query: "My grandmother gave me a family recipe for a herbal joint pain oil made from classical Ayurvedic texts — can I patent it?",
    jurisdiction: "national",
    answers: {},
  },
  {
    title: "ABS Kerala Herbal Export",
    query: "I want to export a herbal supplement made from a plant sourced in Kerala — what approval do I need?",
    jurisdiction: "national",
    answers: {},
  },
  {
    title: "Classical Patentability",
    query: "Is a classical Ayurvedic formulation patentable under Indian Patent Law?",
    jurisdiction: "national",
    answers: { is_first_schedule_text: true },
  },
  {
    title: "Rule 158-B ASU Proof",
    query: "What safety and efficacy proof is required for a new Ayurvedic drug vs classical medicine?",
    jurisdiction: "national",
    answers: { is_first_schedule_text: false, requires_new_safety_efficacy: true },
  },
  {
    title: "Biodiversity Export Clearance",
    query: "Does an Ayurvedic company need NBA approval before exporting Indian biological resources?",
    jurisdiction: "national",
    answers: { is_first_schedule_text: false },
  },
  {
    title: "International Nagoya Access",
    query: "What are the prior informed consent rules under the Nagoya Protocol for traditional knowledge?",
    jurisdiction: "international",
    answers: {},
  },
];

const TRANSLATE_LANGUAGES = [
  { code: "en", name: "English", native: "English", script: "Latin" },
  { code: "hi", name: "Hindi", native: "हिन्दी", script: "Devanagari" },
  { code: "pa", name: "Punjabi", native: "ਪੰਜਾਬੀ", script: "Gurmukhi" },
  { code: "ml", name: "Malayalam", native: "മലയാളം", script: "Malayalam" },
  { code: "ta", name: "Tamil", native: "தமிழ்", script: "Tamil" },
] as const;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Resolves the statutory source PDF file URL to view official Act / Treaty documents.
 */
function getCitationPdfUrl(cit: Citation): string {
  if (cit.pdf_url && cit.pdf_url.trim()) return cit.pdf_url;
  if (cit.url && cit.url.includes("/pdf/")) return cit.url;

  const text = `${cit.source || ""} ${cit.section || ""}`.toLowerCase();
  let filename = "Patents Act, 1970.pdf";

  if (text.includes("pct") || text.includes("patent cooperation")) {
    filename = "PCT (Patent Cooperation Treaty).pdf";
  } else if (text.includes("gratk")) {
    filename = "WIPO GRATK Treaty (2024).pdf";
  } else if (text.includes("nagoya")) {
    filename = "Nagoya Protocol.pdf";
  } else if (text.includes("trips") || text.includes("wto")) {
    filename = "trips_agreement.pdf";
  } else if (text.includes("cbd") || text.includes("convention on biological diversity")) {
    filename = "Convention on Biological Diversity (CBD).pdf";
  } else if (text.includes("magic remedies") || text.includes("dmr") || text.includes("advertisement")) {
    filename = "Drugs and Magic Remedies (Objectionable Advertisements) Act.pdf";
  } else if (text.includes("aahara") || text.includes("fssai")) {
    filename = "Gazette_Notification_Ayurveda_Aahara.pdf";
  } else if (text.includes("phytopharmaceutical") || text.includes("ipc")) {
    filename = "Phytopharmaceutical-Drugs-General-Guidance-for-Development.pdf";
  } else if (text.includes("2025") && (text.includes("rule") || text.includes("diversity"))) {
    filename = "The Biological Diversity (Amendment) Rules, 2025.pdf";
  } else if (text.includes("bd rules") || (text.includes("rule") && text.includes("diversity")) || text.includes("rules, 2024")) {
    filename = "The Biological Diversity Rules, 2024.pdf";
  } else if (text.includes("biological diversity") || text.includes("bda") || text.includes("biodiversity")) {
    filename = "Biological Diversity (Amendment) Act, 2023.pdf";
  } else if (text.includes("drug") || text.includes("cosmetic") || text.includes("d&c") || text.includes("158-b") || text.includes("158b") || text.includes("schedule t") || text.includes("schedule e")) {
    filename = "2016DrugsandCosmeticsAct1940Rules1945.pdf";
  } else if (text.includes("trademark") || text.includes("trade mark") || text.includes("tm act")) {
    filename = "The Trade Marks Act, 1999.pdf";
  } else if (text.includes("copyright")) {
    filename = "The Copyright Act, 1957.pdf";
  } else if (text.includes("geographical indication") || text.includes("gi act")) {
    filename = "Geographical Indications of Goods.pdf";
  } else if (text.includes("design")) {
    filename = "The Designs Act, 2000 (Act No. 16 of 2000).pdf";
  } else if (text.includes("patent")) {
    filename = "Patents Act, 1970.pdf";
  }

  return `${API_BASE_URL}/pdf/${encodeURIComponent(filename)}`;
}

export default function Home() {
  const [jurisdiction, setJurisdiction] = useState<"national" | "international">("national");
  const [isCompareMode, setIsCompareMode] = useState<boolean>(false);
  const [inputQuery, setInputQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("Analyzing inquiry...");
  const [formulationAnswers, setFormulationAnswers] = useState<Record<string, boolean>>({});
  const [lastQuery, setLastQuery] = useState("");
  const [showFacilitatorModal, setShowFacilitatorModal] = useState(false);
  const [showCorpusModal, setShowCorpusModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [corpusData, setCorpusData] = useState<CorpusProvenance | null>(null);
  const [conversationsList, setConversationsList] = useState<ConversationItem[]>([]);
  const [mySessionIds, setMySessionIds] = useState<string[]>([]);
  const [historyTab, setHistoryTab] = useState<"my" | "archive">("my");
  const heroTextareaRef = useRef<HTMLTextAreaElement>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("ipsakti_my_sessions");
      if (raw) {
        setMySessionIds(JSON.parse(raw));
      }
    } catch (e) {
      console.warn("Could not parse local session IDs", e);
    }
  }, []);

  const trackMySession = (id: string) => {
    if (!id) return;
    setMySessionIds((prev) => {
      if (prev.includes(id)) return prev;
      const next = [id, ...prev];
      try {
        localStorage.setItem("ipsakti_my_sessions", JSON.stringify(next));
      } catch (_) {}
      return next;
    });
  };
  const [backendError, setBackendError] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<
    Record<
      string,
      {
        rating?: "up" | "down";
        showCommentInput?: boolean;
        comment?: string;
        submitted?: boolean;
      }
    >
  >({});

  const handleFeedback = async (
    msgId: string,
    rating: "up" | "down",
    comment?: string,
    msgContent?: string,
    citations?: Citation[]
  ) => {
    setFeedbackState((prev) => ({
      ...prev,
      [msgId]: {
        ...prev[msgId],
        rating,
        comment: comment !== undefined ? comment : prev[msgId]?.comment,
        submitted: comment !== undefined || rating === "up",
        showCommentInput: rating === "down" && comment === undefined,
      },
    }));

    let associatedQuery = lastQuery;
    const msgIdx = messages.findIndex((m) => m.id === msgId);
    if (msgIdx > 0) {
      for (let i = msgIdx - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
          associatedQuery = messages[i].content;
          break;
        }
      }
    }

    try {
      await fetch(`${API_BASE_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          query: associatedQuery,
          answer_snippet: (msgContent || "").slice(0, 300),
          citations: citations || [],
          rating,
          comment: comment || null,
        }),
      });
    } catch (err) {
      console.warn("Failed to record feedback:", err);
    }
  };

  const [openTranslateMsgId, setOpenTranslateMsgId] = useState<string | null>(null);

  const handleTranslateMessage = async (msgId: string, targetLang: string) => {
    setOpenTranslateMsgId(null);
    const targetMsg = messages.find((m) => m.id === msgId);
    if (!targetMsg) return;

    if (targetLang === "en") {
      // Hide translation card to view only the original English text
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                showTranslation: false,
                activeLanguage: "en",
                activeTranslationText: undefined,
              }
            : m
        )
      );
      return;
    }

    // Check client-side cached translation to avoid re-querying API
    const cached = targetMsg.translations?.[targetLang];
    if (cached) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                showTranslation: true,
                activeLanguage: targetLang,
                activeTranslationText: cached,
              }
            : m
        )
      );
      return;
    }

    // Set local loading indicator on this specific message only
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, isTranslating: true } : m))
    );

    try {
      const baseText = targetMsg.content;
      const res = await fetch(`${API_BASE_URL}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer_text: baseText,
          citations: targetMsg.citations || [],
          target_language: targetLang,
        }),
      });

      if (!res.ok) {
        throw new Error(`Translation failed with HTTP ${res.status}`);
      }

      const data = await res.json();
      const translatedText = data.translated_text || baseText;

      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== msgId) return m;
          const currentTranslations = m.translations || {};
          return {
            ...m,
            // Keep original m.content strictly untouched!
            showTranslation: true,
            activeLanguage: targetLang,
            activeTranslationText: translatedText,
            isTranslating: false,
            translations: {
              ...currentTranslations,
              [targetLang]: translatedText,
            },
          };
        })
      );
    } catch (err) {
      console.error("Failed to translate answer:", err);
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, isTranslating: false } : m))
      );
    }
  };

  const handleToggleSimplify = async (msgId: string) => {
    const targetMsg = messages.find((m) => m.id === msgId);
    if (!targetMsg) return;

    // If currently showing simplified card below, toggle it off
    if (targetMsg.showSimplified) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                showSimplified: false,
              }
            : m
        )
      );
      return;
    }

    // If cached simplified version already exists, show it below without re-querying
    if (targetMsg.simplifiedContent) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                showSimplified: true,
              }
            : m
        )
      );
      return;
    }

    // Set local loading indicator on this specific message
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, isSimplifying: true } : m))
    );

    try {
      const formalText = targetMsg.content;
      const res = await fetch(`${API_BASE_URL}/simplify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer_text: formalText,
          citations: targetMsg.citations || [],
        }),
      });

      if (!res.ok) {
        throw new Error(`Simplification failed with HTTP ${res.status}`);
      }

      const data = await res.json();
      const simplifiedText = data.simplified_text || data.simplified_answer || formalText;

      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== msgId) return m;
          return {
            ...m,
            // Keep original m.content strictly untouched!
            showSimplified: true,
            simplifiedContent: simplifiedText,
            isSimplifying: false,
          };
        })
      );
    } catch (err) {
      console.error("Failed to simplify answer:", err);
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, isSimplifying: false } : m))
      );
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const fetchConversations = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversationsList(data.conversations || []);
      }
    } catch (err) {
      console.warn("Could not fetch conversations:", err);
    }
  };

  // Load dynamic corpus provenance and past conversations from backend
  useEffect(() => {
    fetch(`${API_BASE_URL}/corpus`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setCorpusData(data);
      })
      .catch((err) => console.warn("Could not fetch corpus provenance:", err));

    fetchConversations();

    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("view") === "history") {
        setShowHistoryModal(true);
      } else if (params.get("view") === "corpus") {
        setShowCorpusModal(true);
      }
    }
  }, []);

  const loadConversation = async (convId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/conversations/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setConversationId(data.id);
        trackMySession(data.id);
        setJurisdiction(data.jurisdiction === "international" ? "international" : "national");
        const loadedMsgs = (data.messages || []).map((m: any) => ({
          ...m,
          originalContent: m.originalContent || m.content,
          activeLanguage: m.activeLanguage || "en",
          translations: m.translations || (m.content ? { en: m.content } : {}),
          case_study: m.case_study || m.tkdl_pointer?.case_study,
        }));
        setMessages(loadedMsgs);
        setShowHistoryModal(false);
      }
    } catch (err) {
      console.error("Failed to load conversation:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE_URL}/conversations/${convId}`, { method: "DELETE" });
      if (res.ok) {
        setConversationsList((prev) => prev.filter((c) => c.id !== convId));
        setMySessionIds((prev) => {
          const next = prev.filter((id) => id !== convId);
          try {
            localStorage.setItem("ipsakti_my_sessions", JSON.stringify(next));
          } catch (_) {}
          return next;
        });
        if (conversationId === convId) {
          handleResetChat();
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  const myConversations = conversationsList.filter((c) => mySessionIds.includes(c.id));
  const displayedConversations = historyTab === "my" ? myConversations : conversationsList;

  const sendQueryToBackend = async (
    query: string,
    currentAnswers: Record<string, boolean>,
    targetJurisdiction: "national" | "international",
    customHistory?: Message[]
  ) => {
    if (!query || !query.trim()) {
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "Error 400: Query cannot be empty or whitespace-only.",
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
      return;
    }

    setIsLoading(true);
    setBackendError(null);
    setLoadingStep("Connecting to statutory inference engine...");

    const messageHistory = customHistory || messages;
    const historyPayload = messageHistory
      .filter((m) => !m.isError)
      .map((m) => ({
        role: m.role,
        content: m.content,
        citations: m.citations || [],
        language: m.language,
      }));

    const payload = {
      query: query.trim(),
      jurisdiction: targetJurisdiction,
      formulation_answers: currentAnswers,
      conversation_id: conversationId,
      history: historyPayload,
    };

    try {
      // Stream real backend pipeline stages and token deltas using SSE
      const response = await fetch(`${API_BASE_URL}/ask/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorDetail = `Server responded with status ${response.status}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errorDetail = errJson.detail;
        } catch (_) {}
        throw new Error(errorDetail);
      }

      if (!response.body) {
        throw new Error("No response body received from server stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentAssistantId: string | null = null;
      let accumulatedContent = "";
      let currentAbsCompliance: ABSComplianceData | undefined = undefined;
      let currentTkdlPointer: TKDLPointerData | undefined = undefined;
      let currentCaseStudy: HistoricalCaseStudyData | undefined = undefined;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const eventJson = JSON.parse(line.substring(6));

            if (eventJson.conversation_id && !conversationId) {
              setConversationId(eventJson.conversation_id);
              trackMySession(eventJson.conversation_id);
            }

            if (eventJson.message) {
              setLoadingStep(eventJson.message);
            }

            // Real-time ABS Compliance Stage (Prompt 1)
            if (eventJson.stage === "abs_compliance" && eventJson.data) {
              currentAbsCompliance = eventJson.data;
              if (currentAssistantId) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === currentAssistantId ? { ...m, abs_compliance: eventJson.data } : m
                  )
                );
              }
            }

            // Real-time TKDL Prior-Art Pointer Stage (Prompt 2)
            if (eventJson.stage === "tkdl_pointer" && eventJson.data) {
              currentTkdlPointer = eventJson.data;
              if (eventJson.data.case_study) {
                currentCaseStudy = eventJson.data.case_study;
              }
              if (currentAssistantId) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === currentAssistantId
                      ? {
                          ...m,
                          tkdl_pointer: eventJson.data,
                          case_study: eventJson.data.case_study || currentCaseStudy,
                        }
                      : m
                  )
                );
              }
            }

            // Real-time live token streaming into message bubble
            if (eventJson.stage === "synthesis" || eventJson.stage === "translating_answer") {
              if (!currentAssistantId) {
                currentAssistantId = "stream-" + Date.now();
                accumulatedContent = "";
                const newAssistantMsg: Message = {
                  id: currentAssistantId,
                  role: "assistant",
                  content: "",
                  abs_compliance: currentAbsCompliance,
                  tkdl_pointer: currentTkdlPointer,
                  isStreaming: true,
                  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                };
                setMessages((prev) => [...prev, newAssistantMsg]);
              }
            }

            if (eventJson.stage === "llm_token") {
              const textChunk =
                eventJson.answer_delta !== undefined && eventJson.answer_delta !== null
                  ? eventJson.answer_delta
                  : eventJson.delta;

              if (textChunk) {
                if (!currentAssistantId) {
                  currentAssistantId = "stream-" + Date.now();
                  accumulatedContent = textChunk;
                  const newAssistantMsg: Message = {
                    id: currentAssistantId,
                    role: "assistant",
                    content: accumulatedContent,
                    abs_compliance: currentAbsCompliance,
                    tkdl_pointer: currentTkdlPointer,
                    isStreaming: true,
                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                  };
                  setMessages((prev) => [...prev, newAssistantMsg]);
                } else {
                  if (eventJson.is_translated && textChunk.length > 30 && !accumulatedContent.includes(textChunk)) {
                    accumulatedContent = textChunk;
                  } else {
                    accumulatedContent += textChunk;
                  }
                  const currentContent = accumulatedContent;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === currentAssistantId ? { ...m, content: currentContent, isStreaming: true } : m
                    )
                  );
                }
              }
            }

            if (eventJson.stage === "complete" && eventJson.data) {
              const data = eventJson.data;
              if (data.conversation_id) {
                setConversationId(data.conversation_id);
                trackMySession(data.conversation_id);
              }
              fetchConversations();

              if (data.needs_classification) {
                if (currentAssistantId) {
                  setMessages((prev) => prev.filter((m) => m.id !== currentAssistantId));
                }
                const assistantMsg: Message = {
                  id: Date.now().toString(),
                  role: "assistant",
                  content: "Regulatory classification required to determine the exact statutory pathway:",
                  needs_classification: true,
                  question: data.question,
                  language: data.language,
                  pending_formulation_answers: currentAnswers,
                  abs_compliance: data.abs_compliance || currentAbsCompliance,
                  tkdl_pointer: data.tkdl_pointer || currentTkdlPointer,
                  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                };
                setMessages((prev) => [...prev, assistantMsg]);
              } else {
                const rawContent = data.answer || accumulatedContent || "No response text generated.";
                const finalMsg: Message = {
                  id: currentAssistantId || Date.now().toString(),
                  role: "assistant",
                  content: rawContent,
                  originalContent: rawContent,
                  activeLanguage: "en",
                  translations: { en: rawContent },
                  needs_classification: false,
                  classification: data.classification,
                  classification_citation: data.classification_citation,
                  citations: data.citations || [],
                  confidence: data.confidence || "medium",
                  abstained: data.abstained || false,
                  language: data.language || "en",
                  provider_used: data.provider_used,
                  abs_compliance: data.abs_compliance || currentAbsCompliance,
                  tkdl_pointer: data.tkdl_pointer || currentTkdlPointer,
                  case_study: data.case_study || data.tkdl_pointer?.case_study || currentCaseStudy,
                  isStreaming: false,
                  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                };
                if (currentAssistantId) {
                  setMessages((prev) => prev.map((m) => (m.id === currentAssistantId ? finalMsg : m)));
                } else {
                  setMessages((prev) => [...prev, finalMsg]);
                }
              }
            } else if (eventJson.stage === "error") {
              if (currentAssistantId) {
                setMessages((prev) => prev.filter((m) => m.id !== currentAssistantId));
              }
              throw new Error(eventJson.error || "Backend pipeline error occurred.");
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Backend request error:", err);
      setBackendError(err.message || `Unable to reach backend at ${API_BASE_URL}`);
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `Error: ${err.message || "Failed to communicate with IP-SAKTI Sahayak backend"}.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendCompareQueryToBackend = async (
    query: string,
    customHistory?: Message[]
  ) => {
    if (!query || !query.trim()) {
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "Error 400: Query cannot be empty or whitespace-only.",
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
      return;
    }

    setIsLoading(true);
    setBackendError(null);
    setLoadingStep("Executing parallel dual-jurisdiction statutory analysis...");

    const payload = {
      query: query.trim(),
      conversation_id: conversationId,
      formulation_answers: formulationAnswers,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/ask/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorDetail = `Server responded with status ${response.status}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errorDetail = errJson.detail;
        } catch (_) {}
        throw new Error(errorDetail);
      }

      const data: JurisdictionComparisonData = await response.json();
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        trackMySession(data.conversation_id);
      }
      fetchConversations();

      const assistantMsg: Message = {
        id: "compare-" + Date.now().toString(),
        role: "assistant",
        content: `Dual-Jurisdiction Analysis for: "${data.query}"`,
        is_comparison: true,
        comparison_data: data,
        confidence:
          data.national.confidence === "high" || data.international.confidence === "high"
            ? "high"
            : "medium",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Compare request error:", err);
      setBackendError(err.message || `Unable to execute comparison at ${API_BASE_URL}`);
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `Comparison Error: ${err.message || "Failed to communicate with IP-SAKTI Sahayak backend"}.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;

    const currentQuery = inputQuery.trim();
    setLastQuery(currentQuery);
    setFormulationAnswers({});

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: currentQuery,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInputQuery("");

    if (isCompareMode) {
      sendCompareQueryToBackend(currentQuery, newMessages);
    } else {
      sendQueryToBackend(currentQuery, {}, jurisdiction, newMessages);
    }
  };

  const handleClassificationSelect = (answerKey: string, answerValue: boolean) => {
    if (isLoading) return;

    const updatedAnswers = {
      ...formulationAnswers,
      [answerKey]: answerValue,
    };
    setFormulationAnswers(updatedAnswers);

    const userChoiceMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: answerValue ? "Yes, this applies." : "No, this does not apply.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    const newMessages = [...messages, userChoiceMsg];
    setMessages(newMessages);

    sendQueryToBackend(lastQuery, updatedAnswers, jurisdiction, newMessages);
  };

  const handleABSOptionSelect = async (msgId: string, answerKey: string, answerValue: boolean) => {
    const msg = messages.find((m) => m.id === msgId);
    const existingAnswers = msg?.abs_compliance?.answers || {};
    const updatedAnswers = {
      ...existingAnswers,
      [answerKey]: answerValue,
    };

    // Determine query context from last query or message content
    let associatedQuery = lastQuery;
    if (!associatedQuery && msg) {
      const msgIdx = messages.findIndex((m) => m.id === msgId);
      if (msgIdx > 0) {
        for (let i = msgIdx - 1; i >= 0; i--) {
          if (messages[i].role === "user") {
            associatedQuery = messages[i].content;
            break;
          }
        }
      }
    }

    try {
      const res = await fetch(`${API_BASE_URL}/compliance/abs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: associatedQuery || "",
          answers: updatedAnswers,
        }),
      });
      if (res.ok) {
        const data: ABSComplianceData = await res.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? { ...m, abs_compliance: data }
              : m
          )
        );
      }
    } catch (err) {
      console.warn("Failed to update ABS compliance:", err);
    }
  };

  const handleSamplePromptClick = (sample: SamplePrompt) => {
    setLastQuery(sample.query);
    setFormulationAnswers(sample.answers);

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: sample.query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages([userMsg]);

    if (sample.is_compare) {
      setIsCompareMode(true);
      sendCompareQueryToBackend(sample.query, [userMsg]);
    } else {
      setIsCompareMode(false);
      setJurisdiction(sample.jurisdiction);
      sendQueryToBackend(sample.query, sample.answers, sample.jurisdiction, [userMsg]);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
    setFormulationAnswers({});
    setLastQuery("");
    setConversationId(null);
    setBackendError(null);
  };

  return (
    <main className="min-h-screen bg-[#050403] text-[#ede8d5] flex flex-col relative overflow-hidden">
      {/* Cinematic Ambient Background Atmosphere */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[850px] h-[850px] rounded-full orb-glow opacity-80 blur-[90px]" />
        <div className="absolute -bottom-40 left-1/2 -translate-x-1/2 w-[1100px] h-[500px] bg-gradient-to-t from-amber-600/10 via-amber-900/5 to-transparent blur-[120px]" />
        <div className="absolute inset-0 bg-[radial-gradient(#eab308_1px,transparent_1px)] [background-size:32px_32px] opacity-[0.035]" />
      </div>

      {/* Top Fixed Slim Nav */}
      <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-[#070605]/85 backdrop-blur-md px-4 sm:px-8 py-3 flex items-center justify-between">
        {/* Left: Minimal Wordmark */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-400/20 flex items-center justify-center text-amber-400">
            <Scale className="w-4 h-4" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-display text-lg tracking-wider text-[#f5eedb]">IP-SAKTI</span>
            <span className="text-[11px] tracking-widest text-stone-400 font-mono">SAHAYAK</span>
          </div>
        </div>

        {/* Center: Plain-Text Nav Items */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-stone-300">
          <button
            onClick={() => setShowCorpusModal(true)}
            className="hover:text-amber-300 transition-colors"
          >
            Corpus (17 Acts)
          </button>
          <a
            href={`${API_BASE_URL}/admin/audit/view`}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-emerald-300 transition-colors inline-flex items-center gap-1"
          >
            <span>DPDP Audit</span>
            <ExternalLink className="w-2.5 h-2.5 opacity-70" />
          </a>
        </nav>

        {/* Right: Consolidated Utility Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              fetchConversations();
              setShowHistoryModal(true);
            }}
            className="p-2 rounded-xl text-stone-300 hover:text-amber-300 hover:bg-white/5 transition-colors relative"
            title="Session History"
          >
            <History className="w-4 h-4" />
            {myConversations.length > 0 && (
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-amber-400" />
            )}
          </button>

          <button
            onClick={() => setShowCorpusModal(true)}
            className="md:hidden p-2 rounded-xl text-stone-300 hover:text-amber-300 hover:bg-white/5 transition-colors"
            title="Corpus (17 Acts)"
          >
            <Database className="w-4 h-4" />
          </button>

          {messages.length > 0 && (
            <button
              onClick={handleResetChat}
              className="p-2 rounded-xl text-stone-300 hover:text-white hover:bg-white/5 transition-colors flex items-center gap-1.5 text-xs font-medium"
              title="Start New Inquiry"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="hidden sm:inline">New Query</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col max-w-6xl w-full mx-auto px-4 sm:px-6 z-10 pt-4 pb-36">
        {/* LANDING / IDLE STATE (Split-Screen Hero) */}
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col justify-center my-auto py-8 lg:py-12">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
              {/* Left Column: Wordmark Headline, MSME Line, Numerals, Soft Seal Graphic */}
              <div className="lg:col-span-6 flex flex-col justify-center relative pr-0 lg:pr-4">
                {/* Soft Graphic Element (Pattern #6): Glowing Seal Motif in background */}
                <div className="absolute -left-10 -top-10 w-80 h-80 pointer-events-none opacity-20 select-none hidden sm:block">
                  <div className="w-full h-full rounded-full border border-amber-400/25 border-dashed animate-[spin_120s_linear_infinite]" />
                  <div className="absolute inset-8 rounded-full border border-amber-300/15" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Scale className="w-28 h-28 text-amber-400/25 stroke-[1]" />
                  </div>
                </div>

                <div className="relative z-10 space-y-5">
                  <div className="inline-flex items-center gap-2 text-xs font-mono tracking-widest text-amber-400/90 uppercase">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                    <span>Statutory AYUSH Intelligence</span>
                  </div>

                  <h1 className="font-display text-4xl sm:text-6xl lg:text-6xl font-bold tracking-tight text-[#f5eedb] leading-[0.95] uppercase">
                    Protect <br />
                    The Heritage. <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-400 to-amber-100">
                      Own The Future.
                    </span>
                  </h1>

                  <p className="text-xs sm:text-sm text-stone-300 font-light leading-relaxed max-w-lg">
                    Statutory Ayurvedic & Traditional Knowledge verification under Section 3(p), ASU drug classification under Rule 158-B, and NBA/Nagoya access-benefit clearance.
                  </p>

                  {/* Non-lawyer plain language line (Accuracy Fix #2) */}
                  <div className="p-3.5 rounded-xl bg-amber-500/5 border-l-2 border-amber-400/70 text-xs sm:text-sm text-stone-200 leading-relaxed max-w-lg">
                    <span className="text-amber-300 font-medium">In plain terms:</span> find out what you can protect, and how, before you invest.
                  </div>

                  {/* Confident Large Numerals (Pattern #3) */}
                  <div className="grid grid-cols-3 gap-4 sm:gap-6 pt-4 border-t border-white/5 max-w-lg">
                    <div>
                      <div className="font-mono text-3xl sm:text-4xl font-bold text-[#f5eedb] tracking-tight">17</div>
                      <div className="text-[11px] font-mono text-stone-400 mt-1">Verified Acts</div>
                    </div>
                    <div>
                      <div className="font-mono text-3xl sm:text-4xl font-bold text-amber-300 tracking-tight">~300ms</div>
                      <div className="text-[11px] font-mono text-stone-400 mt-1">Dual RAG Recall</div>
                    </div>
                    <div>
                      <div className="font-mono text-3xl sm:text-4xl font-bold text-[#f5eedb] tracking-tight">87.5%</div>
                      <div className="text-[11px] font-mono text-stone-400 mt-1">Recall@5 Benchmark</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Functional Swap-Style Tool Panel */}
              <div className="lg:col-span-6 flex flex-col justify-center">
                <div className="bg-[#0c0a08]/95 border border-white/10 rounded-3xl p-5 sm:p-7 shadow-2xl space-y-4">
                  {/* Tool Header: Primary Jurisdiction Segmented Control */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-mono text-stone-400 px-1">
                      <span>JURISDICTION MODE</span>
                      {isCompareMode && (
                        <span className="text-[10px] text-amber-300 font-semibold uppercase">Dual Parallel Inference</span>
                      )}
                    </div>

                    <div className="grid grid-cols-3 bg-black/60 p-1 rounded-2xl border border-white/5">
                      <button
                        type="button"
                        onClick={() => {
                          setJurisdiction("national");
                          setIsCompareMode(false);
                        }}
                        className={`py-2 px-2 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                          !isCompareMode && jurisdiction === "national"
                            ? "bg-[#1f1a14] text-amber-200 border border-amber-400/30 shadow-sm"
                            : "text-stone-400 hover:text-stone-200"
                        }`}
                      >
                        <Shield className="w-3.5 h-3.5 shrink-0" />
                        <span className="truncate">India</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setJurisdiction("international");
                          setIsCompareMode(false);
                        }}
                        className={`py-2 px-2 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                          !isCompareMode && jurisdiction === "international"
                            ? "bg-[#1f1a14] text-sky-200 border border-sky-400/30 shadow-sm"
                            : "text-stone-400 hover:text-stone-200"
                        }`}
                      >
                        <Globe2 className="w-3.5 h-3.5 shrink-0" />
                        <span className="truncate">Global</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setIsCompareMode(true)}
                        className={`py-2 px-2 rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                          isCompareMode
                            ? "bg-amber-400/15 text-amber-300 border border-amber-400/40 shadow-sm"
                            : "text-stone-400 hover:text-stone-200"
                        }`}
                      >
                        <Columns2 className="w-3.5 h-3.5 shrink-0" />
                        <span className="truncate">Compare</span>
                      </button>
                    </div>
                  </div>

                  {/* Query Input Well */}
                  <div className="bg-black/70 border border-white/5 focus-within:border-amber-400/50 rounded-2xl p-4 transition-all space-y-2.5">
                    <textarea
                      ref={heroTextareaRef}
                      value={inputQuery}
                      onChange={(e) => setInputQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleUserSubmit();
                        }
                      }}
                      placeholder={
                        isCompareMode
                          ? "Compare National (Patents Act) vs International (Nagoya / WIPO) side-by-side..."
                          : `Ask any Ayurvedic patent, licensing (Rule 158-B), or biodiversity question (${
                              jurisdiction === "national" ? "India" : "Global"
                            })...`
                      }
                      rows={3}
                      disabled={isLoading}
                      className="w-full bg-transparent border-0 outline-none text-sm sm:text-base text-[#f5eedb] placeholder-stone-400 resize-none font-light leading-relaxed focus:ring-0"
                    />

                    <div className="flex items-center justify-between text-[11px] text-stone-400 pt-2 border-t border-white/5 font-mono">
                      <span>Retrieval-verified citations</span>
                      <span>Press Enter ↵ to ask</span>
                    </div>
                  </div>

                  {/* Single Clear Accent CTA Button (Pattern #5) */}
                  <button
                    type="button"
                    onClick={() => handleUserSubmit()}
                    disabled={!inputQuery.trim() || isLoading}
                    className="w-full py-3.5 sm:py-4 rounded-2xl bg-amber-400 hover:bg-amber-300 active:scale-[0.99] text-stone-950 font-bold text-sm sm:text-base shadow-[0_0_25px_rgba(251,191,36,0.3)] transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                  >
                    {isLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin text-black" />
                    ) : (
                      <>
                        <span>{isCompareMode ? "Compare Both Jurisdictions" : "Ask Sahayak"}</span>
                        <ArrowRight className="w-4 h-4 text-stone-950 stroke-[2.5]" />
                      </>
                    )}
                  </button>

                  {/* Streamlined Suggested Queries */}
                  <div className="space-y-2 pt-1">
                    <div className="text-[11px] font-mono tracking-wider uppercase text-stone-400 flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-amber-400" />
                      <span>Quick Verified Queries</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {SAMPLE_PROMPTS.slice(0, 4).map((sample, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleSamplePromptClick(sample)}
                          className="p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/5 hover:border-amber-400/30 text-stone-300 hover:text-[#f5eedb] text-xs font-normal transition-all text-left flex items-center justify-between gap-2 group"
                        >
                          <span className="truncate">{sample.title}</span>
                          <ArrowRight className="w-3 h-3 text-stone-400 group-hover:text-amber-300 group-hover:translate-x-0.5 transition-all shrink-0" />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Provenance & Microcopy (High Contrast) */}
            <div className="mt-8 pt-4 border-t border-white/5 text-center flex flex-wrap items-center justify-center gap-3 text-xs text-stone-400 font-mono">
              <span>Every claim cites its source</span>
              <span>•</span>
              <button
                onClick={() => setShowCorpusModal(true)}
                className="text-amber-400/90 hover:text-amber-300 hover:underline transition-colors"
              >
                17 Indexed Statutory Acts
              </button>
              <span>•</span>
              <span>Multilingual AI Translation with English citation anchors</span>
            </div>
          </div>
        )}

        {/* CHAT VIEW */}
        {messages.length > 0 && (
          <div className="space-y-6 pt-4">
            {messages.map((msg) => {
              const isUser = msg.role === "user";

              if (isUser) {
                return (
                  <div key={msg.id} className="flex justify-end gap-3 items-start pl-8">
                    <div className="max-w-2xl bg-gradient-to-r from-amber-950/50 to-[#221c14]/90 border border-amber-500/30 text-[#f5eedb] rounded-2xl rounded-tr-none px-5 py-3.5 shadow-xl">
                      <p className="text-sm sm:text-base leading-relaxed font-light">{msg.content}</p>
                      <span className="block text-[10px] text-amber-400/60 text-right mt-1.5 font-mono">
                        {msg.timestamp}
                      </span>
                    </div>
                    <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4 text-amber-200" />
                    </div>
                  </div>
                );
              }

              // Parallel Comparison Response View
              if (msg.is_comparison && msg.comparison_data) {
                const cmp = msg.comparison_data;
                return (
                  <div key={msg.id} className="w-full space-y-4 animate-in fade-in-50 duration-300">
                    {/* Top Comparative Header & Zero Overlap Badge */}
                    <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-[#0d0b09]/95 border border-amber-500/30 backdrop-blur-xl shadow-2xl">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-amber-600/30 to-black border border-amber-400/40 flex items-center justify-center text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.25)]">
                          <Columns2 className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h2 className="text-sm sm:text-base font-display font-semibold text-[#f5eedb] tracking-wide">
                              Side-by-Side Jurisdiction Comparison
                            </h2>
                            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300">
                              Dual Parallel RAG
                            </span>
                          </div>
                          <p className="text-xs text-stone-400 font-light">
                            Independent statutory pipelines: National (India) vs International (Treaties)
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-2.5">
                        {/* Parallel Latency Badge */}
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-white/5 border border-white/10 text-stone-300">
                          <span className="text-stone-400">Parallel Latency:</span>
                          <span className="text-amber-300 font-semibold">{cmp.latency_ms}ms</span>
                        </span>

                        {/* Zero Overlap Badge (Item 4 in requirements) */}
                        {cmp.is_zero_overlap ? (
                          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-950/70 border border-emerald-500/50 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                            <span>0 shared sources — jurisdictions kept separate</span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-rose-950/70 border border-rose-500/50 text-rose-300">
                            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                            <span>{cmp.shared_citations_count} Shared Sources Overlap</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Dual Panels Grid: Side-by-Side on Desktop (grid-cols-2), Stacked on Mobile (grid-cols-1) */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full items-stretch">
                      {/* Left Panel: India (National) */}
                      <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-amber-500/30 bg-gradient-to-b from-[#120f0b]/95 to-[#090806]/95 shadow-2xl flex flex-col justify-between">
                        <div>
                          {/* Panel Header */}
                          <div className="flex items-center justify-between border-b border-amber-500/15 pb-3.5 mb-4">
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-400/30 flex items-center justify-center text-amber-300">
                                <Shield className="w-4 h-4" />
                              </div>
                              <div>
                                <span className="font-display text-sm font-semibold tracking-wide text-amber-100 uppercase">
                                  India (National)
                                </span>
                                <span className="block text-[10px] text-stone-400 font-mono">
                                  Patents Act, Biological Diversity, D&C
                                </span>
                              </div>
                            </div>
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium uppercase ${
                                cmp.national.confidence?.toLowerCase() === "high"
                                  ? "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                                  : cmp.national.confidence?.toLowerCase() === "medium"
                                  ? "bg-amber-950/60 border border-amber-500/40 text-amber-300"
                                  : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                              }`}
                            >
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${
                                  cmp.national.confidence?.toLowerCase() === "high"
                                    ? "bg-emerald-400"
                                    : cmp.national.confidence?.toLowerCase() === "medium"
                                    ? "bg-amber-400"
                                    : "bg-rose-400"
                                }`}
                              />
                              {cmp.national.confidence} Confidence
                            </span>
                          </div>

                          {/* Classification badge if present */}
                          {cmp.national.classification && (
                            <div className="mb-3">
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/20 text-amber-300 text-[11px] font-mono uppercase">
                                <CheckCircle2 className="w-3 h-3 text-amber-400" />
                                {cmp.national.classification.replace(/_/g, " ")}
                              </span>
                            </div>
                          )}

                          {/* Answer Content or Abstention */}
                          {cmp.national.abstained ? (
                            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-400/30 text-amber-200 text-xs sm:text-sm space-y-2">
                              <div className="flex items-center gap-2 font-semibold text-amber-300 uppercase tracking-wider">
                                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                                <span>No Relevant National Authority (Abstained)</span>
                              </div>
                              <p className="text-stone-300 leading-relaxed font-light whitespace-pre-line">
                                {cmp.national.answer}
                              </p>
                            </div>
                          ) : (
                            <div className="prose prose-invert prose-amber max-w-none text-xs sm:text-sm leading-relaxed text-[#ede8d5] font-light whitespace-pre-line">
                              {cmp.national.answer}
                            </div>
                          )}
                        </div>

                        {/* Citation Ledger Underneath National Panel */}
                        <div className="mt-6 pt-4 border-t border-amber-500/15">
                          <div className="text-xs font-mono uppercase tracking-wider text-amber-400/90 mb-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <FileCheck className="w-3.5 h-3.5 text-amber-400" />
                              <span>National Statutory Citations ({cmp.national.citations?.length || 0})</span>
                            </div>
                            <span className="text-[10px] text-stone-500 font-mono">Domestic Law</span>
                          </div>

                          {cmp.national.citations && cmp.national.citations.length > 0 ? (
                            <div className="space-y-2">
                              {cmp.national.citations.map((cit, cIdx) => {
                                const pdfUrl = getCitationPdfUrl(cit);
                                return (
                                  <div
                                    key={cIdx}
                                    className="p-3 rounded-xl bg-black/40 border border-amber-500/20 hover:border-amber-400/50 transition-all flex flex-col justify-between"
                                  >
                                    <div className="flex items-center justify-between gap-2 mb-1">
                                      <span className="text-[11px] font-mono text-amber-300 font-bold">
                                        {cit.section}
                                      </span>
                                      <a
                                        href={pdfUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-[10px] text-amber-300 hover:bg-amber-400 hover:text-black transition-all"
                                      >
                                        <FileText className="w-2.5 h-2.5" />
                                        <span>PDF</span>
                                        <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                                      </a>
                                    </div>
                                    <div className="text-xs text-stone-300 font-normal leading-snug">
                                      {cit.source}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="text-xs text-stone-500 italic">No national statutory citations recorded.</p>
                          )}
                        </div>
                      </div>

                      {/* Right Panel: International (Treaties) */}
                      <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-sky-500/30 bg-gradient-to-b from-[#0b1016]/95 to-[#07090e]/95 shadow-2xl flex flex-col justify-between">
                        <div>
                          {/* Panel Header */}
                          <div className="flex items-center justify-between border-b border-sky-500/15 pb-3.5 mb-4">
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-xl bg-sky-500/15 border border-sky-400/30 flex items-center justify-center text-sky-300">
                                <Globe2 className="w-4 h-4" />
                              </div>
                              <div>
                                <span className="font-display text-sm font-semibold tracking-wide text-sky-100 uppercase">
                                  International (Treaties)
                                </span>
                                <span className="block text-[10px] text-stone-400 font-mono">
                                  Nagoya Protocol, WIPO GRATK, TRIPS, CBD
                                </span>
                              </div>
                            </div>
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium uppercase ${
                                cmp.international.confidence?.toLowerCase() === "high"
                                  ? "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                                  : cmp.international.confidence?.toLowerCase() === "medium"
                                  ? "bg-amber-950/60 border border-amber-500/40 text-amber-300"
                                  : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                              }`}
                            >
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${
                                  cmp.international.confidence?.toLowerCase() === "high"
                                    ? "bg-emerald-400"
                                    : cmp.international.confidence?.toLowerCase() === "medium"
                                    ? "bg-amber-400"
                                    : "bg-rose-400"
                                }`}
                              />
                              {cmp.international.confidence} Confidence
                            </span>
                          </div>

                          {/* Answer Content or Abstention */}
                          {cmp.international.abstained ? (
                            <div className="p-4 rounded-xl bg-sky-950/20 border border-sky-400/30 text-sky-200 text-xs sm:text-sm space-y-2">
                              <div className="flex items-center gap-2 font-semibold text-sky-300 uppercase tracking-wider">
                                <AlertTriangle className="w-4 h-4 text-sky-400 shrink-0" />
                                <span>No Relevant Treaty Authority (Abstained)</span>
                              </div>
                              <p className="text-stone-300 leading-relaxed font-light whitespace-pre-line">
                                {cmp.international.answer}
                              </p>
                            </div>
                          ) : (
                            <div className="prose prose-invert prose-sky max-w-none text-xs sm:text-sm leading-relaxed text-[#ede8d5] font-light whitespace-pre-line">
                              {cmp.international.answer}
                            </div>
                          )}
                        </div>

                        {/* Citation Ledger Underneath International Panel */}
                        <div className="mt-6 pt-4 border-t border-sky-500/15">
                          <div className="text-xs font-mono uppercase tracking-wider text-sky-400/90 mb-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Globe2 className="w-3.5 h-3.5 text-sky-400" />
                              <span>International Treaty Authorities ({cmp.international.citations?.length || 0})</span>
                            </div>
                            <span className="text-[10px] text-stone-500 font-mono">Global Conventions</span>
                          </div>

                          {cmp.international.citations && cmp.international.citations.length > 0 ? (
                            <div className="space-y-2">
                              {cmp.international.citations.map((cit, cIdx) => {
                                const pdfUrl = getCitationPdfUrl(cit);
                                return (
                                  <div
                                    key={cIdx}
                                    className="p-3 rounded-xl bg-black/40 border border-sky-500/20 hover:border-sky-400/50 transition-all flex flex-col justify-between"
                                  >
                                    <div className="flex items-center justify-between gap-2 mb-1">
                                      <span className="text-[11px] font-mono text-sky-300 font-bold">
                                        {cit.section}
                                      </span>
                                      <a
                                        href={pdfUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-sky-500/15 border border-sky-400/30 text-[10px] text-sky-300 hover:bg-sky-400 hover:text-black transition-all"
                                      >
                                        <FileText className="w-2.5 h-2.5" />
                                        <span>PDF</span>
                                        <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                                      </a>
                                    </div>
                                    <div className="text-xs text-stone-300 font-normal leading-snug">
                                      {cit.source}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="text-xs text-stone-500 italic">No international treaty citations recorded.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }

              // Assistant Response
              return (
                <div key={msg.id} className="flex justify-start gap-3 items-start pr-4 sm:pr-8">
                  <div className="w-9 h-9 rounded-xl bg-[#12100e] border border-amber-400/40 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(234,179,8,0.15)] mt-1">
                    <Scale className="w-4 h-4 text-[#fefae0]" />
                  </div>

                  <div className="flex-1 max-w-3xl space-y-3">
                    <div
                      className={`glass-panel rounded-2xl p-5 sm:p-6 shadow-2xl ${
                        msg.isError
                          ? "border-red-500/40 bg-red-950/10"
                          : msg.abstained
                          ? "border-amber-500/50 bg-amber-950/15"
                          : "border-amber-500/20"
                      }`}
                    >
                      {/* Top Badges */}
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-500/10 pb-3 mb-4">
                        <div className="flex items-center gap-2">
                          {msg.isStreaming ? (
                            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300 text-xs font-mono tracking-wider">
                              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                              Generating Verified Legal Response...
                            </span>
                          ) : (
                            <>
                              {msg.classification && (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300 text-xs font-medium uppercase tracking-wider">
                                  <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
                                  {msg.classification.replace(/_/g, " ")}
                                </span>
                              )}
                              {msg.classification_citation && (
                                <span className="text-[11px] text-stone-400 font-mono hidden sm:inline">
                                  Basis: {msg.classification_citation}
                                </span>
                              )}
                            </>
                          )}
                        </div>

                        {/* Confidence Badge */}
                        {!msg.isStreaming && msg.confidence && !msg.needs_classification && (
                          <div className="flex items-center gap-2">
                            {msg.language && (
                              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-white/5 border border-amber-500/20 text-stone-300">
                                Lang: {msg.language}
                              </span>
                            )}
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium uppercase ${
                                msg.confidence.toLowerCase() === "high"
                                  ? "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                                  : msg.confidence.toLowerCase() === "medium"
                                  ? "bg-amber-950/60 border border-amber-500/40 text-amber-300"
                                  : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                              }`}
                            >
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${
                                  msg.confidence.toLowerCase() === "high"
                                    ? "bg-emerald-400 shadow-[0_0_8px_#34d399]"
                                    : msg.confidence.toLowerCase() === "medium"
                                    ? "bg-amber-400 shadow-[0_0_8px_#fbbf24]"
                                    : "bg-rose-400 shadow-[0_0_8px_#f43f5e]"
                                }`}
                              />
                              {msg.confidence} Confidence
                            </span>
                          </div>
                        )}
                      </div>

                      {/* CLASSIFICATION QUESTION STEP */}
                      {msg.needs_classification && msg.question && (
                        <div className="space-y-4">
                          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-400/30">
                            <div className="flex items-center gap-2 text-xs font-mono uppercase text-amber-300 tracking-wider mb-1.5">
                              <HelpCircle className="w-4 h-4 text-amber-400" />
                              <span>Regulatory Decision Tree Required</span>
                            </div>
                            <h3 className="text-base sm:text-lg font-medium text-[#f5eedb] leading-snug">
                              {msg.question.question}
                            </h3>
                            {msg.question.help_text && (
                              <p className="mt-2 text-xs text-stone-400 leading-relaxed">
                                {msg.question.help_text}
                              </p>
                            )}
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                            <button
                              onClick={() => handleClassificationSelect(msg.question!.id, true)}
                              disabled={isLoading}
                              className="px-5 py-3.5 rounded-xl bg-[#f5eedb] hover:bg-white text-[#070605] font-semibold text-sm transition-all shadow-[0_0_20px_rgba(245,238,219,0.2)] flex items-center justify-between group disabled:opacity-50"
                            >
                              <span>YES, THIS APPLIES</span>
                              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </button>

                            <button
                              onClick={() => handleClassificationSelect(msg.question!.id, false)}
                              disabled={isLoading}
                              className="px-5 py-3.5 rounded-xl bg-stone-900/90 hover:bg-stone-800 border border-amber-500/30 text-[#ede8d5] font-medium text-sm transition-all flex items-center justify-between group disabled:opacity-50"
                            >
                              <span>NO, DOES NOT APPLY</span>
                              <ArrowRight className="w-4 h-4 text-stone-500 group-hover:translate-x-1 transition-transform" />
                            </button>
                          </div>
                        </div>
                      )}

                      {/* ABSTENTION STATE */}
                      {!msg.needs_classification && msg.abstained && (
                        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-400/40 text-amber-200 mb-4 space-y-3">
                          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-amber-300">
                            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                            <span>No Reliable Statutory Source Found in Corpus</span>
                          </div>
                          <p className="text-sm text-stone-300 leading-relaxed font-light">
                            {msg.content}
                          </p>
                          <div className="pt-2 border-t border-amber-500/20 flex flex-wrap items-center justify-between gap-3">
                            <span className="text-xs text-stone-400">
                              Requires expert human IP interpretation and regulatory drafting.
                            </span>
                            <button
                              onClick={() => setShowFacilitatorModal(true)}
                              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors shadow-md"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>Talk to Human IP Facilitator</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* SUBSTANTIVE ANSWER (Always front and center) */}
                      {!msg.needs_classification && !msg.abstained && (
                        <div>
                          <div className="prose prose-invert prose-amber max-w-none text-sm sm:text-base leading-relaxed text-[#ede8d5] font-light whitespace-pre-line mb-4">
                            {msg.content}
                            {msg.isStreaming && (
                              <span className="inline-block w-2 h-4 ml-1.5 bg-amber-400 animate-pulse rounded-sm align-middle" />
                            )}
                          </div>

                          {/* SIMPLIFIED PLAIN-LANGUAGE RESPONSE (RENDERED DIRECTLY BELOW ORIGINAL ANSWER) */}
                          {msg.showSimplified && msg.simplifiedContent && (
                            <div className="mt-3.5 mb-4 p-4 rounded-xl bg-gradient-to-br from-emerald-950/45 via-stone-900/60 to-emerald-950/30 border border-emerald-500/35 shadow-[0_0_20px_rgba(16,185,129,0.08)] space-y-2.5 animate-in fade-in slide-in-from-top-2 duration-200">
                              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                                <div className="flex items-center gap-2">
                                  <div className="w-5 h-5 rounded-md bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center text-emerald-300 shrink-0">
                                    <Sparkles className="w-3 h-3 text-emerald-400" />
                                  </div>
                                  <span className="text-xs font-mono font-semibold text-emerald-300">
                                    Plain-Language Explanation (Simplified Register)
                                  </span>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => handleToggleSimplify(msg.id)}
                                  title="Hide simplified response"
                                  className="text-stone-400 hover:text-stone-200 p-1 rounded hover:bg-white/5 transition-colors"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                              <p className="text-sm sm:text-base leading-relaxed text-emerald-100/95 font-light whitespace-pre-line">
                                {msg.simplifiedContent}
                              </p>
                              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-stone-400">
                                <span className="text-emerald-400/80">Phrased for non-lawyers &bull; Same legal grounding</span>
                                <span>See statutory citations below &darr;</span>
                              </div>
                            </div>
                          )}

                          {/* REGIONAL TRANSLATION RESPONSE (RENDERED DIRECTLY BELOW ORIGINAL ANSWER) */}
                          {msg.showTranslation && msg.activeTranslationText && (
                            <div className="mt-3.5 mb-4 p-4 rounded-xl bg-gradient-to-br from-amber-950/45 via-stone-900/60 to-amber-950/30 border border-amber-500/35 shadow-[0_0_20px_rgba(245,158,11,0.08)] space-y-2.5 animate-in fade-in slide-in-from-top-2 duration-200">
                              <div className="flex items-center justify-between border-b border-amber-500/20 pb-2">
                                <div className="flex items-center gap-2">
                                  <div className="w-5 h-5 rounded-md bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 shrink-0">
                                    <Languages className="w-3 h-3 text-amber-400" />
                                  </div>
                                  <span className="text-xs font-mono font-semibold text-amber-300">
                                    {TRANSLATE_LANGUAGES.find((l) => l.code === msg.activeLanguage)?.name || "Regional"} Translation
                                    <span className="text-stone-400 font-normal ml-1">
                                      ({TRANSLATE_LANGUAGES.find((l) => l.code === msg.activeLanguage)?.native || msg.activeLanguage})
                                    </span>
                                  </span>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => handleTranslateMessage(msg.id, "en")}
                                  title="Hide translation"
                                  className="text-stone-400 hover:text-stone-200 p-1 rounded hover:bg-white/5 transition-colors"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                              <p className="text-sm sm:text-base leading-relaxed text-amber-100/95 font-light whitespace-pre-line">
                                {msg.activeTranslationText}
                              </p>
                              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-stone-400">
                                <span className="text-amber-400/80">Statutory citations strictly preserved in English</span>
                                <span>See statutory citations below &darr;</span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* DEDICATED ABS COMPLIANCE HELPER PANEL (PROMPT 1) */}
                      {msg.abs_compliance && msg.abs_compliance.triggered && (
                        <div className="mb-6 rounded-2xl bg-gradient-to-b from-[#08130e]/95 via-[#0b1712]/90 to-[#070e0a]/95 border border-emerald-500/40 p-5 sm:p-6 shadow-[0_0_35px_rgba(16,185,129,0.14)] space-y-5">
                          {/* Panel Header */}
                          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-500/20 pb-3.5">
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-400/50 flex items-center justify-center text-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.3)] shrink-0">
                                <Leaf className="w-4 h-4 text-emerald-400" />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-semibold tracking-wide text-emerald-200">
                                    ABS Compliance Helper
                                  </span>
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-emerald-500/15 border border-emerald-400/30 text-emerald-300">
                                    Structured Flow
                                  </span>
                                </div>
                                <span className="text-[11px] text-stone-400 font-mono">
                                  Biological Diversity Act, 2002 (as amended 2023) · BD Rules 2024
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span
                                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium ${
                                  msg.abs_compliance.status === "completed"
                                    ? "bg-emerald-950/80 border border-emerald-400/50 text-emerald-300"
                                    : "bg-amber-950/80 border border-amber-400/50 text-amber-300 animate-pulse"
                                }`}
                              >
                                <span
                                  className={`w-2 h-2 rounded-full ${
                                    msg.abs_compliance.status === "completed" ? "bg-emerald-400" : "bg-amber-400"
                                  }`}
                                />
                                {msg.abs_compliance.status === "completed" ? "Evaluation Complete" : "Action Required"}
                              </span>
                            </div>
                          </div>

                          {/* Decision Questions Stepper & Interactive Selectors */}
                          <div className="space-y-3">
                            <div className="text-[11px] uppercase tracking-wider font-mono text-emerald-400/80 flex items-center gap-1.5">
                              <Sprout className="w-3.5 h-3.5 text-emerald-400" />
                              <span>Statutory Decision Flow (Click to Test Scenarios):</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              {/* Q1: Sourced in India */}
                              <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/20 space-y-2">
                                <div className="text-[10px] font-mono text-stone-400 uppercase">1. Resource Origin</div>
                                <div className="text-xs font-medium text-stone-200 leading-snug">
                                  Sourced in India?
                                </div>
                                <div className="flex gap-1.5 pt-1">
                                  <button
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, "is_sourced_from_india", true)}
                                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all ${
                                      msg.abs_compliance.answers?.is_sourced_from_india === true
                                        ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                                        : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                                    }`}
                                  >
                                    India (Domestic)
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, "is_sourced_from_india", false)}
                                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all ${
                                      msg.abs_compliance.answers?.is_sourced_from_india === false
                                        ? "bg-rose-500 text-white font-semibold shadow-[0_0_10px_rgba(244,63,94,0.4)]"
                                        : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                                    }`}
                                  >
                                    Outside India
                                  </button>
                                </div>
                              </div>

                              {/* Q2: Purpose */}
                              <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/20 space-y-2">
                                <div className="text-[10px] font-mono text-stone-400 uppercase">2. Utilization Purpose</div>
                                <div className="text-xs font-medium text-stone-200 leading-snug">
                                  Commercial vs Research?
                                </div>
                                <div className="flex gap-1.5 pt-1">
                                  <button
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, "is_commercial_use", true)}
                                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all ${
                                      msg.abs_compliance.answers?.is_commercial_use === true
                                        ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                                        : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                                    }`}
                                  >
                                    Commercial / Export
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, "is_commercial_use", false)}
                                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all ${
                                      msg.abs_compliance.answers?.is_commercial_use === false
                                        ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                                        : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                                    }`}
                                  >
                                    Research Only
                                  </button>
                                </div>
                              </div>

                              {/* Q3: Entity Type */}
                              <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/20 space-y-2">
                                <div className="text-[10px] font-mono text-stone-400 uppercase">3. Applicant Entity</div>
                                <div className="text-xs font-medium text-stone-200 leading-snug">
                                  Domestic vs Foreign Entity?
                                </div>
                                <div className="flex gap-1.5 pt-1">
                                  <button
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, "is_foreign_entity", false)}
                                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all ${
                                      msg.abs_compliance.answers?.is_foreign_entity === false
                                        ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                                        : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                                    }`}
                                  >
                                    Indian Entity
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, "is_foreign_entity", true)}
                                    className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all ${
                                      msg.abs_compliance.answers?.is_foreign_entity === true
                                        ? "bg-amber-500 text-black font-semibold shadow-[0_0_10px_rgba(245,158,11,0.4)]"
                                        : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                                    }`}
                                  >
                                    Foreign / NRI (S. 3(2))
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Pending Question Callout if Needs Input */}
                          {msg.abs_compliance.status === "needs_input" && msg.abs_compliance.next_question && (
                            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-400/40 space-y-2">
                              <div className="flex items-center gap-2 text-xs font-mono uppercase text-amber-300">
                                <HelpCircle className="w-4 h-4 text-amber-400 shrink-0" />
                                <span>Pending Compliance Clarification:</span>
                              </div>
                              <p className="text-sm font-medium text-[#f5eedb] leading-snug">
                                {msg.abs_compliance.next_question.question}
                              </p>
                              {msg.abs_compliance.next_question.help_text && (
                                <p className="text-xs text-stone-400 leading-relaxed">
                                  {msg.abs_compliance.next_question.help_text}
                                </p>
                              )}
                              <div className="flex flex-wrap gap-2.5 pt-1.5">
                                {msg.abs_compliance.next_question.options.map((opt, idx) => (
                                  <button
                                    key={idx}
                                    type="button"
                                    onClick={() => handleABSOptionSelect(msg.id, msg.abs_compliance!.next_question!.id, opt.value)}
                                    className="px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-300 text-black font-semibold text-xs transition-colors shadow-md flex items-center gap-2"
                                  >
                                    <span>{opt.label}</span>
                                    <ArrowRight className="w-3.5 h-3.5" />
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Structured Results Card */}
                          {msg.abs_compliance.result && (
                            <div className="p-4 sm:p-5 rounded-xl bg-black/50 border border-emerald-500/30 space-y-4">
                              {/* Dual Approval Status Verdict Badges */}
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {/* NBA Approval Verdict */}
                                <div
                                  className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 ${
                                    msg.abs_compliance.result.requires_nba_approval
                                      ? "bg-rose-950/40 border-rose-500/40 text-rose-200"
                                      : "bg-emerald-950/30 border-emerald-500/30 text-emerald-200"
                                  }`}
                                >
                                  <div>
                                    <div className="text-[10px] font-mono uppercase tracking-wider text-stone-400">
                                      National Biodiversity Authority (NBA)
                                    </div>
                                    <div className="text-sm font-semibold mt-0.5">
                                      {msg.abs_compliance.result.requires_nba_approval ? "Prior Approval Required" : "No NBA Approval Required"}
                                    </div>
                                  </div>
                                  {msg.abs_compliance.result.requires_nba_approval ? (
                                    <span className="px-2.5 py-1 rounded-md bg-rose-500/20 border border-rose-400/40 text-rose-300 text-xs font-mono font-bold">
                                      MANDATORY
                                    </span>
                                  ) : (
                                    <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs font-mono font-bold">
                                      EXEMPT
                                    </span>
                                  )}
                                </div>

                                {/* SBB Intimation Verdict */}
                                <div
                                  className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 ${
                                    msg.abs_compliance.result.requires_sbb_intimation
                                      ? "bg-amber-950/40 border-amber-500/40 text-amber-200"
                                      : "bg-stone-900/40 border-white/10 text-stone-400"
                                  }`}
                                >
                                  <div>
                                    <div className="text-[10px] font-mono uppercase tracking-wider text-stone-400">
                                      State Biodiversity Board (SBB)
                                    </div>
                                    <div className="text-sm font-semibold mt-0.5">
                                      {msg.abs_compliance.result.requires_sbb_intimation
                                        ? `Prior Intimation Required (${msg.abs_compliance.result.sbb_state ? msg.abs_compliance.result.sbb_state + " KSBB" : "State SBB"})`
                                        : "No SBB Intimation Required"}
                                    </div>
                                  </div>
                                  {msg.abs_compliance.result.requires_sbb_intimation ? (
                                    <span className="px-2.5 py-1 rounded-md bg-amber-500/20 border border-amber-400/40 text-amber-300 text-xs font-mono font-bold">
                                      MANDATORY
                                    </span>
                                  ) : (
                                    <span className="px-2.5 py-1 rounded-md bg-stone-800 border border-stone-700 text-stone-400 text-xs font-mono font-bold">
                                      N/A
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Applicable Statutory Provision */}
                              <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-500/25 space-y-1.5">
                                <div className="flex items-center gap-2 text-xs font-mono text-emerald-300 font-semibold">
                                  <Scale className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                  <span>Applicable Provision: {msg.abs_compliance.result.applicable_provision}</span>
                                </div>
                                {msg.abs_compliance.result.exact_statutory_text && (
                                  <p className="text-xs text-stone-300 leading-relaxed font-light italic">
                                    &ldquo;{msg.abs_compliance.result.exact_statutory_text}&rdquo;
                                  </p>
                                )}
                              </div>

                              {/* Next Steps Checklist */}
                              {msg.abs_compliance.result.next_steps?.length > 0 && (
                                <div className="space-y-2">
                                  <div className="text-xs font-mono uppercase tracking-wider text-stone-400 flex items-center gap-1.5">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                                    <span>Prescribed Regulatory Next Steps:</span>
                                  </div>
                                  <div className="space-y-2">
                                    {msg.abs_compliance.result.next_steps.map((step, sIdx) => (
                                      <div key={sIdx} className="flex items-start gap-2.5 text-xs text-stone-300 leading-relaxed">
                                        <span className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 flex items-center justify-center shrink-0 font-mono text-[10px] font-bold mt-0.5">
                                          {sIdx + 1}
                                        </span>
                                        <span>{step}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Relevant Statutory Forms */}
                              {msg.abs_compliance.result.relevant_forms?.length > 0 && (
                                <div className="pt-2 border-t border-white/5 flex flex-wrap items-center gap-2">
                                  <span className="text-[11px] font-mono text-stone-400">Relevant Statutory Forms:</span>
                                  {msg.abs_compliance.result.relevant_forms.map((form, fIdx) => (
                                    <span
                                      key={fIdx}
                                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-400/30 text-emerald-300 text-xs font-mono"
                                    >
                                      <FileText className="w-3 h-3 text-emerald-400" />
                                      <span>{form}</span>
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* CONDITIONAL INLINE TKDL PRIOR-ART NOTE */}
                      {msg.tkdl_pointer && msg.tkdl_pointer.triggered && (
                        <div className="mt-4 p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs text-stone-300 flex items-start gap-2.5 shadow-sm">
                          <BookOpen className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                          <div className="space-y-1 leading-relaxed">
                            <div>
                              <span className="font-semibold text-indigo-300">Prior-Art Clearance (TKDL): </span>
                              <span>
                                Classical formulations belong to the public domain under Section 3(p) of the Patents Act, 1970 and are catalogued in the Traditional Knowledge Digital Library (
                              </span>
                              <a
                                href="https://www.tkdl.res.in"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-0.5 text-indigo-300 hover:text-indigo-100 underline font-mono text-[11px]"
                              >
                                <span>tkdl.res.in</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                              <span>).</span>
                            </div>
                            <p className="text-[11px] text-stone-400 font-light">
                              TKDL is accessed directly by patent examiners during examination rather than via open public search.
                            </p>
                          </div>
                        </div>
                      )}

                      {/* HISTORICAL BIOPIRACY PRECEDENTS CARD (TURMERIC & NEEM) - PROMPT 1 */}
                      {((msg.case_study && msg.case_study.triggered) ||
                        (msg.tkdl_pointer?.case_study && msg.tkdl_pointer.case_study.triggered)) && (
                        (() => {
                          const cs = msg.case_study || msg.tkdl_pointer?.case_study;
                          if (!cs) return null;
                          return (
                            <div className="mt-4 rounded-2xl bg-gradient-to-b from-[#14100b]/95 via-[#19130d]/90 to-[#0f0c08]/95 border border-amber-600/35 p-4 sm:p-5 shadow-[0_0_30px_rgba(217,119,6,0.12)] space-y-4">
                              {/* Header */}
                              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-500/20 pb-3">
                                <div className="flex items-center gap-2.5">
                                  <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.25)] shrink-0">
                                    <History className="w-4 h-4 text-amber-400" />
                                  </div>
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs sm:text-sm font-semibold tracking-wide text-amber-200">
                                        Historical Landmark Precedents: Turmeric &amp; Neem Revocations
                                      </span>
                                      <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[9px] font-mono uppercase bg-amber-500/15 border border-amber-400/30 text-amber-300">
                                        Case Law
                                      </span>
                                    </div>
                                    <p className="text-[11px] text-stone-400 font-light">
                                      Real-world patent office precedents establishing Section 3(p) &amp; TKDL
                                    </p>
                                  </div>
                                </div>
                                <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-stone-900/80 border border-white/10 text-stone-400">
                                  USPTO &amp; EPO Revocation Records
                                </span>
                              </div>

                              {/* Two Landmark Case Cards Side-by-Side */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {/* Turmeric Case */}
                                <div className="p-3.5 rounded-xl bg-black/45 border border-amber-500/25 space-y-2 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-center justify-between gap-2 mb-1.5">
                                      <span className="text-xs font-mono font-bold text-amber-300 tracking-wide">
                                        TURMERIC CASE
                                      </span>
                                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 font-semibold">
                                        Revoked 1997
                                      </span>
                                    </div>
                                    <div className="text-[11px] font-mono text-stone-400 mb-2 flex items-center justify-between">
                                      <span>USPTO &bull; US Patent 5,401,504</span>
                                      <span className="text-stone-400 text-[10px]">Granted 1995</span>
                                    </div>
                                    <p className="text-xs text-stone-300 leading-relaxed font-light">
                                      In 1995, the US Patent and Trademark Office granted US Patent 5,401,504 to the University of Mississippi Medical Center for turmeric powder&apos;s wound-healing use. India&apos;s CSIR filed a re-examination request in 1996 with 32 prior-art references from traditional and scientific literature, and the USPTO revoked the patent in 1997 after finding the use was already known traditional knowledge, not a novel invention.
                                    </p>
                                  </div>
                                </div>

                                {/* Neem Case */}
                                <div className="p-3.5 rounded-xl bg-black/45 border border-amber-500/25 space-y-2 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-center justify-between gap-2 mb-1.5">
                                      <span className="text-xs font-mono font-bold text-amber-300 tracking-wide">
                                        NEEM CASE
                                      </span>
                                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 font-semibold">
                                        Revoked 2000 (Appeal 2005)
                                      </span>
                                    </div>
                                    <div className="text-[11px] font-mono text-stone-400 mb-2 flex items-center justify-between">
                                      <span>EPO &bull; EP 436257</span>
                                      <span className="text-stone-400 text-[10px]">Granted 1994</span>
                                    </div>
                                    <p className="text-xs text-stone-300 leading-relaxed font-light">
                                      In 1994, the European Patent Office granted a patent (EP 436257) to the US Department of Agriculture and W.R. Grace for a neem-based fungicide. Following opposition on grounds that neem&apos;s antifungal use was centuries-old Indian traditional knowledge, the EPO revoked the patent in 2000, a decision upheld on final appeal in 2005 &mdash; the world&apos;s first patent revoked specifically on biopiracy grounds.
                                    </p>
                                  </div>
                                </div>
                              </div>

                              {/* Closing Statutory Takeaway Banner */}
                              <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-400/25 text-xs text-amber-200/95 leading-relaxed font-light">
                                <span className="font-semibold text-amber-300">Statutory Significance: </span>
                                These cases are part of why Section 3(p) of the Patents Act, 1970 excludes traditional knowledge from patentability, and why the Traditional Knowledge Digital Library (TKDL) exists &mdash; to document India&apos;s traditional knowledge so it can be used as prior art before a wrongful patent is even granted, rather than fought after the fact.
                              </div>

                              {/* Footnote Citation */}
                              <div className="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-stone-400">
                                <span>
                                  Sources: WIPO Traditional Knowledge Case Studies (WIPO/GRTKF); USPTO Reexamination Certificate B1 5,401,504; EPO Opposition Decision EP 0436257 B1.
                                </span>
                                <span className="text-stone-400">Public historical patent office records</span>
                              </div>
                            </div>
                          );
                        })()
                      )}

                      {/* STATUTORY CITATION CARDS */}
                      {!msg.needs_classification && msg.citations && msg.citations.length > 0 && (
                        <div className="mt-5 pt-4 border-t border-amber-500/15">
                          <div className="text-xs font-mono uppercase tracking-wider text-amber-400/90 mb-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <FileCheck className="w-3.5 h-3.5 text-amber-400" />
                              <span>Verified Statutory & Treaty Authorities</span>
                            </div>
                            <span className="text-[10px] text-amber-400/70 font-mono hidden sm:inline">
                              Click card to open legal PDF
                            </span>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                            {msg.citations.map((cit, idx) => {
                              const pdfUrl = getCitationPdfUrl(cit);
                              const officialUrl = cit.official_url;

                              return (
                                <div
                                  key={idx}
                                  className="group relative p-3.5 rounded-xl bg-black/40 hover:bg-amber-950/25 border border-amber-500/25 hover:border-amber-400/70 transition-all duration-200 shadow-sm text-left flex flex-col justify-between"
                                >
                                  {/* Primary link that opens the official legal PDF directly */}
                                  <a
                                    href={pdfUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="block cursor-pointer focus:outline-none"
                                    title={`Open verified statutory PDF: ${cit.source}`}
                                  >
                                    <div className="flex items-center justify-between gap-2 mb-1.5">
                                      <span className="text-[11px] font-mono text-amber-300 font-bold tracking-wide group-hover:text-amber-200 transition-colors">
                                        {cit.section}
                                      </span>
                                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-[10px] text-amber-300 font-mono group-hover:bg-amber-400 group-hover:text-black transition-all">
                                        <FileText className="w-3 h-3" />
                                        <span>Open PDF</span>
                                        <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                                      </span>
                                    </div>
                                    <div className="text-xs text-stone-200 font-normal group-hover:text-white transition-colors leading-snug">
                                      {cit.source}
                                    </div>
                                  </a>

                                  {/* Bottom metadata with Primary Source indicator & optional official portal link */}
                                  <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[9px] font-mono text-stone-400">
                                    <span className="text-amber-500/70 flex items-center gap-1">
                                      <span>Primary PDF Record</span>
                                    </span>
                                    {officialUrl && (
                                      <a
                                        href={officialUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="hover:text-amber-300 hover:underline transition-colors flex items-center gap-1 text-stone-300"
                                        title={`Visit official registry website: ${officialUrl}`}
                                      >
                                        <span>Web Portal</span>
                                        <ExternalLink className="w-2.5 h-2.5" />
                                      </a>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Footer Metadata & Language Action */}
                      {!msg.isStreaming && (
                        <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[10px] text-stone-400 font-mono">
                          <div className="flex items-center gap-3">
                            <span>
                              {msg.provider_used && `Provider: ${msg.provider_used.toUpperCase()}`}
                            </span>
                            <span>{msg.timestamp}</span>

                            {/* Lightweight Feedback Signal (Prompt 3) */}
                            {!msg.needs_classification && !msg.isError && msg.role === "assistant" && (
                              <div className="flex items-center gap-1.5 ml-1 border-l border-white/10 pl-3">
                                {feedbackState[msg.id]?.submitted ? (
                                  <span className="inline-flex items-center gap-1 text-[11px] text-amber-300/90 font-sans font-medium">
                                    <CheckCircle2 className="w-3 h-3 text-amber-400" />
                                    <span>{feedbackState[msg.id]?.rating === "up" ? "Helpful" : "Feedback recorded"}</span>
                                  </span>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    <button
                                      type="button"
                                      onClick={() => handleFeedback(msg.id, "up", undefined, msg.content, msg.citations)}
                                      title="Helpful statutory response"
                                      className={`p-1.5 rounded-lg border transition-all ${
                                        feedbackState[msg.id]?.rating === "up"
                                          ? "bg-amber-500/20 border-amber-400 text-amber-300"
                                          : "border-white/10 hover:border-amber-400/40 hover:bg-amber-500/10 text-stone-400 hover:text-amber-300"
                                      }`}
                                    >
                                      <ThumbsUp className="w-3 h-3" />
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleFeedback(msg.id, "down", undefined, msg.content, msg.citations)}
                                      title="Report issue or improvement"
                                      className={`p-1.5 rounded-lg border transition-all ${
                                        feedbackState[msg.id]?.rating === "down"
                                          ? "bg-rose-500/20 border-rose-400 text-rose-300"
                                          : "border-white/10 hover:border-rose-400/40 hover:bg-rose-500/10 text-stone-400 hover:text-rose-300"
                                      }`}
                                    >
                                      <ThumbsDown className="w-3 h-3" />
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          {!msg.needs_classification && !msg.isError && msg.role === "assistant" && (
                            <div className="relative flex items-center gap-2">
                              {/* Explain-Simply / Plain Language Register Toggle */}
                              {msg.isSimplifying ? (
                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 text-[11px] font-sans font-medium animate-pulse">
                                  <Loader2 className="w-3 h-3 animate-spin text-emerald-400" />
                                  <span>Simplifying...</span>
                                </div>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => handleToggleSimplify(msg.id)}
                                  title={
                                    msg.showSimplified
                                      ? "Hide plain language explanation"
                                      : "Show plain-language explanation below"
                                  }
                                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-sans font-medium transition-all ${
                                    msg.showSimplified
                                      ? "bg-emerald-500/20 border-emerald-400/60 text-emerald-200 shadow-[0_0_10px_rgba(16,185,129,0.2)]"
                                      : "bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-400/30 text-emerald-300"
                                  }`}
                                >
                                  <Sparkles className={`w-3.5 h-3.5 ${msg.showSimplified ? "text-emerald-400" : "text-emerald-400/80"}`} />
                                  <span>{msg.showSimplified ? "Hide Simplified" : "Simplify"}</span>
                                </button>
                              )}

                              {/* If currently translating this message, show local loading spinner */}
                              {msg.isTranslating ? (
                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-400/30 text-amber-300 text-[11px] font-sans font-medium animate-pulse">
                                  <Loader2 className="w-3 h-3 animate-spin text-amber-400" />
                                  <span>Translating answer...</span>
                                </div>
                              ) : (
                                <>
                                  {/* Quick toggle to English / hide translation */}
                                  {msg.showTranslation && msg.activeLanguage && msg.activeLanguage !== "en" && (
                                    <button
                                      type="button"
                                      onClick={() => handleTranslateMessage(msg.id, "en")}
                                      title="Hide translation"
                                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-stone-800/80 hover:bg-stone-700/80 border border-stone-600/40 text-stone-300 hover:text-white text-[10px] font-sans font-medium transition-colors"
                                    >
                                      <X className="w-2.5 h-2.5 text-stone-400" />
                                      <span>Hide {TRANSLATE_LANGUAGES.find((l) => l.code === msg.activeLanguage)?.name || "Translation"}</span>
                                    </button>
                                  )}

                                  {/* Compact Translate trigger button */}
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setOpenTranslateMsgId(
                                        openTranslateMsgId === msg.id ? null : msg.id
                                      )
                                    }
                                    title="Translate answer into Indian regional language"
                                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-sans font-medium transition-all ${
                                      msg.showTranslation && msg.activeLanguage && msg.activeLanguage !== "en"
                                        ? "bg-amber-500/20 border-amber-400/60 text-amber-200 shadow-[0_0_10px_rgba(245,158,11,0.2)]"
                                        : "bg-amber-500/10 hover:bg-amber-500/20 border-amber-400/30 text-amber-300"
                                    }`}
                                  >
                                    <Languages className="w-3.5 h-3.5 text-amber-400" />
                                    <span>
                                      {msg.showTranslation && msg.activeLanguage && msg.activeLanguage !== "en"
                                        ? TRANSLATE_LANGUAGES.find((l) => l.code === msg.activeLanguage)?.name || "Translated"
                                        : "Translate"}
                                    </span>
                                    <ChevronDown className={`w-3 h-3 text-amber-400 transition-transform ${openTranslateMsgId === msg.id ? "rotate-180" : ""}`} />
                                  </button>

                                  {/* Compact Language Picker Dropdown */}
                                  {openTranslateMsgId === msg.id && (
                                    <div
                                      className="absolute right-0 bottom-full mb-2 z-50 w-52 rounded-xl bg-[#14120e] border border-amber-500/30 shadow-2xl p-1.5 backdrop-blur-xl animate-in fade-in zoom-in-95 duration-150"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <div className="px-2.5 py-1.5 border-b border-white/5 text-[10px] font-mono uppercase tracking-wider text-stone-400 flex items-center justify-between">
                                        <span>Select Language</span>
                                        <span className="text-[9px] text-amber-400/80">Citations in English</span>
                                      </div>
                                      <div className="py-1 space-y-0.5">
                                        {TRANSLATE_LANGUAGES.map((lang) => {
                                          const isCurrent = (msg.activeLanguage || "en") === lang.code;
                                          const isCached = !!msg.translations?.[lang.code];
                                          return (
                                            <button
                                              key={lang.code}
                                              type="button"
                                              onClick={() => handleTranslateMessage(msg.id, lang.code)}
                                              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left text-xs transition-colors ${
                                                isCurrent
                                                  ? "bg-amber-500/20 text-amber-200 font-semibold"
                                                  : "text-stone-300 hover:bg-white/5 hover:text-white"
                                              }`}
                                            >
                                              <div className="flex items-center gap-2">
                                                <span className="font-sans font-medium">{lang.name}</span>
                                                <span className="text-[11px] text-stone-400">({lang.native})</span>
                                              </div>
                                              <div className="flex items-center gap-1 text-[10px] text-stone-400 font-mono">
                                                {isCurrent && <Check className="w-3 h-3 text-amber-400" />}
                                                {!isCurrent && isCached && (
                                                  <span className="text-[9px] px-1 rounded bg-stone-800 text-stone-300">cached</span>
                                                )}
                                              </div>
                                            </button>
                                          );
                                        })}
                                      </div>
                                    </div>
                                  )}
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Optional Thumbs-Down Reason / Comment Input Drawer */}
                      {!msg.needs_classification && !msg.isError && msg.role === "assistant" && feedbackState[msg.id]?.showCommentInput && (
                        <div className="mt-3 p-3 rounded-xl bg-black/60 border border-amber-500/30 text-xs space-y-2.5">
                          <div className="flex items-center justify-between text-stone-200 font-sans font-medium">
                            <span>What could be improved? <span className="text-stone-400 text-[10px] font-normal">(optional)</span></span>
                            <button
                              type="button"
                              onClick={() => setFeedbackState((prev) => ({
                                ...prev,
                                [msg.id]: { ...prev[msg.id], showCommentInput: false, submitted: true }
                              }))}
                              className="text-stone-400 hover:text-stone-200 text-[11px]"
                            >
                              Dismiss
                            </button>
                          </div>

                          {/* Quick-select reason tags */}
                          <div className="flex flex-wrap gap-1.5">
                            {[
                              "Wrong jurisdiction",
                              "Missing citation",
                              "Confusing answer",
                              "Outdated statute reference",
                            ].map((tag) => (
                              <button
                                key={tag}
                                type="button"
                                onClick={() => handleFeedback(msg.id, "down", tag, msg.content, msg.citations)}
                                className="px-2.5 py-1 rounded-lg bg-stone-900 hover:bg-amber-950/60 border border-stone-700 hover:border-amber-400/50 text-stone-300 hover:text-amber-200 text-[11px] font-sans transition-all"
                              >
                                {tag}
                              </button>
                            ))}
                          </div>

                          {/* Free-text comment input */}
                          <div className="flex gap-2">
                            <input
                              type="text"
                              placeholder="Specific feedback note..."
                              value={feedbackState[msg.id]?.comment || ""}
                              onChange={(e) => setFeedbackState((prev) => ({
                                ...prev,
                                [msg.id]: { ...prev[msg.id], comment: e.target.value }
                              }))}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  handleFeedback(msg.id, "down", feedbackState[msg.id]?.comment, msg.content, msg.citations);
                                }
                              }}
                              className="flex-1 px-3 py-1.5 rounded-lg bg-stone-900 border border-white/10 focus:border-amber-400/60 outline-none text-stone-200 text-xs placeholder-stone-500"
                            />
                            <button
                              type="button"
                              onClick={() => handleFeedback(msg.id, "down", feedbackState[msg.id]?.comment, msg.content, msg.citations)}
                              className="px-3 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-black font-semibold text-xs transition-colors"
                            >
                              Submit
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* REAL-TIME BACKEND SSE STAGE PROGRESS INDICATOR */}
            {isLoading && !messages.some((m) => m.isStreaming) && (
              <div className="flex justify-start gap-3 items-start pr-8 animate-in fade-in duration-300">
                <div className="w-9 h-9 rounded-xl bg-[#12100e] border border-amber-400/40 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(234,179,8,0.2)]">
                  <Loader2 className="w-4 h-4 text-amber-300 animate-spin" />
                </div>
                <div className="glass-panel p-4 rounded-2xl border-amber-500/30 max-w-md">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    <span className="text-xs font-mono uppercase tracking-wider text-amber-300">
                      Live Pipeline Execution
                    </span>
                  </div>
                  <p className="text-xs text-stone-300 mt-2 font-light">{loadingStep}</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* FLOATING FIXED BOTTOM QUERY BAR (Only active during ongoing inquiry) */}
      {messages.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-30 p-4 sm:p-6 bg-gradient-to-t from-[#050403] via-[#050403]/95 to-transparent backdrop-blur-md">
          <div className="max-w-4xl mx-auto">
            <form
              onSubmit={handleUserSubmit}
              className="relative flex items-center glass-panel rounded-2xl p-2 sm:p-2.5 border-amber-500/30 focus-within:border-amber-400/80 focus-within:shadow-[0_0_30px_rgba(234,179,8,0.2)] transition-all shadow-2xl"
            >
              <div className="pl-3 pr-2 text-stone-400">
                <Bot className="w-5 h-5 text-amber-400" />
              </div>

              <input
                ref={inputRef}
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  isCompareMode
                    ? "Compare National (India) vs International (Treaties) side-by-side..."
                    : `Ask any Ayurvedic regulatory or patent question (${
                        jurisdiction === "national" ? "India" : "International"
                      })...`
                }
                disabled={isLoading}
                className="flex-1 bg-transparent border-0 outline-none text-sm sm:text-base text-[#f5eedb] placeholder-stone-400 px-2 py-1.5 focus:ring-0"
              />

              <button
                type="submit"
                disabled={!inputQuery.trim() || isLoading}
                className={`px-4 sm:px-6 py-2.5 rounded-xl font-semibold text-xs sm:text-sm transition-all shadow-md flex items-center gap-2 shrink-0 disabled:opacity-40 cursor-pointer ${
                  isCompareMode
                    ? "bg-gradient-to-r from-amber-400 to-amber-500 text-stone-950 hover:brightness-110 shadow-[0_0_20px_rgba(251,191,36,0.35)]"
                    : "bg-amber-400 hover:bg-amber-300 text-stone-950 font-bold shadow-[0_0_20px_rgba(251,191,36,0.25)]"
                }`}
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-black" />
                ) : (
                  <>
                    <span>{isCompareMode ? "COMPARE BOTH" : "ASK SAHAYAK"}</span>
                    {isCompareMode ? (
                      <Columns2 className="w-3.5 h-3.5 text-black" />
                    ) : (
                      <Send className="w-3.5 h-3.5 text-black" />
                    )}
                  </>
                )}
              </button>
            </form>

            <div className="mt-2 text-center flex items-center justify-center gap-4 text-[11px] text-stone-400 font-mono">
              <button
                onClick={() => setShowCorpusModal(true)}
                className="text-amber-400/90 hover:text-amber-300 transition-colors flex items-center gap-1"
              >
                <Database className="w-3 h-3" />
                <span>Corpus Provenance (17 Source Acts)</span>
              </button>
              <span>•</span>
              <span className="text-stone-300">Multilingual AI Translation with English citation anchors</span>
              <span>•</span>
              <span className="text-amber-400/90">Informational guidance under Indian law</span>
            </div>
          </div>
        </div>
      )}

      {/* CORPUS PROVENANCE DRAWER / MODAL (Item 4) */}
      {showCorpusModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-lg">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl max-w-4xl w-full max-h-[85vh] overflow-y-auto border-amber-500/40 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center">
                  <Database className="w-5 h-5 text-amber-300" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-[#f5eedb]">CORPUS PROVENANCE & AUTHORITIES</h2>
                  <p className="text-xs text-stone-400">
                    Dynamically retrieved from verified legal manifest (17 statutory sources)
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowCorpusModal(false)}
                className="p-2 rounded-xl text-stone-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* National Statutes Group */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-4 h-4 text-amber-400" />
                <h3 className="font-display text-lg text-amber-300">
                  NATIONAL JURISDICTION (INDIA) — {corpusData?.national_count || 12} SOURCES
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {corpusData?.national.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-3.5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-400/40 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-semibold text-[#f5eedb] leading-snug">
                        {doc.title}
                      </h4>
                      <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/30 text-amber-300 shrink-0">
                        {doc.document_type}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-stone-400 font-mono">
                      <span>Authority: <strong className="text-stone-300 font-normal">{doc.authority}</strong></span>
                      <span>Year: {doc.year}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-amber-400/80 font-mono mt-1.5">
                      <span>Prefix: {doc.citation_prefix}</span>
                      <div className="flex items-center gap-3">
                        <a
                          href={doc.pdf_url || `${API_BASE_URL}/pdf/${encodeURIComponent(doc.pdf_filename || doc.title)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-amber-300 hover:text-white font-medium underline underline-offset-2"
                        >
                          <FileText className="w-2.5 h-2.5" />
                          <span>Open PDF</span>
                        </a>
                        {doc.official_url && (
                          <a
                            href={doc.official_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-stone-400 hover:text-amber-200 underline underline-offset-2"
                          >
                            <span>Registry</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* International Treaties Group */}
            <div className="pt-4 border-t border-amber-500/15">
              <div className="flex items-center gap-2 mb-3">
                <Globe2 className="w-4 h-4 text-amber-400" />
                <h3 className="font-display text-lg text-amber-300">
                  INTERNATIONAL JURISDICTION (TREATIES & CONVENTIONS) — {corpusData?.international_count || 5} SOURCES
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {corpusData?.international.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-3.5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-400/40 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-semibold text-[#f5eedb] leading-snug">
                        {doc.title}
                      </h4>
                      <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/30 text-amber-300 shrink-0">
                        {doc.document_type}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-stone-400 font-mono">
                      <span>Authority: <strong className="text-stone-300 font-normal">{doc.authority}</strong></span>
                      <span>Year: {doc.year}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-amber-400/80 font-mono mt-1.5">
                      <span>Prefix: {doc.citation_prefix}</span>
                      <div className="flex items-center gap-3">
                        <a
                          href={doc.pdf_url || `${API_BASE_URL}/pdf/${encodeURIComponent(doc.pdf_filename || doc.title)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-amber-300 hover:text-white font-medium underline underline-offset-2"
                        >
                          <FileText className="w-2.5 h-2.5" />
                          <span>Open PDF</span>
                        </a>
                        {doc.official_url && (
                          <a
                            href={doc.official_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-stone-400 hover:text-amber-200 underline underline-offset-2"
                          >
                            <span>Registry</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-3">
              <button
                onClick={() => setShowCorpusModal(false)}
                className="px-5 py-2.5 rounded-xl bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors shadow-md"
              >
                Close Provenance View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HUMAN FACILITATOR MODAL */}
      {showFacilitatorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel p-6 rounded-3xl max-w-lg w-full border-amber-500/40 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-amber-500/20 pb-3">
              <div className="flex items-center gap-2">
                <Scale className="w-5 h-5 text-amber-400" />
                <h3 className="font-display text-xl text-[#f5eedb]">HUMAN IP FACILITATOR</h3>
              </div>
              <button
                onClick={() => setShowFacilitatorModal(false)}
                className="text-stone-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-sm text-stone-300 leading-relaxed font-light">
              Since the automated statutory corpus did not contain high-confidence provisions for this inquiry, you can connect directly with registered Ayush patent attorneys and regulatory facilitators.
            </p>

            <div className="space-y-2 text-xs font-mono text-stone-400 bg-black/40 p-4 rounded-xl border border-amber-500/20">
              <div>Facilitation Desk: AYUSH IP Facilitation Cell (AIPFC)</div>
              <div>Email: ip-facilitator@ayush-sahayak.gov.in</div>
              <div>Emergency Clearance: Form 25D / Rule 158B Expedited</div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowFacilitatorModal(false)}
                className="px-4 py-2 rounded-xl bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors"
              >
                Close & Return to Assistant
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONVERSATION SESSIONS & AUDIT LOGS MODAL */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-lg">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl max-w-2xl w-full max-h-[80vh] overflow-y-auto border-amber-500/40 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center">
                  <History className="w-5 h-5 text-amber-300" />
                </div>
                <div>
                  <h2 className="font-display text-2xl text-[#f5eedb]">INQUIRY SESSIONS & AUDIT LOGS</h2>
                  <p className="text-xs text-stone-400">
                    Persistent conversations stored in local SQLite database
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="p-2 rounded-xl text-stone-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scoped Session Tabs (Accuracy Fix #3) */}
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-1.5 p-1 bg-black/60 rounded-xl border border-white/5">
                <button
                  type="button"
                  onClick={() => setHistoryTab("my")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    historyTab === "my"
                      ? "bg-amber-400 text-stone-950 font-bold shadow-sm"
                      : "text-stone-400 hover:text-stone-200"
                  }`}
                >
                  My Inquiries ({myConversations.length})
                </button>
                <button
                  type="button"
                  onClick={() => setHistoryTab("archive")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    historyTab === "archive"
                      ? "bg-amber-400 text-stone-950 font-bold shadow-sm"
                      : "text-stone-400 hover:text-stone-200"
                  }`}
                >
                  System Archive ({conversationsList.length})
                </button>
              </div>

              <button
                onClick={() => {
                  handleResetChat();
                  setShowHistoryModal(false);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-400/15 border border-amber-400/30 hover:bg-amber-400/25 text-amber-300 text-xs font-semibold transition-all cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Session</span>
              </button>
            </div>

            {displayedConversations.length === 0 ? (
              <div className="text-center py-12 text-stone-400 text-sm font-light">
                {historyTab === "my"
                  ? "No inquiries saved in this session yet. Ask any question to start recording your personal inquiry history."
                  : "No historical conversations found in the system archive."}
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
                {displayedConversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 group ${
                      conversationId === conv.id
                        ? "bg-amber-500/15 border-amber-400/60 shadow-[0_0_15px_rgba(234,179,8,0.15)]"
                        : "bg-black/50 border-amber-500/20 hover:border-amber-400/40 hover:bg-stone-900/60"
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-[#f5eedb] group-hover:text-amber-300 transition-colors truncate">
                          {conv.title}
                        </span>
                        <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/20 text-amber-300 shrink-0">
                          {conv.jurisdiction}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-stone-300 font-mono">
                        <span>{conv.message_count} messages</span>
                        <span>•</span>
                        <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={(e) => deleteConversation(conv.id, e)}
                        className="p-1.5 rounded-lg text-stone-400 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                        title="Delete conversation"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <ArrowRight className="w-4 h-4 text-stone-400 group-hover:text-amber-300 group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-amber-500/15">
              <button
                onClick={() => setShowHistoryModal(false)}
                className="px-5 py-2.5 rounded-xl bg-stone-800 text-stone-200 hover:bg-stone-700 font-semibold text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
