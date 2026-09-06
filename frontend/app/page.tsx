"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Scale,
  Shield,
  Send,
  Sparkles,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Bot,
  User,
  Globe2,
  FileCheck,
  Loader2,
  Database,
  FileText,
  ChevronDown,
  X,
  History,
  Columns2,
  Languages,
  Volume2,
  VolumeX,
} from "lucide-react";

import {
  Citation,
  Message,
  ConversationItem,
  SamplePrompt,
  CorpusProvenance,
} from "../types";
import {
  SAMPLE_PROMPTS,
  TRANSLATE_LANGUAGES,
  SPEECH_LANG_MAP,
  API_BASE_URL,
} from "../lib/constants";
import { cleanLegalTextForTTS } from "../lib/audioUtils";

import { ABSComplianceCard } from "../components/ABSComplianceCard";
import { TKDLPriorArtCard } from "../components/TKDLPriorArtCard";
import { FormulationTreeCard } from "../components/FormulationTreeCard";
import { JurisdictionComparisonModal } from "../components/JurisdictionComparisonModal";
import { ChatHistoryDrawer } from "../components/ChatHistoryDrawer";
import { PDFViewerModal } from "../components/PDFViewerModal";
import { VoiceControls } from "../components/VoiceControls";
import { FeedbackDrawer } from "../components/FeedbackDrawer";
import { CorpusProvenanceModal } from "../components/CorpusProvenanceModal";
import { FacilitatorModal } from "../components/FacilitatorModal";
import { VerificationProofCard } from "../components/VerificationProofCard";

function generateMsgId(prefix = "msg"): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}

function getCurrentTimeString(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
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
  
  // Modals initialized cleanly
  const [showFacilitatorModal, setShowFacilitatorModal] = useState(false);
  const [showCorpusModal, setShowCorpusModal] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      return params.get("view") === "corpus";
    }
    return false;
  });
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      return params.get("view") === "history";
    }
    return false;
  });
  const [selectedCitationForViewer, setSelectedCitationForViewer] = useState<Citation | null>(null);
  
  const [corpusData, setCorpusData] = useState<CorpusProvenance | null>(null);
  const [conversationsList, setConversationsList] = useState<ConversationItem[]>([]);
  const [mySessionIds, setMySessionIds] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const raw = localStorage.getItem("ipsakti_my_sessions");
        return raw ? JSON.parse(raw) : [];
      } catch {
        return [];
      }
    }
    return [];
  });
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  // Voice Input (Speech-to-Text) States
  const [isSpeechRecognitionSupported] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const win = window as unknown as {
        SpeechRecognition?: unknown;
        webkitSpeechRecognition?: unknown;
      };
      return !!(win.SpeechRecognition || win.webkitSpeechRecognition);
    }
    return false;
  });
  const [isListening, setIsListening] = useState(false);
  const [voiceLanguage, setVoiceLanguage] = useState<string>("en-IN");
  const recognitionRef = useRef<{ stop: () => void } | null>(null);
  const transcriptPrefixRef = useRef("");

  // Text-to-Speech (Read Aloud) States
  const [isSpeechSynthesisSupported] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return "speechSynthesis" in window;
    }
    return false;
  });
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  // Translation dropdown state
  const [openTranslateMsgId, setOpenTranslateMsgId] = useState<string | null>(null);

  // Feedback state
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

  const heroTextareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => {
          try {
            window.speechSynthesis.getVoices();
          } catch {}
        };
      }
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const trackMySession = (id: string) => {
    if (!id) return;
    setMySessionIds((prev) => {
      if (prev.includes(id)) return prev;
      const next = [id, ...prev];
      try {
        localStorage.setItem("ipsakti_my_sessions", JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const scrollToResponseStart = (msgId?: string) => {
    if (typeof window === "undefined") return;
    requestAnimationFrame(() => {
      setTimeout(() => {
        let targetEl: HTMLElement | null = null;
        if (msgId) {
          targetEl = document.getElementById(`message-${msgId}`);
        }
        if (!targetEl) {
          const allMsgs = document.querySelectorAll<HTMLElement>('[id^="message-"]');
          if (allMsgs.length > 0) {
            targetEl = allMsgs[allMsgs.length - 1];
          }
        }
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 70);
    });
  };

  // Automatically scroll to the top of new response turns on inquiry submission
  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      scrollToResponseStart(lastMsg.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages.length, isLoading]);

  const fetchConversations = React.useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversationsList(data.conversations || []);
      }
    } catch (err) {
      console.warn("Could not fetch conversations:", err);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    fetch(`${API_BASE_URL}/corpus`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && isMounted) setCorpusData(data);
      })
      .catch((err) => console.warn("Could not fetch corpus provenance:", err));

    fetch(`${API_BASE_URL}/conversations`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && isMounted) setConversationsList(data.conversations || []);
      })
      .catch((err) => console.warn("Could not fetch conversations:", err));

    return () => {
      isMounted = false;
    };
  }, []);

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

  const handleTranslateMessage = async (msgId: string, targetLang: string) => {
    setOpenTranslateMsgId(null);
    const targetMsg = messages.find((m) => m.id === msgId);
    if (!targetMsg) return;

    if (speakingMsgId === msgId) {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setSpeakingMsgId(null);
    }

    if (targetLang && SPEECH_LANG_MAP[targetLang]) {
      setVoiceLanguage(SPEECH_LANG_MAP[targetLang]);
    }

    if (targetLang === "en") {
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

    if (targetMsg.translations && targetMsg.translations[targetLang]) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                showTranslation: true,
                activeLanguage: targetLang,
                activeTranslationText: m.translations![targetLang],
              }
            : m
        )
      );
      return;
    }

    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, isTranslating: true } : m))
    );

    try {
      const textToTranslate = targetMsg.originalContent || targetMsg.content;
      const res = await fetch(`${API_BASE_URL}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer_text: textToTranslate,
          citations: targetMsg.citations || [],
          target_language: targetLang,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const translatedText = data.translated_text || "";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  showTranslation: true,
                  activeLanguage: targetLang,
                  activeTranslationText: translatedText,
                  translations: {
                    ...(m.translations || {}),
                    [targetLang]: translatedText,
                  },
                  isTranslating: false,
                }
              : m
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, isTranslating: false } : m))
        );
      }
    } catch (err) {
      console.warn("Translation failed:", err);
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, isTranslating: false } : m))
      );
    }
  };

  const handleToggleSimplify = async (msgId: string) => {
    const targetMsg = messages.find((m) => m.id === msgId);
    if (!targetMsg) return;

    if (speakingMsgId === msgId) {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setSpeakingMsgId(null);
    }

    if (targetMsg.showSimplified) {
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, showSimplified: false } : m))
      );
      return;
    }

    if (targetMsg.simplifiedContent) {
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, showSimplified: true } : m))
      );
      return;
    }

    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, isSimplifying: true } : m))
    );

    try {
      const formalText = targetMsg.originalFormalContent || targetMsg.originalContent || targetMsg.content;
      const res = await fetch(`${API_BASE_URL}/simplify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer_text: formalText,
          citations: targetMsg.citations || [],
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const simplifiedText = data.simplified_text || data.simplified_answer || "";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  isSimplified: true,
                  showSimplified: true,
                  simplifiedContent: simplifiedText,
                  originalFormalContent: formalText,
                  isSimplifying: false,
                }
              : m
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, isSimplifying: false } : m))
        );
      }
    } catch (err) {
      console.warn("Simplification failed:", err);
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, isSimplifying: false } : m))
      );
    }
  };

  const toggleVoiceInput = () => {
    if (typeof window === "undefined") return;
    interface CustomSpeechRecognition {
      new (): {
        continuous: boolean;
        interimResults: boolean;
        lang: string;
        onstart: () => void;
        onresult: (event: {
          resultIndex: number;
          results: Array<{ 0: { transcript: string }; isFinal: boolean }>;
        }) => void;
        onerror: (event: { error: string }) => void;
        onend: () => void;
        start: () => void;
        stop: () => void;
      };
    }
    const win = window as unknown as {
      SpeechRecognition?: CustomSpeechRecognition;
      webkitSpeechRecognition?: CustomSpeechRecognition;
    };
    const SpeechRec = win.SpeechRecognition || win.webkitSpeechRecognition;
    if (!SpeechRec) return;

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRec();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = voiceLanguage;

      transcriptPrefixRef.current = inputQuery.trim() ? inputQuery.trim() + " " : "";

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: {
        resultIndex: number;
        results: Array<{ 0: { transcript: string }; isFinal: boolean }>;
      }) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const currentText = (finalTranscript || interimTranscript).trim();
        if (currentText) {
          setInputQuery(transcriptPrefixRef.current + currentText);
        }
      };

      recognition.onerror = (event: { error: string }) => {
        console.warn("Speech recognition error:", event.error);
        setIsListening(false);
        recognitionRef.current = null;
      };

      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("Could not start speech recognition:", err);
      setIsListening(false);
    }
  };

  const handleToggleReadAloud = (msg: Message) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    if (speakingMsgId === msg.id) {
      window.speechSynthesis.cancel();
      setSpeakingMsgId(null);
      return;
    }

    window.speechSynthesis.cancel();

    let textToRead = msg.content;
    let targetLangCode = "en-IN";

    if (msg.showSimplified && msg.simplifiedContent) {
      textToRead = msg.simplifiedContent;
      targetLangCode = "en-IN";
    } else if (msg.showTranslation && msg.activeTranslationText) {
      textToRead = msg.activeTranslationText;
      const activeCode = msg.activeLanguage || "en";
      targetLangCode = SPEECH_LANG_MAP[activeCode] || "en-IN";
    }

    const cleanedText = cleanLegalTextForTTS(textToRead);
    if (!cleanedText) return;

    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.lang = targetLangCode;

    try {
      const voices = window.speechSynthesis.getVoices();
      const langPrefix = targetLangCode.split("-")[0];
      const matchingVoice =
        voices.find((v) => v.lang.toLowerCase() === targetLangCode.toLowerCase()) ||
        voices.find((v) => v.lang.toLowerCase().startsWith(langPrefix.toLowerCase()));
      if (matchingVoice) {
        utterance.voice = matchingVoice;
      }
    } catch {}

    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      setSpeakingMsgId(msg.id);
    };

    utterance.onend = () => {
      setSpeakingMsgId(null);
    };

    utterance.onerror = (e) => {
      if (e.error !== "canceled" && e.error !== "interrupted") {
        console.warn("Speech synthesis error:", e);
      }
      setSpeakingMsgId(null);
    };

    window.speechSynthesis.speak(utterance);
  };

  const loadConversation = async (convId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/conversations/${convId}`);
      if (res.ok) {
        const data = await res.json();
        setConversationId(data.id);
        trackMySession(data.id);
        setJurisdiction(data.jurisdiction === "international" ? "international" : "national");
        const loadedMsgs = (data.messages || []).map((m: Message) => ({
          ...m,
          originalContent: m.originalContent || m.content,
          activeLanguage: m.activeLanguage || "en",
          translations: m.translations || (m.content ? { en: m.content } : {}),
          case_study: m.case_study || m.tkdl_pointer?.case_study,
        }));
        setMessages(loadedMsgs);
        setShowHistoryModal(false);
        setTimeout(() => {
          scrollToResponseStart();
        }, 120);
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
          } catch {}
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

  const handleResetChat = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeakingMsgId(null);
    setMessages([]);
    setFormulationAnswers({});
    setConversationId(null);
    setBackendError(null);
    setInputQuery("");
    setLastQuery("");
  };

  const sendQueryToBackend = async (
    query: string,
    currentAnswers: Record<string, boolean>,
    targetJurisdiction: "national" | "international",
    customHistory?: Message[]
  ) => {
    if (!query || !query.trim()) {
      const errorMsg: Message = {
        id: generateMsgId("err"),
        role: "assistant",
        content: "Error 400: Query cannot be empty or whitespace-only.",
        isError: true,
        timestamp: getCurrentTimeString(),
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
      .slice(-6)
      .map((m) => ({
        role: m.role,
        content: m.originalContent || m.content,
        citations: m.citations || [],
        classification: m.classification,
        language: m.language,
      }));

    if (isCompareMode) {
      setLoadingStep("Running parallel National & International statutory pipelines...");
      try {
        const response = await fetch(`${API_BASE_URL}/ask/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: query.trim(),
            conversation_id: conversationId,
            formulation_answers: currentAnswers,
            history: historyPayload,
          }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Server error: ${response.status}`);
        }

        const cmpData = await response.json();
        const newConvId = cmpData.conversation_id || conversationId;
        if (newConvId) {
          setConversationId(newConvId);
          trackMySession(newConvId);
        }

        const comparisonMsg: Message = {
          id: generateMsgId("cmp"),
          role: "assistant",
          content: `Dual-Jurisdiction Comparative Analysis for: "${query}"`,
          is_comparison: true,
          comparison_data: cmpData,
          timestamp: getCurrentTimeString(),
        };

        setMessages((prev) => [...prev, comparisonMsg]);
        fetchConversations();
      } catch (err: unknown) {
        const errorMsgText = err instanceof Error ? err.message : "Parallel comparison pipeline encountered an error.";
        console.error("Comparison request failed:", err);
        setBackendError(errorMsgText);
        const errorMsg: Message = {
          id: generateMsgId("err"),
          role: "assistant",
          content: `Comparison Error: ${errorMsgText}`,
          isError: true,
          timestamp: getCurrentTimeString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
      return;
    }

    const streamingAssistantId = generateMsgId("asst");
    const initialStreamingMsg: Message = {
      id: streamingAssistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp: getCurrentTimeString(),
      citations: [],
    };
    setMessages((prev) => [...prev, initialStreamingMsg]);

    try {
      const response = await fetch(`${API_BASE_URL}/ask/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          jurisdiction: targetJurisdiction,
          formulation_answers: currentAnswers,
          conversation_id: conversationId,
          history: historyPayload,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No readable stream received from server.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split(/\r?\n\r?\n/);
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const parsed = JSON.parse(jsonStr);

            if (parsed.stage === "detect_language") {
              setLoadingStep(parsed.message || "Detecting inquiry language...");
              if (parsed.conversation_id) {
                setConversationId(parsed.conversation_id);
                trackMySession(parsed.conversation_id);
              }
            } else if (parsed.stage === "translating_query" || parsed.stage === "translating_answer") {
              setLoadingStep(parsed.message);
            } else if (parsed.stage === "classification_check") {
              setLoadingStep(parsed.message);
            } else if (parsed.stage === "retrieval") {
              setLoadingStep(parsed.message);
            } else if (parsed.stage === "reranking") {
              setLoadingStep(parsed.message);
            } else if (parsed.stage === "synthesis") {
              setLoadingStep(parsed.message);
            } else if (parsed.stage === "llm_token") {
              const delta = parsed.answer_delta !== undefined ? parsed.answer_delta : parsed.delta || "";
              if (delta) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === streamingAssistantId
                      ? { ...m, content: m.content + delta }
                      : m
                  )
                );
              }
            } else if (parsed.stage === "complete") {
              const finalData = parsed.data;
              const newConvId = finalData.conversation_id || conversationId;
              if (newConvId) {
                setConversationId(newConvId);
                trackMySession(newConvId);
              }

              if (finalData.needs_classification) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === streamingAssistantId
                      ? {
                          ...m,
                          isStreaming: false,
                          needs_classification: true,
                          question: finalData.question,
                          language: finalData.language,
                          pending_formulation_answers: currentAnswers,
                          abs_compliance: finalData.abs_compliance,
                          tkdl_pointer: finalData.tkdl_pointer,
                          case_study: finalData.case_study || finalData.tkdl_pointer?.case_study,
                        }
                      : m
                  )
                );
              } else {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === streamingAssistantId
                      ? {
                          ...m,
                          isStreaming: false,
                          content: finalData.answer,
                          originalContent: finalData.answer,
                          activeLanguage: finalData.language || "en",
                          translations: { [finalData.language || "en"]: finalData.answer },
                          citations: finalData.citations || [],
                          confidence: finalData.confidence,
                          classification: finalData.classification,
                          classification_citation: finalData.classification_citation,
                          abstained: finalData.abstained,
                          language: finalData.language,
                          provider_used: finalData.provider_used,
                          abs_compliance: finalData.abs_compliance,
                          tkdl_pointer: finalData.tkdl_pointer,
                          case_study: finalData.case_study || finalData.tkdl_pointer?.case_study,
                          verification_proof: finalData.verification_proof,
                        }
                      : m
                  )
                );
              }
              fetchConversations();
            } else if (parsed.stage === "error") {
              throw new Error(parsed.error || "Streaming synthesis error.");
            }
          } catch (e) {
            console.warn("Error parsing stream chunk:", e);
          }
        }
      }
    } catch (err: unknown) {
      console.warn("Stream failed, executing synchronous fallback:", err);
      try {
        setLoadingStep("Synchronizing with legal inference fallback...");
        const fallbackRes = await fetch(`${API_BASE_URL}/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: query.trim(),
            jurisdiction: targetJurisdiction,
            formulation_answers: currentAnswers,
            conversation_id: conversationId,
            history: historyPayload,
          }),
        });

        if (!fallbackRes.ok) {
          const errPayload = await fallbackRes.json().catch(() => ({}));
          throw new Error(errPayload.detail || `Server returned ${fallbackRes.status}`);
        }

        const data = await fallbackRes.json();
        const newConvId = data.conversation_id || conversationId;
        if (newConvId) {
          setConversationId(newConvId);
          trackMySession(newConvId);
        }

        if (data.needs_classification) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingAssistantId
                ? {
                    ...m,
                    isStreaming: false,
                    needs_classification: true,
                    question: data.question,
                    language: data.language,
                    pending_formulation_answers: currentAnswers,
                    abs_compliance: data.abs_compliance,
                    tkdl_pointer: data.tkdl_pointer,
                    case_study: data.case_study || data.tkdl_pointer?.case_study,
                  }
                : m
            )
          );
        } else {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingAssistantId
                ? {
                    ...m,
                    isStreaming: false,
                    content: data.answer,
                    originalContent: data.answer,
                    activeLanguage: data.language || "en",
                    translations: { [data.language || "en"]: data.answer },
                    citations: data.citations || [],
                    confidence: data.confidence,
                    classification: data.classification,
                    classification_citation: data.classification_citation,
                    abstained: data.abstained,
                    language: data.language,
                    provider_used: data.provider_used,
                    abs_compliance: data.abs_compliance,
                    tkdl_pointer: data.tkdl_pointer,
                    case_study: data.case_study || data.tkdl_pointer?.case_study,
                    verification_proof: data.verification_proof,
                  }
                : m
            )
          );
        }
        fetchConversations();
      } catch (fallbackErr: unknown) {
        const fallbackMsgText = fallbackErr instanceof Error ? fallbackErr.message : "Failed to retrieve statutory authority.";
        console.error("Full pipeline failure:", fallbackErr);
        setBackendError(fallbackMsgText);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === streamingAssistantId
              ? {
                  ...m,
                  isStreaming: false,
                  isError: true,
                  content: `Inference Error: ${fallbackMsgText}`,
                }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleClassificationSelect = async (questionId: string, value: boolean) => {
    const updatedAnswers = {
      ...formulationAnswers,
      [questionId]: value,
    };
    setFormulationAnswers(updatedAnswers);

    const activeQuery = lastQuery || inputQuery;
    if (!activeQuery) return;

    await sendQueryToBackend(activeQuery, updatedAnswers, jurisdiction);
  };

  const handleABSOptionSelect = async (msgId: string, questionId: string, value: boolean) => {
    const targetMsg = messages.find((m) => m.id === msgId);
    if (!targetMsg || !targetMsg.abs_compliance) return;

    const updatedAnswers = {
      ...(targetMsg.abs_compliance.answers || {}),
      [questionId]: value,
    };

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
      const res = await fetch(`${API_BASE_URL}/compliance/abs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: associatedQuery,
          answers: updatedAnswers,
        }),
      });

      if (res.ok) {
        const absResult = await res.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  abs_compliance: absResult,
                }
              : m
          )
        );
      }
    } catch (err) {
      console.warn("Failed to evaluate ABS compliance:", err);
    }
  };

  const handleUserSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
      setIsListening(false);
    }

    const trimmed = inputQuery.trim();
    if (!trimmed || isLoading) return;

    setLastQuery(trimmed);

    const userMsg: Message = {
      id: generateMsgId("user"),
      role: "user",
      content: trimmed,
      timestamp: getCurrentTimeString(),
    };

    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    setInputQuery("");

    await sendQueryToBackend(trimmed, formulationAnswers, jurisdiction, updatedHistory);
  };

  const handleSamplePromptClick = async (sample: SamplePrompt) => {
    if (isLoading) return;
    setInputQuery("");
    setJurisdiction(sample.jurisdiction);
    setFormulationAnswers(sample.answers || {});
    setIsCompareMode(!!sample.is_compare);
    setLastQuery(sample.query);

    const userMsg: Message = {
      id: generateMsgId("user"),
      role: "user",
      content: sample.query,
      timestamp: getCurrentTimeString(),
    };

    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    scrollToResponseStart(userMsg.id);

    await sendQueryToBackend(
      sample.query,
      sample.answers || {},
      sample.jurisdiction,
      updatedHistory
    );
  };

  return (
    <main className="min-h-screen relative flex flex-col bg-[#070605] text-[#ede8d5] font-sans selection:bg-amber-400 selection:text-black pb-32">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[450px] bg-amber-500/10 rounded-full blur-[140px]" />
        <div className="absolute top-1/3 -left-32 w-80 h-80 bg-amber-600/5 rounded-full blur-[100px]" />
        <div className="absolute top-2/3 -right-32 w-80 h-80 bg-amber-500/5 rounded-full blur-[100px]" />
      </div>

      {/* HEADER NAVBAR */}
      <header className="sticky top-0 z-40 border-b border-amber-500/20 bg-[#070605]/90 backdrop-blur-xl shadow-lg">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 sm:h-20 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 cursor-pointer" onClick={handleResetChat}>
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-400/25 via-amber-500/10 to-transparent border border-amber-400/40 flex items-center justify-center text-amber-300 shadow-[0_0_20px_rgba(234,179,8,0.2)]">
              <Scale className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-lg sm:text-xl tracking-wider text-[#f5eedb]">
                  IP-SAKTI
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-400/15 border border-amber-400/30 text-amber-300 font-semibold tracking-wider uppercase">
                  Sahayak
                </span>
              </div>
              <p className="text-[11px] text-stone-400 hidden sm:block font-light">
                Grounded Statutory Intelligence for Ayurvedic IP & Regulatory Affairs
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Compare Toggle */}
            <button
              onClick={() => setIsCompareMode((prev) => !prev)}
              className={`px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 border cursor-pointer ${
                isCompareMode
                  ? "bg-amber-400 text-stone-950 border-amber-300 shadow-[0_0_15px_rgba(251,191,36,0.3)]"
                  : "bg-white/5 text-stone-300 border-white/10 hover:border-amber-400/40 hover:text-amber-200"
              }`}
            >
              <Columns2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Compare</span>
            </button>

            {/* Jurisdiction Selector */}
            {!isCompareMode && (
              <div className="flex items-center bg-black/60 p-1 rounded-2xl border border-amber-500/30">
                <button
                  onClick={() => setJurisdiction("national")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                    jurisdiction === "national"
                      ? "bg-amber-400 text-stone-950 font-bold shadow-sm"
                      : "text-stone-400 hover:text-stone-200"
                  }`}
                >
                  <Shield className="w-3 h-3" />
                  <span>India</span>
                </button>
                <button
                  onClick={() => setJurisdiction("international")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                    jurisdiction === "international"
                      ? "bg-amber-400 text-stone-950 font-bold shadow-sm"
                      : "text-stone-400 hover:text-stone-200"
                  }`}
                >
                  <Globe2 className="w-3 h-3" />
                  <span>Global</span>
                </button>
              </div>
            )}

            {/* History Drawer Trigger */}
            <button
              onClick={() => setShowHistoryModal(true)}
              className="p-2 sm:px-3 sm:py-2 rounded-xl bg-white/5 border border-white/10 hover:border-amber-400/40 text-stone-300 hover:text-amber-200 text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer"
              title="View session history & audit logs"
            >
              <History className="w-4 h-4 text-amber-400" />
              <span className="hidden sm:inline">Sessions</span>
            </button>

            {/* Reset Chat Button */}
            {messages.length > 0 && (
              <button
                onClick={handleResetChat}
                className="p-2 rounded-xl bg-white/5 border border-white/10 hover:border-amber-400/40 text-stone-300 hover:text-amber-200 transition-colors cursor-pointer"
                title="Reset conversation"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <div className="max-w-4xl mx-auto w-full px-4 sm:px-6 pt-6 flex-1 flex flex-col justify-start relative z-10">
        {/* Error Notification */}
        {backendError && (
          <div className="mb-6 p-4 rounded-2xl bg-red-950/40 border border-red-500/40 text-red-200 flex items-start justify-between gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{backendError}</span>
            </div>
            <button onClick={() => setBackendError(null)} className="text-red-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* HERO / EMPTY STATE */}
        {messages.length === 0 && (
          <div className="my-auto py-8 sm:py-12 flex flex-col justify-center">
            <div className="text-center space-y-3 mb-8">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-300 text-xs font-mono tracking-wider uppercase">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Statutory AI for Ayurvedic IP</span>
              </div>
              <h1 className="font-display text-3xl sm:text-5xl lg:text-6xl text-[#f5eedb] tracking-tight font-bold">
                Ayurvedic Legal Intelligence
              </h1>
              <p className="text-sm sm:text-base text-stone-400 max-w-2xl mx-auto font-light leading-relaxed">
                Multilingual, citation-grounded statutory AI for Ayurvedic intellectual property, traditional knowledge & regulatory affairs.
              </p>
            </div>

            {/* Hero Input Box */}
            <div className="glass-panel p-4 sm:p-6 rounded-3xl border-amber-500/30 shadow-2xl relative">
              <div className="space-y-4">
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
                      ? "Compare National (India) vs International (Treaties) side-by-side..."
                      : `Ask any Ayurvedic regulatory or patent question (${
                          jurisdiction === "national" ? "India" : "International"
                        })...`
                  }
                  rows={3}
                  disabled={isLoading}
                  className="w-full bg-transparent border-0 outline-none text-base sm:text-lg text-[#f5eedb] placeholder-stone-400 resize-none font-light"
                />

                <div className="flex flex-col gap-3 pt-2 border-t border-white/5">
                  <div className="flex items-center justify-between text-xs text-stone-400">
                    <VoiceControls
                      isSupported={isSpeechRecognitionSupported}
                      isListening={isListening}
                      voiceLanguage={voiceLanguage}
                      onLanguageChange={setVoiceLanguage}
                      onToggleListening={toggleVoiceInput}
                      disabled={isLoading}
                    />

                    <span className="hidden sm:inline font-mono text-[11px] text-stone-400">
                      Press Enter ↵ to ask
                    </span>
                  </div>

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

                  {/* Sample Prompts */}
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
                          className="p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/5 hover:border-amber-400/30 text-stone-300 hover:text-[#f5eedb] text-xs font-normal transition-all text-left flex items-center justify-between gap-2 group cursor-pointer"
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

            {/* Bottom Provenance & Microcopy */}
            <div className="mt-8 pt-4 border-t border-white/5 text-center flex flex-wrap items-center justify-center gap-3 text-xs text-stone-400 font-mono">
              <span>Every claim cites its source</span>
              <span>•</span>
              <button
                onClick={() => setShowCorpusModal(true)}
                className="text-amber-400/90 hover:text-amber-300 hover:underline transition-colors cursor-pointer"
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
          <div className="space-y-6 pt-4 w-full max-w-full overflow-x-hidden">
            {messages.map((msg) => {
              const isUser = msg.role === "user";

              if (isUser) {
                return (
                  <div
                    id={`message-${msg.id}`}
                    key={msg.id}
                    className="flex justify-end gap-3 items-start pl-8 scroll-top-offset scroll-mt-24"
                  >
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
                return (
                  <div id={`message-${msg.id}`} key={msg.id} className="scroll-top-offset scroll-mt-24 w-full max-w-full">
                    <JurisdictionComparisonModal comparisonData={msg.comparison_data} />
                  </div>
                );
              }

              // Assistant Response
              return (
                <div
                  id={`message-${msg.id}`}
                  key={msg.id}
                  className="flex justify-start gap-3 items-start pr-4 sm:pr-8 scroll-top-offset scroll-mt-24 w-full max-w-full"
                >
                  <div className="w-9 h-9 rounded-xl bg-[#12100e] border border-amber-400/40 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(234,179,8,0.15)] mt-1">
                    <Scale className="w-4 h-4 text-[#fefae0]" />
                  </div>

                  <div className="flex-1 max-w-3xl space-y-3 min-w-0">
                    <div
                      className={`glass-panel rounded-2xl p-5 sm:p-6 shadow-2xl max-w-full ${
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
                        <FormulationTreeCard
                          question={msg.question}
                          isLoading={isLoading}
                          onSelect={handleClassificationSelect}
                        />
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
                              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors shadow-md cursor-pointer"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>Talk to Human IP Facilitator</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* SUBSTANTIVE ANSWER */}
                      {!msg.needs_classification && !msg.abstained && (
                        <div>
                          {msg.isStreaming && !msg.content ? (
                            <div className="flex items-center gap-2.5 text-xs text-amber-300 font-mono py-1.5 animate-pulse">
                              <Loader2 className="w-4 h-4 text-amber-400 animate-spin shrink-0" />
                              <span>{loadingStep || "Analyzing statutory corpus & synthesizing answer..."}</span>
                            </div>
                          ) : (
                            <div className="prose prose-invert prose-amber max-w-none text-sm sm:text-base leading-relaxed text-[#ede8d5] font-light whitespace-pre-line mb-4">
                              {msg.content}
                              {msg.isStreaming && (
                                <span className="inline-block w-2 h-4 ml-1.5 bg-amber-400 animate-pulse rounded-sm align-middle" />
                              )}
                            </div>
                          )}

                          {/* SIMPLIFIED PLAIN-LANGUAGE RESPONSE */}
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
                                  className="text-stone-400 hover:text-stone-200 p-1 rounded hover:bg-white/5 transition-colors cursor-pointer"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                              <p className="text-sm sm:text-base leading-relaxed text-emerald-100/95 font-light whitespace-pre-line">
                                {msg.simplifiedContent}
                              </p>
                              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-stone-400">
                                <span className="text-emerald-400/80">Phrased for non-lawyers • Same legal grounding</span>
                                <span>See statutory citations below ↓</span>
                              </div>
                            </div>
                          )}

                          {/* REGIONAL TRANSLATION RESPONSE */}
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
                                  className="text-stone-400 hover:text-stone-200 p-1 rounded hover:bg-white/5 transition-colors cursor-pointer"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                              <p className="text-sm sm:text-base leading-relaxed text-amber-100/95 font-light whitespace-pre-line">
                                {msg.activeTranslationText}
                              </p>
                              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-stone-400">
                                <span className="text-amber-400/80">Statutory citations strictly preserved in English</span>
                                <span>See statutory citations below ↓</span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* DEDICATED ABS COMPLIANCE HELPER PANEL */}
                      {msg.abs_compliance && msg.abs_compliance.triggered && (
                        <ABSComplianceCard
                          messageId={msg.id}
                          absData={msg.abs_compliance}
                          onOptionSelect={handleABSOptionSelect}
                        />
                      )}

                      {/* DEDICATED TKDL PRIOR-ART & CASE STUDIES CARD */}
                      <TKDLPriorArtCard
                        tkdlData={msg.tkdl_pointer}
                        caseStudyData={msg.case_study || msg.tkdl_pointer?.case_study}
                      />

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
                              const officialUrl = cit.official_url;

                              return (
                                <div
                                  key={idx}
                                  onClick={() => setSelectedCitationForViewer(cit)}
                                  className="group relative p-3.5 rounded-xl bg-black/40 hover:bg-amber-950/25 border border-amber-500/25 hover:border-amber-400/70 transition-all duration-200 shadow-sm text-left flex flex-col justify-between cursor-pointer"
                                >
                                  <div>
                                    <div className="flex items-center justify-between gap-2 mb-1.5">
                                      <span className="text-[11px] font-mono text-amber-300 font-bold tracking-wide group-hover:text-amber-200 transition-colors">
                                        {cit.section}
                                      </span>
                                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-[10px] text-amber-300 font-mono group-hover:bg-amber-400 group-hover:text-black transition-all">
                                        <FileText className="w-3 h-3" />
                                        <span>PDF</span>
                                        {cit.page_number && (
                                          <span className="text-[9px] font-bold">p.{cit.page_number}</span>
                                        )}
                                        <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                                      </span>
                                    </div>
                                    <div className="text-xs text-stone-200 font-normal group-hover:text-white transition-colors leading-snug">
                                      {cit.source}
                                    </div>
                                  </div>

                                  <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[9px] font-mono text-stone-400">
                                    <span className="text-amber-500/70">
                                      Primary PDF Record {cit.page_number ? `(Page ${cit.page_number})` : ""}
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

                      {/* DEDICATED ACCURACY & CORPUS VERIFICATION PROOF CARD */}
                      {!msg.needs_classification && !msg.isError && msg.role === "assistant" && (
                        <VerificationProofCard
                          proof={msg.verification_proof}
                          citations={msg.citations}
                          timing_ms={msg.verification_proof?.timing_ms}
                          provider_used={msg.provider_used}
                        />
                      )}

                      {/* Footer Actions & Metadata */}
                      {!msg.isStreaming && (
                        <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[10px] text-stone-400 font-mono">
                          <div className="flex items-center gap-3">
                            <span>
                              {msg.provider_used && `Provider: ${msg.provider_used.toUpperCase()}`}
                            </span>
                            <span>{msg.timestamp}</span>

                            {/* Feedback Drawer Trigger */}
                            {!msg.needs_classification && !msg.isError && msg.role === "assistant" && (
                              <div className="ml-1 border-l border-white/10 pl-3">
                                <FeedbackDrawer
                                  messageId={msg.id}
                                  messageContent={msg.content}
                                  citations={msg.citations}
                                  feedbackState={feedbackState[msg.id]}
                                  onFeedback={handleFeedback}
                                />
                              </div>
                            )}
                          </div>

                          {/* Read Aloud & Simplify & Translation Tools */}
                          {!msg.needs_classification && !msg.isError && (
                            <div className="flex items-center gap-2">
                              {/* Read Aloud TTS Button */}
                              {isSpeechSynthesisSupported && (
                                <button
                                  type="button"
                                  onClick={() => handleToggleReadAloud(msg)}
                                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-sans transition-all cursor-pointer ${
                                    speakingMsgId === msg.id
                                      ? "bg-amber-400 text-stone-950 font-bold shadow-[0_0_12px_rgba(251,191,36,0.4)] animate-pulse"
                                      : "bg-white/5 hover:bg-white/10 text-stone-300 hover:text-amber-200 border border-white/10"
                                  }`}
                                  title={speakingMsgId === msg.id ? "Stop reading aloud" : "Read answer aloud"}
                                >
                                  {speakingMsgId === msg.id ? (
                                    <>
                                      {/* Dynamic Audio Equalizer Wave Animation */}
                                      <div className="flex items-center gap-0.5 h-3.5 px-0.5 text-stone-950">
                                        <span className="w-0.5 bg-stone-950 rounded-full wave-bar-1" />
                                        <span className="w-0.5 bg-stone-950 rounded-full wave-bar-2" />
                                        <span className="w-0.5 bg-stone-950 rounded-full wave-bar-3" />
                                        <span className="w-0.5 bg-stone-950 rounded-full wave-bar-4" />
                                      </div>
                                      <VolumeX className="w-3.5 h-3.5 ml-0.5" />
                                      <span>Playing Audio</span>
                                    </>
                                  ) : (
                                    <>
                                      <Volume2 className="w-3.5 h-3.5 text-amber-400" />
                                      <span>Listen</span>
                                    </>
                                  )}
                                </button>
                              )}

                              {/* Simplify Button */}
                              <button
                                type="button"
                                onClick={() => handleToggleSimplify(msg.id)}
                                disabled={msg.isSimplifying}
                                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-sans transition-all cursor-pointer ${
                                  msg.showSimplified
                                    ? "bg-emerald-500 text-black font-semibold shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                                    : "bg-white/5 hover:bg-white/10 text-stone-300 hover:text-emerald-300 border border-white/10"
                                }`}
                                title="Explain in plain language for non-lawyers"
                              >
                                {msg.isSimplifying ? (
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                ) : (
                                  <Sparkles className="w-3 h-3 text-emerald-400" />
                                )}
                                <span>{msg.showSimplified ? "Simplified" : "Simplify"}</span>
                              </button>

                              {/* Translation Dropdown */}
                              <div className="relative">
                                <button
                                  type="button"
                                  onClick={() =>
                                    setOpenTranslateMsgId((prev) => (prev === msg.id ? null : msg.id))
                                  }
                                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-stone-300 hover:text-amber-200 border border-white/10 text-xs font-sans transition-colors cursor-pointer"
                                >
                                  <Languages className="w-3 h-3 text-amber-400" />
                                  <span>Translate</span>
                                  <ChevronDown className="w-3 h-3" />
                                </button>

                                {openTranslateMsgId === msg.id && (
                                  <div className="absolute right-0 bottom-full mb-1 w-40 rounded-xl bg-stone-900 border border-amber-500/30 p-1 shadow-2xl z-20 space-y-0.5">
                                    {TRANSLATE_LANGUAGES.map((lang) => (
                                      <button
                                        key={lang.code}
                                        type="button"
                                        onClick={() => handleTranslateMessage(msg.id, lang.code)}
                                        className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-amber-400 hover:text-black transition-colors flex items-center justify-between cursor-pointer"
                                      >
                                        <span>{lang.name}</span>
                                        <span className="font-mono text-[10px] opacity-70">
                                          {lang.native}
                                        </span>
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* LIVE SSE PROGRESS INDICATOR */}
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

      {/* FLOATING BOTTOM QUERY BAR */}
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

              {/* Voice Controls in Bottom Bar */}
              <div className="mr-2">
                <VoiceControls
                  isSupported={isSpeechRecognitionSupported}
                  isListening={isListening}
                  voiceLanguage={voiceLanguage}
                  onLanguageChange={setVoiceLanguage}
                  onToggleListening={toggleVoiceInput}
                  disabled={isLoading}
                />
              </div>

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
                className="text-amber-400/90 hover:text-amber-300 transition-colors flex items-center gap-1 cursor-pointer"
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

      {/* MODALS */}
      <CorpusProvenanceModal
        isOpen={showCorpusModal}
        onClose={() => setShowCorpusModal(false)}
        corpusData={corpusData}
      />

      <FacilitatorModal
        isOpen={showFacilitatorModal}
        onClose={() => setShowFacilitatorModal(false)}
      />

      <ChatHistoryDrawer
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        conversationsList={conversationsList}
        mySessionIds={mySessionIds}
        activeConversationId={conversationId}
        onSelectConversation={loadConversation}
        onDeleteConversation={deleteConversation}
        onNewSession={handleResetChat}
      />

      <PDFViewerModal
        citation={selectedCitationForViewer}
        isOpen={!!selectedCitationForViewer}
        onClose={() => setSelectedCitationForViewer(null)}
      />
    </main>
  );
}
