# IP-SAKTI Sahayak: Verified Technical Feature Reference

> **Grounded Legal RAG System for Indian Intellectual Property, Ayurvedic Regulatory Affairs & International Treaties.**  
> *Technical reference document detailing every implemented and verified capability, benchmark metrics, real test evidence, and documented limitations.*

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Feature 1: Citation-Grounded RAG Core (Hybrid Dense + BM25 + RRF + Cross-Encoder)](#feature-1-citation-grounded-rag-core-hybrid-dense--bm25--rrf--cross-encoder)
- [Feature 2: Exact-Citation Lookup & Query Normalization Layer](#feature-2-exact-citation-lookup--query-normalization-layer)
- [Feature 3: Formulation Classification Flow (6-Way Conversational Decision Tree)](#feature-3-formulation-classification-flow-6-way-conversational-decision-tree)
- [Feature 4: Strict Jurisdiction Separation (National vs. International Filtering)](#feature-4-strict-jurisdiction-separation-national-vs-international-filtering)
- [Feature 5: Multi-Turn Conversational Memory & Contextual Query Reformulation](#feature-5-multi-turn-conversational-memory--contextual-query-reformulation)
- [Feature 6: Out-of-Scope Abstention Guardrail & Facilitator Escalation](#feature-6-out-of-scope-abstention-guardrail--facilitator-escalation)
- [Feature 7: Multi-Provider High-Availability LLM Client (Multi-Tier Groq Candidate Failover + Mistral Fallback)](#feature-7-multi-provider-high-availability-llm-client-multi-tier-groq-candidate-failover--mistral-fallback)
- [Feature 8: Curated 17-Statute Corpus, Layout-Aware Chunking & Manifest Integrity](#feature-8-curated-17-statute-corpus-layout-aware-chunking--manifest-integrity)
- [Feature 9: Atomic In-Memory BM25 Startup Disk Cache](#feature-9-atomic-in-memory-bm25-startup-disk-cache)
- [Feature 10: Direct Source Document PDF Citation Viewer](#feature-10-direct-source-document-pdf-citation-viewer)
- [Feature 11: Multilingual Translation Layer & Digital India Bhashini Dhruva Architecture](#feature-11-multilingual-translation-layer--digital-india-bhashini-dhruva-architecture)
- [Feature 12: SQLite-Backed Session Persistence & History Drawer](#feature-12-sqlite-backed-session-persistence--history-drawer)
- [Feature 13: DPDP-Aligned Minimal Regulatory Audit Trail & Administrative Dashboard](#feature-13-dpdp-aligned-minimal-regulatory-audit-trail--administrative-dashboard)
- [Feature 14: Granular User Answer Feedback Mechanism (Thumbs Up/Down + Diagnostic Tagging)](#feature-14-granular-user-answer-feedback-mechanism-thumbs-updown--diagnostic-tagging)
- [Feature 15: Real-Time Incremental Token Streaming with In-Flight JSON Parsing](#feature-15-real-time-incremental-token-streaming-with-in-flight-json-parsing)
- [Feature 16: Traditional Knowledge Digital Library (TKDL) Prior-Art Defense & Historical Biopiracy Precedents](#feature-16-traditional-knowledge-digital-library-tkdl-prior-art-defense--historical-biopiracy-precedents)
- [Feature 17: Access & Benefit Sharing (ABS) Decision Flow & National Biodiversity Authority (NBA) Compliance Wizard](#feature-17-access--benefit-sharing-abs-decision-flow--national-biodiversity-authority-nba-compliance-wizard)
- [Feature 18: Plain-Language / Simplified Legal Explanation Register](#feature-18-plain-language--simplified-legal-explanation-register)
- [Known Limitations & Post-Hackathon Roadmap](#known-limitations--post-hackathon-roadmap)

---

## Architectural Overview

```
[User Interface (Next.js 16 + Tailwind CSS)]
  │
  ├── Jurisdiction Selector (National [IN] / Global [Treaties])
  ├── Interactive Formulation Classification Cards
  ├── Real-time SSE Token Stream Renderer with Live Pipeline Milestone Indicators
  ├── In-App Statutory PDF Viewer (Inline Tabs)
  ├── Plain-Language "Simplify" Explanation Toggle
  ├── Interactive TKDL Defense Cards (Turmeric & Neem Biopiracy Case Studies)
  ├── ABS Compliance Decision Wizard (BDA 2002 / 2023 Amendment)
  └── User Feedback (Thumbs Up/Down + Diagnostic Categorization)
        │
        ▼ HTTP REST / SSE (/ask, /ask/stream, /simplify, /pdf/*, /feedback, /admin/audit)
[FastAPI Application Backend (Uvicorn / Python 3.12)]
  │
  ├── Multi-Turn Memory Contextualizer (Sliding Window + SQLite)
  ├── Multilingual Router (Bhashini NMT + LLM Preserving English Citations)
  ├── Gated Formulation Decision Tree (D&C Act / Patents Act Rules)
  ├── TKDL Prior-Art Rule Engine (IPC A61K 36/00 Concordance)
  ├── ABS Statutory Decision Tree (NBA Form 1/2/3/4 + SBB State Exemptions)
  │
  ├── [Hybrid Legal Retrieval Engine]
  │     ├── Dense Semantic Search (BAAI/bge-m3, FP16 on CUDA / Qdrant HNSW)
  │     ├── Sparse Lexical Index (Custom Okapi BM25 + Gzip Disk Cache)
  │     ├── Reciprocal Rank Fusion (RRF k=60)
  │     └── Cross-Encoder Reranking (BAAI/bge-reranker-v2-m3, FP16 CUDA)
  │
  ├── Multi-Tier High-Availability LLM Client:
  │     ├── Groq Tier 1: openai/gpt-oss-120b
  │     ├── Groq Tier 2: openai/gpt-oss-20b
  │     ├── Groq Tier 3: qwen/qwen3.6-27b
  │     ├── Mistral Tier 4: mistral-small-latest
  │     └── Tier 5: Local Statutory Fallback (Verified Corpus Citations)
  └── Minimal Audit & Session Persistence (SQLite WAL + Append-Only CSV / DPDP Aligned)
```

---

## Feature 1: Citation-Grounded RAG Core (Hybrid Dense + BM25 + RRF + Cross-Encoder)

### 1. What It Is
A hybrid two-stage statutory retrieval and reranking pipeline combining dense semantic vector embeddings (`BAAI/bge-m3`), an in-memory sparse keyword index (Okapi BM25), Reciprocal Rank Fusion (RRF, $k=60$), and a neural Cross-Encoder reranker (`BAAI/bge-reranker-v2-m3`) with hardware-accelerated FP16 inference.

### 2. Why It Was Built
General-purpose dense vector search fails on statutory legal inquiries because legal language hinges on precise alphanumeric subclauses (e.g., Section 3(p), Section 2(1)(ja), Rule 158-B) that semantic embeddings alone frequently dilute. Conversely, pure keyword search fails on paraphrased practitioner inquiries (e.g., *"Can I protect a classical recipe passed down from my grandmother?"*). The problem statement demands high citation fidelity and zero hallucination across 17 distinct acts and treaties.

### 3. How It Works
1. **Query Processing**: The incoming query undergoes legal normalization and statutory synonym expansion (e.g., mapping *"inventive step"* to *"Section 2(1)(ja)"*).
2. **Dual-Path Retrieval**:
   - Dense path: Generates 1024-dimensional dense embeddings via `BAAI/bge-m3` running in FP16 on CUDA, querying Qdrant with hard metadata filters on `jurisdiction`.
   - Sparse path: Queries an in-memory Okapi BM25 index tokenized with custom legal regexes matching nested subclauses, articles, and rules.
3. **Reciprocal Rank Fusion**: Merges candidates from both streams using $RRF(d) = \sum \frac{1}{60 + r(d)}$.
4. **Cross-Encoder Neural Reranker**: Formats query-document pairs (`[query, title + prefix + section + text]`) and reranks the top 12 candidates via `bge-reranker-v2-m3` in FP16 batches with sigmoid relevance calibration.

### 4. Verification Status: Fully Verified
- **Benchmark Suite**: [`eval/production_readiness_benchmark.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/production_readiness_benchmark.py) & [`eval/optimized_production_benchmark_results.json`](file:///c:/Users/Vishal/Desktop/SIH/eval/optimized_production_benchmark_results.json)
- **Key Verified Metrics** (32 statutory test queries across 14 legal domains on NVIDIA RTX 2050 GPU):
  - **Gold Recall@5**: **`87.5% (28/32)`** (vs. 53.1% FP32 baseline)
  - **Exact Section Recall@5**: **`93.8% (15/16)`**
  - **Paraphrased Query Recall@5**: **`81.2% (13/16)`**
  - **Mean Reciprocal Rank (MRR)**: **`0.7250`** (vs. 0.4477 baseline)
  - **End-to-End Retrieval Latency**: **`303.3 ms`** average (reduced from 85,000 ms; **280.3x speedup**)
  - **Duplicate Chunks in Top-5**: **`0`**

### 5. Known Limitations
- While recall is 100% across Patents, Biodiversity/ABS, Nagoya, TRIPS, Trade Marks, and GI, domain Recall@5 for complex AYUSH Drug Rules (D&C Rules 151–170) is 50.0% due to extremely dense, multi-page tabular licensing schedules.

---

## Feature 2: Exact-Citation Lookup & Query Normalization Layer

### 1. What It Is
A deterministic legal tokenization and regex-based statutory query expansion layer that detects explicit legal citations in user prompts and ensures exact section-level matches receive top retrieval priority.

### 2. Why It Was Built
Legal researchers and patent attorneys frequently query specific statutory provisions directly (e.g., *"What does Section 3(p) prohibit?"*, *"Rule 158-B licensing"*, *"Article 27 TRIPS"*). Pure semantic vector embeddings frequently rank adjacent sections or preambles above the exact target clause.

### 3. How It Works
- Implemented in [`app/retrieval/query_expansion.py`](file:///c:/Users/Vishal/Desktop/SIH/app/retrieval/query_expansion.py) and [`app/retrieval/bm25.py`](file:///c:/Users/Vishal/Desktop/SIH/app/retrieval/bm25.py).
- Normalizes canonical statutory prefixes: *"Sec 3(d)"* -> *"Section 3(d)"*, *"R. 158B"* -> *"Rule 158-B"*, *"Art. 27"* -> *"Article 27"*.
- Matches traditional knowledge and classical formulation intents (e.g., *"polyherbal"*, *"Triphala"*, *"Chyawanprash"*, *"rasayana"*, *"ancestral recipe"*) and injects Section 3(p) and Section 3(e) statutory terms directly into sparse and dense query representations.

---

## Feature 3: Formulation Classification Flow (6-Way Conversational Decision Tree)

### 1. What It Is
A deterministic regulatory decision tree that categorizes Ayurvedic products into one of 6 legally recognized statutory classes under the **Drugs and Cosmetics Act, 1940**, **D&C Rules, 1945**, and the **Patents Act, 1970**:
1. `classical_medicine`: Formulations strictly following authoritative First Schedule texts (e.g., *Charaka Samhita*, *Sushruta Samhita*, *Ayurvedic Formulary of India*).
2. `proprietary_patent`: Novel combinations or modified extracts requiring safety/efficacy clinical validation under Rule 158-B.
3. `patent_synergistic_extract`: Standardized active fractions demonstrating surprising synergistic efficacy over known prior art (Section 3(d)/3(p) hurdle).
4. `ayurveda_aahara`: Food products containing traditional ingredients regulated under FSSAI Regulations 2022.
5. `cosmetic_herbal`: Topical aesthetic preparations regulated under D&C Part XVI (Cosmetics Rules).
6. `traditional_knowledge_pure`: Pure ancestral remedies preserved in the public domain and indexed in the TKDL.

### 2. Why It Was Built
Ayurvedic entrepreneurs frequently confuse drug licensing under the D&C Act with patent protection under the Patents Act. Asking a flat question without determining the formulation's statutory classification leads to invalid regulatory guidance.

### 3. How It Works
- Implemented in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L900-L980).
- When a user indicates formulation development intent (e.g., *"I have a new herbal formulation"*), the engine returns `needs_classification: true` and presents interactive decision cards in the frontend.
- When the query is an explicit patentability inquiry (e.g., *"Is Triphala patentable?"*), the gating bypasses the questionnaire and answers directly with Section 3(p) statutory exclusions.

---

## Feature 4: Strict Jurisdiction Separation (National vs. International Filtering)

### 1. What It Is
Hard metadata filtering at both the dense vector database level and sparse lexical index level that completely isolates **National (Indian) Law** from **International Treaties & Agreements**.

### 2. Why It Was Built
Indian IP law possesses unique statutory exclusions (e.g., Section 3(p) on Traditional Knowledge, Section 3(d) on Enhanced Efficacy) that do not exist in foreign jurisdictions or multilateral treaties (TRIPS Article 27). Mixing national and international statutes causes conflicting legal guidance.

### 3. How It Works
- Managed via `jurisdiction` query parameter (`national` | `international`).
- Dense retrieval: Qdrant payload filter `{"key": "jurisdiction", "match": {"value": target_jurisdiction}}`.
- Sparse retrieval: Separate BM25 inverted indexes partitioned in memory by jurisdiction.
- Compare Mode: The UI supports side-by-side comparative inspection (`GET /compare`), executing parallel National and International pipelines and highlighting overlapping treaty principles.

---

## Feature 5: Multi-Turn Conversational Memory & Contextual Query Reformulation

### 1. What It Is
A session-aware conversational memory layer that maintains context across multi-turn consultations, resolving anaphora and implicit pronouns (e.g., *"What about its export requirements?"* following a query on *Triphala*).

### 2. Why It Was Built
Practitioners conduct exploratory dialogues where follow-up questions omit the formulation name or previous statutory citations.

### 3. How It Works
- Implemented in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py) with SQLite-backed session storage.
- Appends the last 4 conversation turns to the prompt context.
- Translates follow-up inquiries while maintaining previous legal anchors and active classification badges.

---

## Feature 6: Out-of-Scope Abstention Guardrail & Facilitator Escalation

### 1. What It Is
A hard retrieval guardrail that detects when an inquiry falls completely outside verified statutory provisions, refusing to speculate and advising escalation to the human IP Facilitation Cell.

### 2. Why It Was Built
In high-stakes legal and patent domains, an AI that hallucinates legal precedents causes severe regulatory liability.

### 3. How It Works
- If `retrieve()` returns zero matching chunks from Qdrant and BM25, or if Cross-Encoder scores fail minimum relevance thresholds, the system short-circuits before invoking the LLM.
- Emits a standardized abstention payload with `abstained: true`, `confidence: "low"`, and `citations: []`.

---

## Feature 7: Multi-Provider High-Availability LLM Client (Multi-Tier Groq Candidate Failover + Mistral Fallback)

### 1. What It Is
An enterprise-grade, multi-tier LLM client that routes inference through a prioritized cascade of high-performance models, automatically recovering from rate limits (HTTP 429), token exhaustion, or service outages.

### 2. Why It Was Built
Free and standard tier cloud LLMs impose strict Requests-Per-Minute (RPM) and Tokens-Per-Day (TPD) quotas. During high-concurrency evaluation bursts or hackathon demonstrations, hitting a 429 error would break the application.

### 3. How It Works
- Implemented in [`app/llm/client.py`](file:///c:/Users/Vishal/Desktop/SIH/app/llm/client.py).
- **Cascade Hierarchy**:
  1. **Groq Primary**: `openai/gpt-oss-120b`
  2. **Groq Failover 1**: `openai/gpt-oss-20b` (separate token rate limit pool)
  3. **Groq Failover 2**: `qwen/qwen3.6-27b`
  4. **Mistral Secondary**: `mistral-small-latest`
  5. **Deterministic Fallback**: Local verified statutory citations delivered with zero API dependency.
- Operates identically for both synchronous (`get_completion`) and streaming (`stream_completion`) modes.

---

## Feature 8: Curated 17-Statute Corpus, Layout-Aware Chunking & Manifest Integrity

### 1. What It Is
A curated regulatory repository of 17 authoritative Indian Acts, Rules, Regulations, and International Treaties, ingested using layout-aware chunking strategies and tracked via a version-controlled manifest with cryptographic file hashing.

### 2. Why It Was Built
Unstructured PDF chunking with naive character splitters breaks legal sections across chunk boundaries, separating subclauses from their parent sections.

### 3. How It Works
- Configured in [`data/manifest.csv`](file:///c:/Users/Vishal/Desktop/SIH/data/manifest.csv) and ingested via [`app/ingestion/chunk.py`](file:///c:/Users/Vishal/Desktop/SIH/app/ingestion/chunk.py).
- Employs dedicated chunking strategies per document type:
  - `section`: Regex parsing of statutory sections (Patents Act, BDA, TM Act, Copyright Act, GI Act, Designs Act).
  - `rule`: Hierarchy extraction of D&C Rules, BD Rules 2024, and BD Amendment Rules 2025.
  - `article`: Multilateral treaty article parsing (TRIPS, CBD, Nagoya Protocol, WIPO GRATK, PCT).
  - `regulation` / `heading`: Specialized extractors for FSSAI Ayurveda Aahara and IPC Phytopharmaceutical Guidance.
- **Corpus Size**: 2,621 clean, layout-aware statutory chunks indexed in Qdrant and BM25.

---

## Feature 9: Atomic In-Memory BM25 Startup Disk Cache

### 1. What It Is
A gzip-compressed, atomic disk serialization cache (`qdrant_data/bm25_cache.pkl.gz`) that stores the pre-tokenized Okapi BM25 index across all 2,621 statutory chunks for near-instantaneous server startup.

### 2. Why It Was Built
On cold startup, constructing the in-memory BM25 index from scratch consumed 3.5 seconds on every boot or test script run.

### 3. How It Works
- Implemented in [`app/retrieval/bm25.py`](file:///c:/Users/Vishal/Desktop/SIH/app/retrieval/bm25.py#L140-L195).
- Cold-start load time: **`120ms – 160ms`** (vs 3,450ms rebuild from database; **12.3x speedup**).
- Maintains exact mathematical score parity (`< 1e-5`) with live database builds.

---

## Feature 10: Direct Source Document PDF Citation Viewer

### 1. What It Is
An integrated document delivery service and frontend citation viewer that allows users to click on any statutory citation card to open the exact official PDF document in a new browser tab.

### 2. Why It Was Built
The problem statement requires facilitating access to authoritative sources so users can verify guidance directly against official legal records.

### 3. How It Works
- Backend route in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py): `@router.api_route("/pdf/{file_path:path}", methods=["GET", "HEAD"])`.
- Serves verified statutory PDFs with inline headers directly from `data/corpus/`.
- 100% of the 17 manifest statutory PDFs are verified accessible (200 OK).

---

## Feature 11: Multilingual Translation Layer & Digital India Bhashini Dhruva Architecture

### 1. What It Is
A multilingual language detection and translation subsystem designed to interface with the Government of India Digital India Bhashini Dhruva NMT pipeline, with an automated fallback legal translation pipeline that strictly preserves English statutory citations.

### 2. Why It Was Built
Ayurvedic practitioners across India interact in regional languages (Hindi, Tamil, Telugu, Marathi, Gujarati, etc.). Translating legal terminology without preserving canonical English Act names and section numbers breaks statutory authority.

### 3. How It Works
- Implemented in [`app/translation/bhashini.py`](file:///c:/Users/Vishal/Desktop/SIH/app/translation/bhashini.py) and [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py).
- Inbound query is translated to English for dense/sparse retrieval; answer is translated to the target regional language while retaining Act names and section numbers in English.

---

## Feature 12: SQLite-Backed Session Persistence & History Drawer

### 1. What It Is
An embedded transactional database store using SQLite in Write-Ahead Logging (WAL) mode that manages multi-turn consultation sessions, message histories, verified citation records, and conversation management in the frontend.

### 2. Why It Was Built
In-memory web sessions are lost on page refresh. Practitioners conducting regulatory reviews need to revisit prior consultations.

### 3. How It Works
- Implemented in [`app/db/session_store.py`](file:///c:/Users/Vishal/Desktop/SIH/app/db/session_store.py) (`data/ip_sakti.db`).
- REST endpoints: `GET /conversations`, `POST /conversations`, `GET /conversations/{id}`, `DELETE /conversations/{id}`.
- Frontend includes a slide-out drawer displaying past consultations with one-click resumption and cascade deletion.

---

## Feature 13: DPDP-Aligned Minimal Regulatory Audit Trail & Administrative Dashboard

### 1. What It Is
A foundational audit logging subsystem aligned with the data minimization mandates of India's **Digital Personal Data Protection (DPDP) Act, 2023**, persisting query/response metadata to append-only logs (`data/audit_log.csv` and SQLite) and exposing a read-only admin inspection dashboard.

### 2. Why It Was Built
Regulators and compliance officers must be able to audit AI responses, verify citation provenance, and track SLA latency without harvesting user personal data.

### 3. How It Works
- Implemented in [`app/db/session_store.py`](file:///c:/Users/Vishal/Desktop/SIH/app/db/session_store.py) and [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py).
- **Zero PII**: Strictly records no IP addresses, device fingerprints, cookies, or personal identifiers.
- Admin views: `GET /admin/audit` (JSON) and `GET /admin/audit/view` (responsive HTML dashboard).

---

## Feature 14: Granular User Answer Feedback Mechanism (Thumbs Up/Down + Diagnostic Tagging)

### 1. What It Is
A lightweight feedback collection mechanism beneath every assistant response allowing practitioners to submit thumbs-up or thumbs-down ratings, with an optional non-blocking diagnostic feedback drawer on negative ratings.

### 2. Why It Was Built
To establish an active signal for continuous legal RAG improvement and evaluation.

### 3. How It Works
- Implemented in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L980-L1050) and [`frontend/app/page.tsx`](file:///c:/Users/Vishal/Desktop/SIH/frontend/app/page.tsx).
- `POST /feedback` accepts ratings and diagnostic tags (*"Wrong jurisdiction"*, *"Missing citation"*, *"Confusing answer"*), appending to `data/feedback_log.csv` and SQLite.

---

## Feature 15: Real-Time Incremental Token Streaming with In-Flight JSON Parsing

### 1. What It Is
An asynchronous token extraction pipeline that parses structured JSON tokens from LLMs in real time as they arrive over Server-Sent Events (SSE), delivering an incremental typing experience in the frontend while preserving strict JSON schema validation.

### 2. Why It Was Built
Standard LLM JSON mode requires buffering the entire completion before parsing and rendering, causing a 3,000ms delay. Users perceive the application as unresponsive during long legal syntheses.

### 3. How It Works
- Implemented via `IncrementalAnswerExtractor` in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L52-L115).
- Filters out `<think>...</think>` reasoning tokens and markdown fences (` ```json `).
- Scans inbound tokens for the `"answer": "` key, decoding JSON escape sequences (`\n`, `\"`, `\\`) on the fly.
- Emits real-time SSE deltas (`{'stage': 'llm_token', 'answer_delta': delta}`).
- Frontend displays an animated milestone indicator (`[⟳ Searching national statutory corpus & treaties...]`) inside the chat bubble during retrieval, transitioning seamlessly into word-by-word typing.

---

## Feature 16: Traditional Knowledge Digital Library (TKDL) Prior-Art Defense & Historical Biopiracy Precedents

### 1. What It Is
An automated traditional knowledge defensive disclosure module that detects classical Ayurvedic formulations and traditional remedies, citing **Section 3(p) of the Patents Act, 1970**, mapping **IPC Classification `A61K 36/00` (Medicinal Preparations of Plant Origin)**, and providing interactive historical case studies on the landmark **Turmeric (US Patent 5,401,504)** and **Neem (EP 436257)** biopiracy revocations.

### 2. Why It Was Built
Traditional Ayurvedic knowledge is part of the Indian public domain. Unscrupulous applicants or foreign entities historically attempted to patent classical uses of turmeric (wound healing) and neem (fungicidal properties). Educating researchers and applicants on how TKDL acts as prior art to block biopiracy is a key objective of Indian IP policy.

### 3. How It Works
- Implemented in [`app/compliance/tkdl_helper.py`](file:///c:/Users/Vishal/Desktop/SIH/app/compliance/tkdl_helper.py) and [`frontend/components/TKDLPriorArtCard.tsx`](file:///c:/Users/Vishal/Desktop/SIH/frontend/components/TKDLPriorArtCard.tsx).
- When a query touches classical formulations (e.g., Triphala, Chyawanprash, turmeric, neem, grandmother recipes), `build_tkdl_prior_art_pointer()` triggers.
- Generates structured guidance:
  1. **Statutory Exclusion**: Why Section 3(p) & 3(e) exclude the formulation.
  2. **Examination Standard**: How patent examiners cross-reference TKDL to issue First Examination Report (FER) objections.
  3. **Legal Standard to Overcome**: Requirement for experimental demonstration of surprising synergy.
  4. **Interactive Historical Precedent Cards**: Detailed summaries of the US Turmeric and EPO Neem patent revocations led by CSIR.

---

## Feature 17: Access & Benefit Sharing (ABS) Decision Flow & National Biodiversity Authority (NBA) Compliance Wizard

### 1. What It Is
An interactive, multi-step regulatory compliance engine for the **Biological Diversity Act, 2002**, the **Biological Diversity (Amendment) Act, 2023**, the **Biological Diversity Rules, 2024**, and the **Biological Diversity (Amendment) Rules, 2025**.

### 2. Why It Was Built
Any commercial utilization of Indian biological resources or application for intellectual property based on Indian bio-resources requires prior statutory approval from the National Biodiversity Authority (NBA) or State Biodiversity Boards (SBB). Non-compliance carries severe penal consequences under Section 55 of the BDA.

### 3. How It Works
- Implemented in [`app/compliance/abs_helper.py`](file:///c:/Users/Vishal/Desktop/SIH/app/compliance/abs_helper.py).
- Evaluates four key statutory criteria:
  1. **Applicant Entity Status**: Non-Indian/Foreign entity (Section 3(2)) vs. Indian citizen/entity (Section 7).
  2. **Activity Type**: Commercial utilization, research, biosurvey, or IP application.
  3. **Statutory Approvals**:
     - **Form 1**: Access to biological resources by foreign entities (Section 3).
     - **Form 2**: Transfer of research results (Section 4).
     - **Form 3**: Prior approval before patent grant (Section 6).
     - **Form 4**: Third-party transfer of accessed resources (Section 20).
  4. **AYUSH Statutory Exemptions**: Detects exemptions introduced under the 2023 Amendment for registered AYUSH practitioners and codified traditional knowledge.

---

## Feature 18: Plain-Language / Simplified Legal Explanation Register

### 1. What It Is
A dedicated legal register simplification engine (`POST /simplify`) that transforms complex statutory explanations into clear, jargon-free guidance for rural entrepreneurs, non-lawyers, and traditional Vaidyas.

### 2. Why It Was Built
Legal citations and statutory phrasing (e.g., *"mere admixture resulting only in aggregation of properties"*, *"inventive step under section 2(1)(ja)"*) are difficult for grassroots Ayurvedic practitioners to understand.

### 3. How It Works
- Implemented via the `/simplify` endpoint in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L1060-L1120).
- Accepts the original legal answer and rewrites it in plain language using everyday metaphors while strictly maintaining legal accuracy and keeping original citations attached.
- Frontend includes an interactive toggle badge (`Plain-Language Explanation (Simplified Register)`) with emerald styling.

---

## Known Limitations & Post-Hackathon Roadmap

The following table explicitly outlines architectural boundaries, trade-offs, and staged capabilities deferred in accordance with the problem statement's guidance:

| Area / Feature | Current Hackathon Implementation Status | Post-Hackathon Enterprise Roadmap |
| :--- | :--- | :--- |
| **Classification Trigger Gate** | Uses keyword and possessive intent indicators (`is_formulation_specific_query`). Inquiries without personal intent pronouns bypass the 6-question questionnaire. | Implement an intent classification sub-model or dual-pass routing to detect formulation inquiries regardless of phrasing. |
| **Bhashini Sovereign API** | Complete Dhruva NMT client implemented and unit-tested; daily runtime operates on Groq/Mistral legal translation fallback due to credential availability. | Plug in verified MeitY Bhashini enterprise credentials for sovereign on-premise government cloud deployment. |
| **Knowledge Graph (KG) Layer** | Staged-build guidance deferred formal KG construction to avoid brittle graph extraction on hackathon timelines; relies on dense + BM25 hybrid indexing. | Construct a Neo4j / NetworkX legal knowledge graph mapping relationships between classical texts (Charaka Samhita), botanical taxa, modern active compounds, and patent claims. |
| **Enterprise DPDP Security** | Foundational audit logging with data minimization, no PII, append-only files, and read-only admin dashboards. | Implement AES-256 encryption at rest for SQLite/CSV logs, cryptographically enforced RBAC (OAuth2/OIDC), and automated 180-day retention expunction crons. |
| **Commercial Patent Registry Connectors** | Strictly scoped to 17 verified official open-access statutes, guidelines, and multilateral treaties. | Build authenticated connectors to commercial patent databases (Derwent, Orbit, IP India InPASS, EPO Espacenet). |
| **Multi-Agent Deliberation** | Single pipeline with multi-tier Groq candidates and zero-backoff Mistral fallback. | Introduce multi-agent deliberation (e.g., Patent Examiner Agent vs. Applicant Advocate Agent) for contested Section 3(d)/3(p) borderline cases. |
| **Multimodal / Voice Interface** | Text-based multilingual chat interface with direct PDF document viewer. | Add ASR (Automatic Speech Recognition) and TTS (Text-to-Speech) using Bhashini speech pipelines for voice interaction by non-literate field practitioners. |

---

*Document compiled from active codebase implementations, test trajectories, and benchmark evaluations in `Vixhal17/SIH`.*
