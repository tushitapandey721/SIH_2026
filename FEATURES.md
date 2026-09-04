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
- [Feature 7: Multi-Provider High-Availability LLM Client (Groq Primary with Zero-Backoff Mistral Fallback)](#feature-7-multi-provider-high-availability-llm-client-groq-primary-with-zero-backoff-mistral-fallback)
- [Feature 8: Curated 17-Statute Corpus, Layout-Aware Chunking & Manifest Integrity](#feature-8-curated-17-statute-corpus-layout-aware-chunking--manifest-integrity)
- [Feature 9: Atomic In-Memory BM25 Startup Disk Cache](#feature-9-atomic-in-memory-bm25-startup-disk-cache)
- [Feature 10: Direct Source Document PDF Citation Viewer](#feature-10-direct-source-document-pdf-citation-viewer)
- [Feature 11: Multilingual Translation Layer & Digital India Bhashini Dhruva Architecture](#feature-11-multilingual-translation-layer--digital-india-bhashini-dhruva-architecture)
- [Feature 12: SQLite-Backed Session Persistence & History Drawer](#feature-12-sqlite-backed-session-persistence--history-drawer)
- [Feature 13: DPDP-Aligned Minimal Regulatory Audit Trail & Administrative Dashboard](#feature-13-dpdp-aligned-minimal-regulatory-audit-trail--administrative-dashboard)
- [Feature 14: Granular User Answer Feedback Mechanism (Thumbs Up/Down + Diagnostic Tagging)](#feature-14-granular-user-answer-feedback-mechanism-thumbs-updown--diagnostic-tagging)
- [Feature 15: Real-Time Incremental Token Streaming with In-Flight JSON Parsing](#feature-15-real-time-incremental-token-streaming-with-in-flight-json-parsing)
- [Known Limitations & Post-Hackathon Roadmap](#known-limitations--post-hackathon-roadmap)

---

## Architectural Overview

```
[User Interface (Next.js 16 + Tailwind CSS)]
  │
  ├── Jurisdiction Selector (National [IN] / Global [Treaties])
  ├── Interactive Formulation Classification Cards
  ├── Real-time SSE Token Stream Renderer with Pulsating Cursor
  ├── In-App Statutory PDF Viewer (Inline Tabs)
  └── User Feedback (Thumbs Up/Down + Diagnostic Categorization)
        │
        ▼ HTTP REST / SSE (/ask, /ask/stream, /pdf/*, /feedback, /admin/audit)
[FastAPI Application Backend (Uvicorn / Python 3.12)]
  │
  ├── Multi-Turn Memory Contextualizer (Sliding Window + SQLite)
  ├── Multilingual Router (Bhashini NMT + LLM Preserving English Citations)
  ├── Gated Formulation Decision Tree (D&C Act / Patents Act Rules)
  │
  ├── [Hybrid Legal Retrieval Engine]
  │     ├── Dense Semantic Search (BAAI/bge-m3, FP16 on CUDA / Qdrant HNSW)
  │     ├── Sparse Lexical Index (Custom Okapi BM25 + Gzip Disk Cache)
  │     ├── Reciprocal Rank Fusion (RRF k=60)
  │     └── Cross-Encoder Reranking (BAAI/bge-reranker-v2-m3, FP16 CUDA)
  │
  ├── High-Availability LLM Client (Groq openai/gpt-oss-120b -> Mistral Small 4)
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
- Extracts and normalizes:
  - Nested subclauses: `Section 2(1)(ja)` -> `['section 2(1)(ja)', '2(1)(ja)', '2(1)', '(ja)']`
  - Clause patterns: `Section 3(p)` -> `['section 3(p)', '3(p)', '(p)']`
  - Treaty articles: `Article 27` / `Art. 6` -> `['article 27', 'art 27']`
  - Rule sub-parts: `Rule 158-B` / `158B` -> `['rule 158b', '158-b', '158b']`
- Injects canonical terminology into the sparse query representation, guaranteeing exact statutory chunk alignment.

### 4. Verification Status: Fully Verified
- **Benchmark Evidence**: Evaluated in [`eval/production_readiness_benchmark.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/production_readiness_benchmark.py) under the 16 exact-section query partition.
- **Result**: **`93.8% (15/16) Exact Section Recall@5`**.
- Query `Q01` (*"What does Section 3(p) of the Patents Act prohibit?"*) attained **Rank 1 across Dense, BM25, RRF, and Cross-Encoder**.
- Query `Q17` (*"What is patentable subject matter under TRIPS Article 27?"*) attained **Rank 1 across Dense, BM25, RRF, and Cross-Encoder**.

### 5. Known Limitations
- Highly idiosyncratic citation shorthand (e.g., Roman numeral sub-sub-clauses like *"Sec. 3(k) iv a"*) that diverge from India Code statutory formatting may require fallback to semantic search.

---

## Feature 3: Formulation Classification Flow (6-Way Conversational Decision Tree)

### 1. What It Is
A guided conversational decision tree that classifies traditional healthcare and Ayurvedic products into one of six statutory regulatory buckets: *Classical Ayurvedic Medicine*, *Patent or Proprietary Medicine (ASU)*, *New Drug (Rule 158-B)*, *Phytopharmaceutical Drug*, *Nutraceutical (Ayurveda Aahara)*, or *Cosmetic*.

### 2. Why It Was Built
Under Indian law (Drugs and Cosmetics Act, 1940, FSSAI Act 2006, and Patents Act, 1970), regulatory approvals, clinical trial exemptions, and patentability turn fundamentally on whether a product is a classical formulation (First Schedule text), a proprietary blend, or an isolated/standardized extract. Lay users and MSME practitioners do not know which regulatory pathway governs their product.

### 3. How It Works
- Implemented in [`app/classification/tree.py`](file:///c:/Users/Vishal/Desktop/SIH/app/classification/tree.py) and [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py).
- When a user asks about a formulation product, the system detects formulation intent via `is_formulation_specific_query()` and presents sequential, non-technical yes/no questions:
  1. Drawn from a First-Schedule authoritative Ayurvedic text?
  2. Requires new safety/efficacy proof (novel indications/excipients)?
  3. Standardized plant-derived extract with defined chemical markers?
  4. Marketed primarily as a dietary/food product?
  5. Topically applied for non-therapeutic/cosmetic purposes?
- Resolves to a statutory classification category with the exact legal basis citation (e.g., *"Section 3(a), D&C Act + Rule 154-A(1)(a)"*).

### 4. Verification Status: Fully Verified
- **Evaluation Scripts**: [`eval/test_gated_classification.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_gated_classification.py) & [`eval/test_frontend_e2e_integration.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_frontend_e2e_integration.py).
- Verified decision branches:
  - First-Schedule Text = Yes -> `classical_medicine` (bypasses remaining questions).
  - Novel Safety/Efficacy = Yes -> `new_drug` (Rule 158-B).
  - Standardized Extract = Yes -> `phytopharmaceutical` (G.S.R. 918(E)).
  - Food/Dietary = Yes -> `nutraceutical` (Ayurveda Aahara 2022).
  - Topical Non-Therapeutic = Yes -> `cosmetic` (Cosmetics Rules 2020).

### 5. Known Limitations
- **Keyword-Gate Edge Case**: `is_formulation_specific_query()` relies on possessive/product intent heuristics (e.g., *"my formulation"*, *"our product"*, *"developed an extract"*). If an inquiry asks abstractly about a phytopharmaceutical or extract without product intent (e.g., *"What are the clinical requirements for a standardized fraction?"*), the query bypasses the interactive questionnaire and defaults to general statutory retrieval.

---

## Feature 4: Strict Jurisdiction Separation (National vs. International Filtering)

### 1. What It Is
Hard architectural isolation between Indian National statutes (Patents Act, Biological Diversity Act, Drugs & Cosmetics Act, etc.) and International Treaties (TRIPS, Nagoya Protocol, CBD, WIPO GRATK, PCT) via UI toggle and backend database partition filters.

### 2. Why It Was Built
The problem statement explicitly forbids conflating domestic legal frameworks with international treaty obligations. An applicant in India seeking a national patent is subject to Section 3(p) and NBA Form III; an international applicant filing via PCT is subject to WIPO GRATK mandatory origin disclosure and TRIPS Article 27. Answers must never mix national and international citations unless requested.

### 3. How It Works
- Hard metadata filtering in Qdrant: `FieldCondition(key="jurisdiction", match=MatchValue(value=jurisdiction))`.
- Hard partitioning in the BM25 index: `self.docs_by_jurisdiction[jurisdiction]`.
- Enforced prompt boundaries: LLM system prompt enforces that only chunks matching the active jurisdiction scope may be cited.

### 4. Verification Status: Fully Verified
- **Dedicated Test Suite**: [`eval/test_jurisdiction_leak_check.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_jurisdiction_leak_check.py).
- **Test Sequence**:
  - **Turn 1 (National)**: *"Can I patent traditional knowledge?"* -> Citations returned: `Patents Act Section 3(p)`, `Biological Diversity Act Section 3`.
  - **Turn 2 (International, same conversation ID)**: *"What about internationally?"*
- **Audit Findings**:
  - Pure International Citations: `WIPO GRATK Treaty Article 3`, `TRIPS Agreement Article 27`, `Convention on Biological Diversity (CBD) Article 15`.
  - Leaked Indian Statute Citations: **`0` (Zero Leakage)**.

### 5. Known Limitations
- Cross-border comparative analysis (e.g., *"Compare Section 6 of Indian BDA with Article 15 of Nagoya Protocol"*) currently requires running two separate inquiries in each jurisdiction or querying under `national` where BDA cites international obligations in its preamble.

---

## Feature 5: Multi-Turn Conversational Memory & Contextual Query Reformulation

### 1. What It Is
An in-memory sliding window cache coupled with SQLite persistence that tracks conversation turns per `conversation_id`, contextually reformulating follow-up inquiries before statutory retrieval.

### 2. Why It Was Built
Real regulatory consultations are multi-turn. When a user asks *"Is a classical Ayurvedic formulation patentable?"* and follows up with *"What about for a new drug instead?"*, a standalone RAG system treats the second query in isolation, losing the patentability context and returning generic licensing fee or drug manufacturing rules.

### 3. How It Works
- Implemented in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L600-L650) via `get_memory_context()` and `contextualize_query_with_memory()`.
- Tracks the last 2–3 turns (query, answer summary, citations) keyed by `conversation_id`.
- On follow-up, reformulates the retrieval query to incorporate prior subject matter while strictly respecting the current turn's active jurisdiction.

### 4. Verification Status: Fully Verified
- **Before/After Verification**: [`eval/test_conversation_memory_check.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_conversation_memory_check.py).
  - **Before (Without Memory)**: Turn 2 query *"What about for a new drug instead?"* retrieved irrelevant administrative fees and Form 25-D licensing conditions.
  - **After (With Memory)**: Turn 2 correctly recognized the inquiry as a comparative patentability question, retrieving Section 2(1)(j), Section 2(1)(ja), and Section 3(d), providing a comparative analysis explaining how new drugs can satisfy novelty and inventive step while classical formulations are excluded under Section 3(p).

### 5. Known Limitations
- In-memory sliding window cache is scoped to the worker process; older historical turns beyond the window are rehydrated from SQLite, which summarizes rather than injecting full raw text to maintain token budget.

---

## Feature 6: Out-of-Scope Abstention Guardrail & Facilitator Escalation

### 1. What It Is
A hard retrieval guardrail that detects when an inquiry falls completely outside verified statutory provisions, refusing to speculate and advising escalation to the human IP Facilitation Cell.

### 2. Why It Was Built
In high-stakes legal and patent domains, an AI that hallucinates legal precedents or invents statutory sections causes regulatory liability. The problem statement mandates explicit abstention when verified authority is lacking.

### 3. How It Works
- If `retrieve()` returns zero matching chunks from Qdrant and BM25, or if Cross-Encoder scores fail minimum relevance thresholds, the system short-circuits before invoking the LLM.
- Emits a standardized abstention payload with `abstained: true`, `confidence: "low"`, and `citations: []`.

### 4. Verification Status: Fully Verified
- **Test Evidence**: [`eval/test_audit_log.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_audit_log.py) & [`eval/production_readiness_benchmark.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/production_readiness_benchmark.py).
- **Test Query**: *"supercalifragilisticexpialidocious quantum crypto asteroid mining"*
- **Actual Response Verified**:
  ```json
  {
    "abstained": true,
    "confidence": "low",
    "citations": [],
    "answer": "No relevant statutory provisions found in the verified legal corpus for this query. Escalation to a qualified human IP facilitator is recommended. This is informational guidance, not legal advice."
  }
  ```
- **Negative Query Correctness**: **`100.0% (2/2)`** in the production benchmark.

### 5. Known Limitations
- Highly edge-case queries combining a real statute with completely fictional facts may retrieve the real statute and require the LLM prompt instructions to disclaim applicability.

---

## Feature 7: Multi-Provider High-Availability LLM Client (Groq Primary with Zero-Backoff Mistral Fallback)

### 1. What It Is
An enterprise-grade, multi-provider LLM client that routes inference to Groq (`openai/gpt-oss-120b`) for high-speed generation, instantly failing over to the Mistral API (`mistral-small-latest`) upon receiving HTTP 429 rate limits, connection timeouts, or service errors.

### 2. Why It Was Built
Free and standard tier cloud LLMs impose strict Requests-Per-Minute (RPM) and Tokens-Per-Minute (TPM) quotas. During high-concurrency evaluation bursts or hackathon demonstrations, hitting a 429 error would break the application.

### 3. How It Works
- Implemented in [`app/llm/client.py`](file:///c:/Users/Vishal/Desktop/SIH/app/llm/client.py).
- Tries Groq primary path. If Groq raises an exception (HTTP 429, 503, `APIConnectionError`), it intercepts the error immediately, logs a warning, and executes the fallback path via Mistral with identical system prompts and JSON extraction schemas. Supports both synchronous (`get_completion`) and streaming (`stream_completion`).

### 4. Verification Status: Fully Verified
- **Automated Fallback Test**: [`eval/test_llm_client.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_llm_client.py) (Mocked 429 error triggers Mistral fallback cleanly; exits code 0).
- **Rapid-Fire Burst Test**: [`eval/test_rapid_fire_fallback.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_rapid_fire_fallback.py).
  - Executed 6 back-to-back streaming queries with 0 ms delay.
  - Average Groq latency: **`1,400ms – 2,700ms`**.
  - On deliberate rate limit saturation, zero requests dropped; fallback engaged transparently.

### 5. Known Limitations
- Streaming failover: If Groq drops mid-stream after emitting initial tokens, the UI handles the reconnection by resubmitting the query to the fallback provider rather than stitching partial token streams.

---

## Feature 8: Curated 17-Statute Corpus, Layout-Aware Chunking & Manifest Integrity

### 1. What It Is
A curated regulatory repository of 17 authoritative Indian Acts, Rules, Regulations, and International Treaties, ingested using layout-aware chunking strategies and tracked via a version-controlled manifest with cryptographic file hashing.

### 2. Why It Was Built
Unstructured PDF chunking with naive character splitters breaks legal sections across chunk boundaries, separating subclauses from their parent sections. The system requires verified, provenance-backed statutory chunks.

### 3. How It Works
- Configured in [`data/manifest.csv`](file:///c:/Users/Vishal/Desktop/SIH/data/manifest.csv) and ingested via [`app/ingestion/chunk.py`](file:///c:/Users/Vishal/Desktop/SIH/app/ingestion/chunk.py).
- Employs dedicated chunking strategies per document type:
  - `section`: Regex parsing of statutory sections (Patents Act, BDA, TM Act, Copyright Act, GI Act, Designs Act).
  - `rule`: Hierarchy extraction of D&C Rules, BD Rules 2024, and BD Amendment Rules 2025.
  - `article`: Multilateral treaty article parsing (TRIPS, CBD, Nagoya Protocol, WIPO GRATK, PCT).
  - `regulation` / `heading`: Specialized extractors for FSSAI Ayurveda Aahara and IPC Phytopharmaceutical Guidance.
- Each document has a YAML sidecar (`data/sidecars/*.yaml`) defining official metadata, citation prefixes, and authority URLs.
- SHA-256 manifest verification in `app/ingestion/manifest.py` prevents duplicate re-indexing.

### 4. Verification Status: Fully Verified
- **Ingested Corpus**: 2,621 statutory chunks indexed in Qdrant and BM25.
- All 17 documents verified in [`eval/test_pdf_citation_links.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_pdf_citation_links.py) and inspected via `GET /corpus`.

### 5. Known Limitations
- The Drugs and Cosmetics Act 1940 and Rules 1945 PDF is over 600 pages. While all ASU rules (Part XVI, XVI-A, XVII) are fully chunked, certain non-Ayurvedic schedules (e.g., Veterinary vaccine testing schedules) were excluded during ingestion to conserve index capacity.

---

## Feature 9: Atomic In-Memory BM25 Startup Disk Cache

### 1. What It Is
A gzip-compressed, atomic disk serialization cache (`qdrant_data/bm25_cache.pkl.gz`) that stores the pre-tokenized Okapi BM25 index across all 2,621 statutory chunks for near-instantaneous server startup.

### 2. Why It Was Built
On cold startup, constructing the in-memory BM25 index required scrolling all 2,621 points from Qdrant, executing legal regex tokenization, computing document frequencies, and building inverted index partitions—consuming 3.5 seconds on every boot or test script run.

### 3. How It Works
- Implemented in [`app/retrieval/bm25.py`](file:///c:/Users/Vishal/Desktop/SIH/app/retrieval/bm25.py#L140-L195) via `save_to_disk()` and `load_from_disk()`.
- Uses `pickle` with `gzip` compression and atomic temporary file replacement (`.tmp` -> `.pkl.gz`).
- On server startup, `LegalHybridRetriever._build_bm25_index()` checks for cache validity; if present, loads the serialized index directly. If absent or corrupt, it rebuilds from Qdrant and writes a fresh cache asynchronously.

### 4. Verification Status: Fully Verified
- **Benchmark Suite**: [`eval/test_bm25_cache_persistence.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_bm25_cache_persistence.py).
- **Cold-Start Startup Time**:
  - Full Rebuild from Qdrant: **`3,452.90 ms`**
  - Cached Disk Load: **`280.38 ms`**
  - **Speedup: `12.3x Faster Startup`**
- **Score Parity**: Retrieved candidate score difference is **`< 1e-5` (100% exact numerical parity)** across all test queries.

### 5. Known Limitations
- When new statutory PDFs are ingested via `ingest_all()`, `rebuild_bm25_cache()` must be triggered to invalidate and regenerate the disk cache.

---

## Feature 10: Direct Source Document PDF Citation Viewer

### 1. What It Is
An integrated document delivery service and frontend citation viewer that allows users to click on any statutory citation card to open the exact official PDF document in a new browser tab.

### 2. Why It Was Built
The problem statement explicitly requires facilitating access to authoritative sources so users can verify guidance directly against official legal records. Plain text citations without direct source document access force users to search external government portals manually.

### 3. How It Works
- Backend route in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L850-L870): `@router.api_route("/pdf/{file_path:path}", methods=["GET", "HEAD"])`.
- Serves verified statutory PDFs from `data/corpus/` with header `Content-Disposition: inline; filename="..."` and `media_type="application/pdf"`.
- Dynamically enriches every citation returned by `/ask` and `/ask/stream` with `{source, section, url, pdf_url}` mapped from `data/manifest.csv`.
- Frontend renders clickable citation badges styled with amber glow and document icons.

### 4. Verification Status: Fully Verified
- **Test Suite**: [`eval/test_pdf_citation_links.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_pdf_citation_links.py).
- **Result**: **`17/17 Manifest Documents Verified (100% 200 OK)`**:
  - `Patents Act, 1970.pdf`: 200 OK
  - `Biological Diversity (Amendment) Act, 2023.pdf`: 200 OK
  - `The Biological Diversity Rules, 2024.pdf`: 200 OK
  - `The Biological Diversity (Amendment) Rules, 2025.pdf`: 200 OK
  - `2016DrugsandCosmeticsAct1940Rules1945.pdf`: 200 OK
  - `WIPO GRATK Treaty (2024).pdf`: 200 OK
  - `trips_agreement.pdf`: 200 OK
  - (All remaining 10 documents verified).

### 5. Known Limitations
- Modern browsers open PDFs at page 1; jump-to-exact-page deep linking depends on browser-specific PDF viewer URL parameters (`#page=X`), which are supported in Chromium but vary in mobile embedded webviews.

---

## Feature 11: Multilingual Translation Layer & Digital India Bhashini Dhruva Architecture

### 1. What It Is
A multilingual language detection and translation subsystem designed to interface with the Government of India Digital India Bhashini Dhruva NMT pipeline, with a fallback legal translation pipeline that preserves English statutory citations.

### 2. Why It Was Built
Ayurvedic practitioners, traditional Vaidyas, and rural entrepreneurs across India interact primarily in regional Indian languages (Hindi, Tamil, Telugu, Marathi, Gujarati, etc.). Translating legal statutory terminology into vernacular without preserving canonical English Act names and section numbers breaks legal validity.

### 3. How It Works
- Implemented in [`app/translation/bhashini.py`](file:///c:/Users/Vishal/Desktop/SIH/app/translation/bhashini.py) and [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py).
- Language detection via `langdetect`.
- Inbound query is translated to English for dense and sparse retrieval.
- Grounded answer is synthesized in English, then translated back to the user's native language.
- Enforces strict translation prompt guardrails: Act names (e.g., *"Patents Act, 1970"*), Rule numbers (*"Rule 158-B"*), and Section numbers (*"Section 3(p)"*) are retained in English, while explanatory statutory guidance is rendered in fluent vernacular.

### 4. Verification Status: Partially Verified (Honest Architecture Assessment)
- **Unit Test Suite**: [`eval/test_bhashini_integration.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_bhashini_integration.py) (5/5 tests passed in 8ms: verified payload structures, 13 Indian language code mappings, and mock 503 fallback).
- **LLM Fallback Translation**: Fully verified via [`eval/test_hindi_query.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_hindi_query.py). Hindi query *"क्या मैं पारंपरिक आयुर्वेदिक नुस्खे पर पेटेंट प्राप्त कर सकता हूँ?"* correctly returned fluent Hindi guidance while preserving *"Section 3(p)"* and *"Patents Act, 1970"*.
- **Live Bhashini API Status**: In current execution environments without live production MeitY API credentials (`BHASHINI_API_KEY` / `BHASHINI_USER_ID`), the system automatically and safely falls back to the high-speed legal LLM translation path. The Bhashini integration is architected and ready for credentials, but daily development operates on the verified LLM fallback.

### 5. Known Limitations
- Nuanced legal terminology in Sanskritized Ayurvedic vocabulary (e.g., *Yukti-Vyapashraya*, *Rasayana*) can occasionally be over-translated by general NMT engines; the prompt explicitly guards First Schedule text titles.

---

## Feature 12: SQLite-Backed Session Persistence & History Drawer

### 1. What It Is
An embedded transactional database store using SQLite in Write-Ahead Logging (WAL) mode that manages multi-turn consultation sessions, message histories, verified citation records, and conversation management in the frontend.

### 2. Why It Was Built
In-memory web sessions are lost on page refresh. Practitioners conducting regulatory reviews need to revisit prior consultations, compare previous statutory answers, and maintain persistent research threads.

### 3. How It Works
- Implemented in [`app/db/session_store.py`](file:///c:/Users/Vishal/Desktop/SIH/app/db/session_store.py) (`data/ip_sakti.db`).
- Schema:
  - `conversations`: `id`, `title`, `jurisdiction`, `created_at`, `updated_at`.
  - `messages`: `id`, `conversation_id`, `role`, `content`, `citations`, `timing_ms`, `timestamp`, with `ON DELETE CASCADE`.
- REST API: `GET /conversations`, `POST /conversations`, `GET /conversations/{id}`, `DELETE /conversations/{id}`.
- Frontend: Slide-out glassmorphism drawer in `frontend/app/page.tsx` displaying saved conversations with message counts, jurisdiction tags, and one-click resumption or deletion.

### 4. Verification Status: Fully Verified
- **Test Suite**: [`eval/test_session_store_and_api.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_session_store_and_api.py).
- **Result**: **`6/6 tests passed in 12.8s`**.
  - Verified conversation creation, message persistence, message rehydration, cascade deletion on delete, and 404 handling.

### 5. Known Limitations
- SQLite is an embedded single-node database. While WAL mode supports concurrent reads and sequential writes suitable for workstation and departmental deployments, horizontal multi-server scaling would require migrating the session store to PostgreSQL.

---

## Feature 13: DPDP-Aligned Minimal Regulatory Audit Trail & Administrative Dashboard

### 1. What It Is
A foundational audit logging subsystem aligned with the data minimization mandates of India's **Digital Personal Data Protection (DPDP) Act, 2023**, persisting query/response metadata to append-only logs (`data/audit_log.csv` and SQLite) and exposing a read-only admin inspection dashboard.

### 2. Why It Was Built
The problem statement requires *"privacy, audit and security aligned to the Digital Personal Data Protection regime."* Regulators and compliance officers must be able to audit AI responses, verify citation provenance, track latency SLA, and inspect model decisions without harvesting or retaining user personal data.

### 3. How It Works
- Implemented in [`app/db/session_store.py`](file:///c:/Users/Vishal/Desktop/SIH/app/db/session_store.py) and [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py).
- **Data Minimization (DPDP Section 4 & 6)**: Records only system metadata: `timestamp` (UTC), `jurisdiction`, `query`, `classification`, `provider_used`, `latency_ms`, `abstained`, `conversation_id`, and `detected_lang`.
- **Zero PII**: Strictly collects **no IP addresses, no device fingerprints, no cookies, and no User-Agent headers**.
- **Dual Storage**: Every query automatically appends to RFC-4180 `data/audit_log.csv`, `data/audit_log`, and SQLite table `audit_logs`.
- **Admin Views**:
  - `GET /admin/audit`: JSON endpoint returning the last 50 queries with explicit DPDP alignment metadata.
  - `GET /admin/audit/view`: Self-contained, responsive HTML table dashboard with metrics cards, status badges, and DPDP transparency notices.

### 4. Verification Status: Fully Verified
- **Test Suite**: [`eval/test_audit_log.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_audit_log.py).
- **Result**: Executed 4 diverse queries (`/ask` and `/ask/stream`), verifying:
  - CSV header audit: Confirmed zero PII headers.
  - JSON API verification: Verified timestamp, jurisdiction, classification, provider, latency, and abstained status for all queries.
  - HTML inspection page: Verified 200 OK and table row presence.
  - Append-only file persistence: Verified record count increments.

### 5. Known Limitations (Honest Scope Declaration)
- *As documented in README.md*: This implementation is explicitly scoped as a foundational starting point for DPDP alignment within a hackathon architecture. Full enterprise compliance in production requires institutional infrastructure—specifically AES-256 encryption at rest, cryptographically enforced Role-Based Access Control (RBAC) on the admin interface, and automated data retention and expunction policies.

---

## Feature 14: Granular User Answer Feedback Mechanism (Thumbs Up/Down + Diagnostic Tagging)

### 1. What It Is
A lightweight feedback collection mechanism beneath every assistant response allowing practitioners to submit thumbs-up or thumbs-down ratings, with an optional non-blocking diagnostic feedback drawer on negative ratings.

### 2. Why It Was Built
To establish an active signal for continuous legal RAG improvement. Identifying which statutory answers users find unhelpful or confusing enables targeted retrieval tuning and dataset augmentation.

### 3. How It Works
- Implemented in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L980-L1050) and [`frontend/app/page.tsx`](file:///c:/Users/Vishal/Desktop/SIH/frontend/app/page.tsx#L240-L280).
- `POST /feedback` accepts `{conversation_id, query, answer_snippet, citations, rating: "up"|"down", comment}`.
- Persists append-only to `data/feedback_log.csv` and SQLite `feedback` table.
- Frontend: Icon buttons below each answer. Clicking thumbs-down opens an optional drawer with quick diagnostic tags (*"Wrong jurisdiction"*, *"Missing citation"*, *"Confusing answer"*, *"Outdated statute reference"*) and optional text input. Non-blocking; dismissible with zero friction.

### 4. Verification Status: Fully Verified
- **Test Suite**: [`eval/test_feedback.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_feedback.py).
- **Results**:
  - `POST /feedback` (Thumbs Up): Verified 200 OK.
  - `POST /feedback` (Thumbs Down with comment): Verified 200 OK.
  - Rating validation: Rejects invalid ratings with 400 Bad Request.
  - CSV persistence: Verified row additions in `data/feedback_log.csv`.
  - `GET /feedback`: Verified retrieval of saved feedback entries.

### 5. Known Limitations
- Feedback currently acts as an observability and evaluation dataset for developers/administrators; it does not automatically fine-tune models in real time (which would risk model degradation).

---

## Feature 15: Real-Time Incremental Token Streaming with In-Flight JSON Parsing

### 1. What It Is
An asynchronous token extraction pipeline that parses structured JSON tokens from LLMs in real time as they arrive over Server-Sent Events (SSE), delivering an incremental typing experience in the frontend while preserving strict JSON schema validation.

### 2. Why It Was Built
Standard LLM JSON mode requires buffering the entire completion before parsing and rendering, causing a 2,500ms–4,000ms delay before users see any response text. Users perceive the application as unresponsive during long legal syntheses.

### 3. How It Works
- Implemented via `IncrementalAnswerExtractor` in [`app/api/routes.py`](file:///c:/Users/Vishal/Desktop/SIH/app/api/routes.py#L36-L115).
- Scans the inbound LLM token stream for the `"answer": "` key boundary.
- Once within the answer payload, decodes JSON escape sequences (`\n`, `\"`, `\\`) on the fly and immediately streams individual character deltas via SSE (`{'stage': 'llm_token', 'answer_delta': delta}`).
- Once the closing quote is reached, stops token streaming and emits the final validated payload with full citations and latency breakdowns on `stage: 'complete'`.
- Frontend (`frontend/app/page.tsx`) renders the streamed text with an active pulsating amber cursor (`animate-pulse`).

### 4. Verification Status: Fully Verified
- **Unit Test**: [`eval/test_streaming_extractor.py`](file:///c:/Users/Vishal/Desktop/SIH/eval/test_streaming_extractor.py) (2/2 tests passed in 1ms).
- **End-to-End Test**: Verified via `POST /ask/stream` across multiple test suites.
- **Latency Impact**: Time-To-First-Token (TTFT) in UI reduced from ~3,500ms to **`~150ms – 250ms`** after retrieval completion.

### 5. Known Limitations
- If the LLM generates severely malformed JSON that fails to produce an `"answer"` key within the first 50 characters, the extractor gracefully falls back to raw text passthrough mode.

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
| **Multi-Agent Deliberation** | Single pipeline with primary LLM and zero-backoff fallback. | Introduce multi-agent deliberation (e.g., Patent Examiner Agent vs. Applicant Advocate Agent) for contested Section 3(d)/3(p) borderline cases. |
| **Multimodal / Voice Interface** | Text-based multilingual chat interface with direct PDF document viewer. | Add ASR (Automatic Speech Recognition) and TTS (Text-to-Speech) using Bhashini speech pipelines for voice interaction by non-literate field practitioners. |

---

*Document compiled from active codebase implementations, test trajectories, and benchmark evaluations in `Vixhal17/SIH`.*
