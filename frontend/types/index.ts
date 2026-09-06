export interface Citation {
  source: string;
  section: string;
  url?: string;
  pdf_url?: string;
  official_url?: string;
  pdf_filename?: string;
  page_number?: number;
  text_excerpt?: string;
  match_score?: number;
  verified?: boolean;
}

export interface VerificationAnchor {
  source: string;
  section: string;
  page_number?: number;
  pdf_filename?: string;
  pdf_url?: string;
  official_url?: string;
  text_excerpt?: string;
  status?: string;
  match_score?: number;
}

export interface RankedDocumentItem {
  rank: number;
  title: string;
  section: string;
  cross_encoder_score: number;
  score_percentage: string;
  relevance_tier: string;
  used_in_synthesis: boolean;
  text_snippet?: string;
  pdf_filename?: string;
  pdf_url?: string;
  page_number?: number;
}

export interface CitationMetrics {
  total_citations_verified: number;
  direct_pdf_deep_links: number;
  statutory_provisions_covered: string[];
  authority_level: string;
  hallucination_risk: string;
}

export interface AccuracyMethodology {
  dense_retrieval_formula: string;
  sparse_retrieval_formula: string;
  hybrid_fusion_formula: string;
  cross_encoder_formula: string;
  grounding_verification_rule: string;
}

export interface PipelineStageItem {
  stage: string;
  detail: string;
}

export interface VerificationProof {
  accuracy_percentage: number;
  accuracy_label: string;
  method: string;
  hardware_accelerator?: string;
  pipeline_stages: PipelineStageItem[];
  verification_anchors: VerificationAnchor[];
  ranked_documents?: RankedDocumentItem[];
  citation_metrics?: CitationMetrics;
  accuracy_methodology?: AccuracyMethodology;
  corpus_integrity?: string;
  timing_ms?: Record<string, number>;
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
  verification_proof?: VerificationProof;
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
  verification_proof?: VerificationProof;
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
