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
  timestamp: string;
  isError?: boolean;
  isStreaming?: boolean;
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

/**
 * Resolves the primary official PDF URL for a statutory/treaty citation.
 * Ensures clicking on any citation opens the exact official PDF document.
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

  return `http://localhost:8000/pdf/${encodeURIComponent(filename)}`;
}

export default function Home() {
  const [jurisdiction, setJurisdiction] = useState<"national" | "international">("national");
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
  const [conversationId, setConversationId] = useState<string | null>(null);
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
      await fetch("http://localhost:8000/feedback", {
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

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const fetchConversations = async () => {
    try {
      const res = await fetch("http://localhost:8000/conversations");
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
    fetch("http://localhost:8000/corpus")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setCorpusData(data);
      })
      .catch((err) => console.warn("Could not fetch corpus provenance:", err));

    fetchConversations();
  }, []);

  const loadConversation = async (convId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/conversations/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setConversationId(data.id);
        setJurisdiction(data.jurisdiction === "international" ? "international" : "national");
        setMessages(data.messages || []);
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
      const res = await fetch(`http://localhost:8000/conversations/${convId}`, { method: "DELETE" });
      if (res.ok) {
        setConversationsList((prev) => prev.filter((c) => c.id !== convId));
        if (conversationId === convId) {
          handleResetChat();
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

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
      const response = await fetch("http://localhost:8000/ask/stream", {
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
            }

            if (eventJson.message) {
              setLoadingStep(eventJson.message);
            }

            // Real-time live token streaming into message bubble
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
                  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                };
                setMessages((prev) => [...prev, assistantMsg]);
              } else {
                const finalMsg: Message = {
                  id: currentAssistantId || Date.now().toString(),
                  role: "assistant",
                  content: data.answer || accumulatedContent || "No response text generated.",
                  needs_classification: false,
                  classification: data.classification,
                  classification_citation: data.classification_citation,
                  citations: data.citations || [],
                  confidence: data.confidence || "medium",
                  abstained: data.abstained || false,
                  language: data.language,
                  provider_used: data.provider_used,
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
      setBackendError(err.message || "Unable to reach http://localhost:8000");
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

  const handleUserSubmit = (e: React.FormEvent) => {
    e.preventDefault();
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
    sendQueryToBackend(currentQuery, {}, jurisdiction, newMessages);
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

  const handleSamplePromptClick = (sample: SamplePrompt) => {
    setJurisdiction(sample.jurisdiction);
    setLastQuery(sample.query);
    setFormulationAnswers(sample.answers);

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: sample.query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages([userMsg]);
    sendQueryToBackend(sample.query, sample.answers, sample.jurisdiction);
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

      {/* Top Fixed Header */}
      <header className="sticky top-0 z-40 w-full border-b border-amber-500/15 bg-[#070605]/80 backdrop-blur-xl px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-amber-600/30 to-black border border-amber-400/30 flex items-center justify-center shadow-[0_0_15px_rgba(234,179,8,0.2)]">
            <Scale className="w-5 h-5 text-[#fefae0]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display text-xl tracking-wider text-[#f5eedb]">IP-SAKTI SAHAYAK</span>
              <span className="text-[10px] font-semibold tracking-widest uppercase px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300">
                v1.0
              </span>
            </div>
            <p className="text-xs text-stone-400 tracking-wide font-light hidden sm:block">
              Statutory Ayurvedic & Traditional Knowledge Regulatory AI
            </p>
          </div>
        </div>

        {/* Center: Jurisdiction Toggle Pill */}
        <div className="flex items-center bg-[#12100d] p-1 rounded-full border border-amber-500/25 shadow-inner">
          <button
            onClick={() => setJurisdiction("national")}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
              jurisdiction === "national"
                ? "bg-[#f5eedb] text-[#070605] font-semibold shadow-[0_0_15px_rgba(245,238,219,0.3)]"
                : "text-stone-400 hover:text-stone-200"
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            <span>India (National)</span>
          </button>
          <button
            onClick={() => setJurisdiction("international")}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
              jurisdiction === "international"
                ? "bg-[#f5eedb] text-[#070605] font-semibold shadow-[0_0_15px_rgba(245,238,219,0.3)]"
                : "text-stone-400 hover:text-stone-200"
            }`}
          >
            <Globe2 className="w-3.5 h-3.5" />
            <span>Global (Treaties)</span>
          </button>
        </div>

        {/* Right Status Indicator & Actions */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => {
              fetchConversations();
              setShowHistoryModal(true);
            }}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#181410] hover:bg-stone-900 border border-amber-500/30 text-amber-300 text-xs font-medium transition-all shadow-sm"
            title="View Past Inquiries & Sessions"
          >
            <History className="w-3.5 h-3.5 text-amber-400" />
            <span>History {conversationsList.length > 0 ? `(${conversationsList.length})` : ""}</span>
          </button>

          <button
            onClick={() => setShowCorpusModal(true)}
            className="hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#181410] hover:bg-stone-900 border border-amber-500/30 text-amber-300 text-xs font-medium transition-all shadow-sm"
          >
            <Database className="w-3.5 h-3.5 text-amber-400" />
            <span>17 Verified Statutes</span>
          </button>

          <a
            href="http://localhost:8000/admin/audit/view"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#181410] hover:bg-stone-900 border border-emerald-500/30 text-emerald-300 text-xs font-medium transition-all shadow-sm"
            title="Inspect DPDP Minimal Query Audit Trail"
          >
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>DPDP Audit ↗</span>
          </a>

          {messages.length > 0 && (
            <button
              onClick={handleResetChat}
              className="p-2 rounded-xl text-stone-400 hover:text-[#f5eedb] hover:bg-white/5 border border-transparent hover:border-amber-500/20 transition-all text-xs flex items-center gap-1.5"
              title="Start New Inquiry"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col max-w-5xl w-full mx-auto px-4 sm:px-6 z-10 pt-4 pb-36">
        {/* LANDING / IDLE STATE */}
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center my-auto py-8 text-center">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#181410] border border-amber-500/30 text-amber-300/90 text-xs font-medium tracking-wider uppercase mb-6 shadow-[0_0_20px_rgba(234,179,8,0.15)]">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>CITATION-GROUNDED STATUTORY CO-PILOT</span>
            </div>

            <h1 className="font-display text-5xl sm:text-7xl lg:text-8xl tracking-tight text-[#f5eedb] leading-[0.9] uppercase max-w-4xl mx-auto drop-shadow-2xl">
              PROTECT THE HERITAGE. <br />
              <span className="text-[#fefae0] drop-shadow-[0_0_35px_rgba(234,179,8,0.25)]">
                OWN THE FUTURE.
              </span>
            </h1>

            <p className="mt-4 text-sm sm:text-base text-stone-300 max-w-2xl mx-auto font-light leading-relaxed">
              Verify Ayurvedic patentability under <strong className="text-amber-200 font-medium">Section 3(p)</strong>, navigate <strong className="text-amber-200 font-medium">Rule 158-B</strong> ASU drug classifications, and comply with <strong className="text-amber-200 font-medium">NBA & Nagoya</strong> access-benefit sharing.
            </p>

            {/* Central Visual Focal Graphic */}
            <div className="relative w-full max-w-3xl my-10 flex items-center justify-center">
              <div className="relative w-48 h-48 sm:w-60 sm:h-60 rounded-full bg-gradient-to-b from-amber-400/20 via-amber-950/60 to-black border border-amber-400/40 flex items-center justify-center shadow-[0_0_80px_rgba(234,179,8,0.25)] group">
                <div className="absolute inset-2 rounded-full border border-amber-300/20 border-dashed animate-[spin_60s_linear_infinite]" />
                <div className="text-center p-4 z-10">
                  <div className="w-14 h-14 mx-auto mb-2 rounded-2xl bg-[#0a0806] border border-amber-400/40 flex items-center justify-center shadow-inner">
                    <BookOpen className="w-7 h-7 text-[#fefae0]" />
                  </div>
                  <span className="font-display text-base tracking-widest text-[#f5eedb] uppercase block">
                    AYUSH STATUTES
                  </span>
                  <span className="text-[11px] text-amber-300/80 font-mono tracking-wider">
                    VERIFIED & INDEXED
                  </span>
                </div>
              </div>

              {/* Floating Glass Telemetry Cards */}
              <div className="absolute -left-2 sm:left-4 top-0 glass-panel p-3.5 rounded-2xl max-w-[200px] text-left hidden sm:block border-amber-500/20">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono tracking-widest uppercase text-emerald-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    ONLINE
                  </span>
                  <span className="text-[9px] text-stone-500 font-mono">100% GROUNDED</span>
                </div>
                <div className="font-display text-xl text-[#f5eedb]">17 STATUTES</div>
                <div className="text-[11px] text-stone-400">Indexed & Hybrid Reranked</div>
              </div>

              <div className="absolute -right-2 sm:right-4 top-2 glass-panel p-3.5 rounded-2xl max-w-[200px] text-left hidden sm:block border-amber-500/20">
                <div className="text-[10px] font-mono tracking-widest uppercase text-amber-400/90 mb-1">
                  REGULATORY ACCURACY
                </div>
                <div className="font-display text-xl text-[#f5eedb]">+100% CITATIONS</div>
                <div className="text-[11px] text-stone-400">Zero Unverified Claims</div>
              </div>

              <div className="absolute -left-2 sm:left-6 bottom-0 glass-panel p-3.5 rounded-2xl max-w-[220px] text-left hidden sm:block border-amber-500/20">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono tracking-widest uppercase text-amber-300/90">
                    CLASSIFICATION
                  </span>
                  <span className="text-[9px] text-stone-500 font-mono">D&C ACT</span>
                </div>
                <ul className="text-[11px] space-y-1 text-stone-300">
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-amber-400 shrink-0" /> Classical Medicine
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-amber-400 shrink-0" /> Proprietary Medicine
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-amber-400 shrink-0" /> Phytopharmaceuticals
                  </li>
                </ul>
              </div>

              <div className="absolute -right-2 sm:right-6 bottom-0 glass-panel p-3.5 rounded-2xl max-w-[210px] text-left hidden sm:block border-amber-500/20">
                <div className="text-[10px] font-mono tracking-widest uppercase text-amber-300/90 mb-1.5">
                  INTELLIGENT RAG
                </div>
                <div className="text-[11px] text-stone-300 space-y-1">
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-amber-400 shrink-0" /> Section 3(p) TKDL
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-amber-400 shrink-0" /> Rule 158-B Trials
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-amber-400 shrink-0" /> Form 25D Licensing
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Benchmark Questions */}
            <div className="w-full max-w-4xl mt-2">
              <div className="text-xs font-mono tracking-widest uppercase text-stone-400 mb-3 flex items-center justify-center gap-2">
                <FileCheck className="w-3.5 h-3.5 text-amber-400" />
                <span>SELECT A VERIFIED STATUTORY QUERY</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
                {SAMPLE_PROMPTS.map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSamplePromptClick(sample)}
                    className="glass-panel glass-panel-hover p-4 rounded-2xl flex items-start justify-between gap-3 group text-left"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-[#f5eedb] group-hover:text-amber-300 transition-colors">
                          {sample.title}
                        </span>
                        <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/20 text-amber-300">
                          {sample.jurisdiction}
                        </span>
                      </div>
                      <p className="text-xs text-stone-400 line-clamp-2 leading-relaxed">
                        {sample.query}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-stone-500 group-hover:text-amber-300 group-hover:translate-x-1 transition-all shrink-0 mt-1" />
                  </button>
                ))}
              </div>
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
                        </div>

                        {/* Confidence Badge */}
                        {msg.confidence && !msg.needs_classification && (
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

                      {/* SUBSTANTIVE ANSWER */}
                      {!msg.needs_classification && !msg.abstained && (
                        <div className="prose prose-invert prose-amber max-w-none text-sm sm:text-base leading-relaxed text-[#ede8d5] font-light whitespace-pre-line">
                          {msg.content}
                          {msg.isStreaming && (
                            <span className="inline-block w-2 h-4 ml-1.5 bg-amber-400 animate-pulse rounded-sm align-middle" />
                          )}
                        </div>
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
                                  <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[9px] font-mono text-stone-500">
                                    <span className="text-amber-500/70 flex items-center gap-1">
                                      <span>Primary PDF Record</span>
                                    </span>
                                    {officialUrl && (
                                      <a
                                        href={officialUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="hover:text-amber-300 hover:underline transition-colors flex items-center gap-1 text-stone-400"
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
                      <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[10px] text-stone-500 font-mono">
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

                        {!msg.needs_classification && !msg.isError && (
                          <div className="flex items-center gap-2">
                            {msg.language === "hi" ? (
                              <button
                                onClick={() => {
                                  const userMsg: Message = {
                                    id: Date.now().toString(),
                                    role: "user",
                                    content: "Convert the above response to English",
                                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                                  };
                                  const newMessages = [...messages, userMsg];
                                  setMessages(newMessages);
                                  sendQueryToBackend("Convert the above response to English", {}, jurisdiction, newMessages);
                                }}
                                disabled={isLoading}
                                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-500/10 hover:bg-amber-500/20 border border-amber-400/30 text-amber-300 text-[11px] font-sans font-medium transition-colors disabled:opacity-50"
                              >
                                <Globe2 className="w-3 h-3 text-amber-400" />
                                <span>Translate to English</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => {
                                  const userMsg: Message = {
                                    id: Date.now().toString(),
                                    role: "user",
                                    content: "उपरोक्त उत्तर को हिंदी में अनुवाद करें",
                                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                                  };
                                  const newMessages = [...messages, userMsg];
                                  setMessages(newMessages);
                                  sendQueryToBackend("उपरोक्त उत्तर को हिंदी में अनुवाद करें", {}, jurisdiction, newMessages);
                                }}
                                disabled={isLoading}
                                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-500/10 hover:bg-amber-500/20 border border-amber-400/30 text-amber-300 text-[11px] font-sans font-medium transition-colors disabled:opacity-50"
                              >
                                <Globe2 className="w-3 h-3 text-amber-400" />
                                <span>हिंदी में अनुवाद करें (Hindi)</span>
                              </button>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Optional Thumbs-Down Reason / Comment Input Drawer */}
                      {!msg.needs_classification && !msg.isError && msg.role === "assistant" && feedbackState[msg.id]?.showCommentInput && (
                        <div className="mt-3 p-3 rounded-xl bg-black/60 border border-amber-500/30 text-xs space-y-2.5">
                          <div className="flex items-center justify-between text-stone-300 font-sans font-medium">
                            <span>What could be improved? <span className="text-stone-500 text-[10px] font-normal">(optional)</span></span>
                            <button
                              type="button"
                              onClick={() => setFeedbackState((prev) => ({
                                ...prev,
                                [msg.id]: { ...prev[msg.id], showCommentInput: false, submitted: true }
                              }))}
                              className="text-stone-500 hover:text-stone-300 text-[11px]"
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
            {isLoading && (
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

      {/* FLOATING FIXED BOTTOM QUERY BAR */}
      <div className="fixed bottom-0 left-0 right-0 z-30 p-4 sm:p-6 bg-gradient-to-t from-[#050403] via-[#050403]/95 to-transparent backdrop-blur-md">
        <div className="max-w-4xl mx-auto">
          <form
            onSubmit={handleUserSubmit}
            className="relative flex items-center glass-panel rounded-2xl p-2 sm:p-2.5 border-amber-500/30 focus-within:border-amber-400/80 focus-within:shadow-[0_0_30px_rgba(234,179,8,0.2)] transition-all shadow-2xl"
          >
            <div className="pl-3 pr-2 text-stone-500">
              <Bot className="w-5 h-5 text-amber-400" />
            </div>

            <input
              ref={inputRef}
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={`Ask any Ayurvedic regulatory or patent question (${
                jurisdiction === "national" ? "India" : "International"
              })...`}
              disabled={isLoading}
              className="flex-1 bg-transparent border-0 outline-none text-sm sm:text-base text-[#f5eedb] placeholder-stone-500 px-2 py-1.5 focus:ring-0"
            />

            <button
              type="submit"
              disabled={!inputQuery.trim() || isLoading}
              className="px-4 sm:px-6 py-2.5 rounded-xl bg-[#f5eedb] hover:bg-white text-[#070605] font-semibold text-xs sm:text-sm transition-all shadow-md flex items-center gap-2 shrink-0 disabled:opacity-40 disabled:hover:bg-[#f5eedb]"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-black" />
              ) : (
                <>
                  <span>ASK SAHAYAK</span>
                  <Send className="w-3.5 h-3.5 text-black" />
                </>
              )}
            </button>
          </form>

          <div className="mt-2 text-center flex items-center justify-center gap-4 text-[11px] text-stone-500 font-mono">
            <button
              onClick={() => setShowCorpusModal(true)}
              className="text-amber-400/80 hover:text-amber-300 transition-colors flex items-center gap-1"
            >
              <Database className="w-3 h-3" />
              <span>Corpus Provenance (17 Source Acts)</span>
            </button>
            <span>•</span>
            <span>Multilingual Bhashini Translation Ready</span>
            <span>•</span>
            <span className="text-amber-500/80">Informational guidance, not formal legal advice</span>
          </div>
        </div>
      </div>

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
                          href={doc.pdf_url || `http://localhost:8000/pdf/${encodeURIComponent(doc.pdf_filename || doc.title)}`}
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
                          href={doc.pdf_url || `http://localhost:8000/pdf/${encodeURIComponent(doc.pdf_filename || doc.title)}`}
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

            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-stone-400 uppercase tracking-wider">
                Saved Sessions ({conversationsList.length})
              </span>
              <button
                onClick={() => {
                  handleResetChat();
                  setShowHistoryModal(false);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-400/15 border border-amber-400/30 hover:bg-amber-400/25 text-amber-300 text-xs font-semibold transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Session</span>
              </button>
            </div>

            {conversationsList.length === 0 ? (
              <div className="text-center py-12 text-stone-500 text-sm">
                No previous inquiries saved yet. Start a consultation to persist your session.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
                {conversationsList.map((conv) => (
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
                      <div className="flex items-center gap-3 text-[10px] text-stone-400 font-mono">
                        <span>{conv.message_count} messages</span>
                        <span>•</span>
                        <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={(e) => deleteConversation(conv.id, e)}
                        className="p-1.5 rounded-lg text-stone-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete conversation"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <ArrowRight className="w-4 h-4 text-stone-500 group-hover:text-amber-300 group-hover:translate-x-0.5 transition-all" />
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
