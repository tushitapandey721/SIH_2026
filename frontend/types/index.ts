export interface Citation {
  source: string;
  section: string;
  url?: string;
  pdf_url?: string;
  official_url?: string;
  pdf_filename?: string;
  page_number?: number;
}

export interface QuestionData {
  id: string;
  question: string;
  options: boolean[];
  help_text?: string;
}

export interface ABSResult {
  requires_nba_approval: boolean;
  requires_sbb_intimation: boolean;
  applicable_provision: string;
  exact_statutory_text?: string;
  next_steps: string[];
  relevant_forms: string[];
  sbb_state?: string;
  summary?: string;
}

export interface ABSQuestionOption {
  label: string;
  value: boolean;
}

export interface ABSQuestion {
  id: string;
  question: string;
  options: ABSQuestionOption[];
  help_text?: string;
}

export interface ABSComplianceData {
  triggered: boolean;
  status: "needs_input" | "completed" | "not_triggered";
  answers: Record<string, boolean>;
  next_question?: ABSQuestion | null;
  result?: ABSResult | null;
}

export interface TKDLIpcClass {
  code: string;
  description: string;
}

export interface TKDLHints {
  formulation_category: string;
  formulation_description: string;
  therapeutic_area: string;
  ipc_classes: TKDLIpcClass[];
  classical_source_texts: string[];
  search_keywords: string[];
  is_simulated_search: boolean;
}

export interface TKDLPriorArtWorkflowStep {
  step: string;
  detail: string;
}

export interface HistoricalCaseItem {
  title: string;
  patent_number?: string;
  jurisdiction?: string;
  year_granted?: string;
  year_revoked?: string;
  facts?: string;
  grounds?: string;
  traditional_knowledge_basis?: string;
  legal_significance?: string;
}

export interface HistoricalCaseStudyData {
  triggered: boolean;
  title: string;
  subtitle?: string;
  turmeric_case: HistoricalCaseItem;
  neem_case: HistoricalCaseItem;
  closing_line: string;
  source_footnote: string;
}

export interface TKDLPointerData {
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

export interface ComparisonJurisdictionResult {
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

export interface JurisdictionComparisonData {
  query: string;
  conversation_id: string;
  national: ComparisonJurisdictionResult;
  international: ComparisonJurisdictionResult;
  shared_citations_count: number;
  shared_sources: string[];
  is_zero_overlap: boolean;
  latency_ms: number;
}

export interface Message {
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

export interface ConversationItem {
  id: string;
  title: string;
  jurisdiction: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_time?: string;
}

export interface SamplePrompt {
  title: string;
  query: string;
  jurisdiction: "national" | "international";
  answers: Record<string, boolean>;
  is_compare?: boolean;
}

export interface CorpusDocument {
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
  page_number?: number;
}

export interface CorpusProvenance {
  total_documents: number;
  national_count: number;
  international_count: number;
  national: CorpusDocument[];
  international: CorpusDocument[];
}
