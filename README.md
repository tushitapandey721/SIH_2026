# IP-SAKTI Sahayak (Legal & Ayurvedic Regulatory Intelligence)

> **Multilingual, Citation-Grounded Statutory AI for Ayurvedic Intellectual Property, Traditional Knowledge & Regulatory Affairs.**

---

## 🏛️ System Overview

**IP-SAKTI Sahayak** is a production-grade regulatory and patent intelligence co-pilot tailored for Indian Ayurveda and traditional knowledge practitioners, researchers, and enterprises. It strictly isolates and grounds responses in **17 verified statutory authorities and international treaties** with zero unverified hallucinations.

```
[User Interface (Next.js 16 + Tailwind CSS)]
  │
  ├── Jurisdiction Selector (National [IN] / Global [Treaties])
  ├── Interactive Formulation Classification Cards (Decision Tree)
  ├── Live Token-by-Token Streaming with Pulsating Cursor
  ├── In-App Statutory PDF Viewer & Official Registry Links
  ├── Multi-Turn Chat History Drawer (SQLite Sessions)
  └── User Feedback Drawer (Thumbs Up/Down + Diagnostic Tagging)
        │
        ▼ HTTP REST / SSE (/ask, /ask/stream, /pdf/*, /feedback, /admin/audit)
[FastAPI Application Backend (Uvicorn / Python 3.12)]
  │
  ├── Multi-Turn Memory Contextualizer (Sliding Window + SQLite)
  ├── Multilingual Translation Router (Bhashini NMT + LLM Preserving Citations)
  ├── Gated Formulation Decision Tree (D&C Act / Patents Act Rules)
  │
  ├── [Hybrid Legal Retrieval Engine (FP16 Accelerated on CUDA)]
  │     ├── Dense Semantic Search (BAAI/bge-m3, FP16 on CUDA / Qdrant HNSW)
  │     ├── Sparse Lexical Index (Custom Okapi BM25 + Compressed Gzip Disk Cache)
  │     ├── Reciprocal Rank Fusion (RRF k=60)
  │     └── Cross-Encoder Reranking (BAAI/bge-reranker-v2-m3, FP16 CUDA)
  │
  ├── High-Availability LLM Client (Groq openai/gpt-oss-120b -> Mistral Small 4 Fallback)
  └── Minimal Audit & Session Persistence (SQLite WAL + Append-Only CSV / DPDP Aligned)
```

---

## ✨ Key Features & Capabilities

For exhaustive technical mechanisms, evaluation scripts, and benchmark metrics, refer to [FEATURES.md](FEATURES.md).

| Feature | Description | Key Tech / Endpoint |
| :--- | :--- | :--- |
| **Hybrid Legal Retrieval (RAG)** | Dense semantic search (`bge-m3`) + sparse lexical matching (Okapi BM25) + Cross-Encoder reranking (`bge-reranker-v2-m3`) in FP16 on CUDA. | `87.5% Recall@5`, `303ms` latency |
| **Real-Time Token Streaming** | Live SSE token-by-token streaming with in-flight JSON extraction, immediate TCP flushing, and animated cursor. | `POST /ask/stream` |
| **Formulation Decision Tree** | Conversational classification across 6 statutory categories (*Classical*, *Proprietary*, *Rule 158-B*, *Phytopharma*, *Ayurveda Aahara*, *Cosmetics*). | D&C Act 1940 / Patents Act 1970 |
| **Strict Jurisdiction Switch** | Total physical and semantic isolation between Indian National statutes and International treaties (TRIPS, CBD, Nagoya, GRATK). | Hard metadata filter |
| **Direct PDF Citation Viewer** | Point-of-citation access to verified source PDFs and authoritative government portal registries (India Code, WIPO, NBA, FSSAI). | `GET /pdf/{doc_id}` |
| **Multi-Turn Conversation Memory** | Sliding-window memory maintaining context across follow-ups without leaking jurisdiction boundaries. | `GET /conversations`, `conversation_id` |
| **High-Availability LLM Client** | Primary inference via Groq (`openai/gpt-oss-120b`) with zero-backoff automated failover to Mistral (`Mistral Small 4`). | `max_retries=0` failover |
| **Multilingual Translation Layer** | Automated language detection and translation (Hindi, Tamil, etc.) with strict English citation preservation and one-click actions. | Bhashini API + LLM Translator |
| **Answer Feedback Mechanism** | Lightweight thumbs up/down signal with optional diagnostic reason tags and append-only logging. | `POST /feedback`, `data/feedback_log.csv` |
| **DPDP Minimal Audit Trail** | Privacy-first operational query audit logging with zero PII/fingerprinting and an interactive inspection view. | `GET /admin/audit`, `GET /admin/audit/view` |
| **Out-of-Scope Abstention** | Guaranteed non-hallucinatory abstention when statutory grounds are absent, with human facilitator escalation. | `abstained: true` |

---

## ⚡ Real-Time Streaming Architecture

The system features real-time token streaming across the entire stack:
1. **Asynchronous TCP Socket Flushing**: `StreamingResponse` with `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`, and `await asyncio.sleep(0.002)` yielding execution to Uvicorn's event loop between chunks.
2. **Groq Reasoning Optimization**: Employs `reasoning_effort="low"` on `gpt-oss` models to eliminate prolonged thinking pauses and begin emitting substantive content tokens in ~200ms.
3. **In-Flight JSON Parsing**: `IncrementalAnswerExtractor` parses the LLM's JSON stream on the fly, streaming only the answer text into the UI while keeping citations structured for completion.
4. **Interactive UI Typing Experience**: Instant bubble creation upon synthesis with an amber pulsating cursor `▮` that smoothly transitions to verified citation cards upon completion.

---

## 📜 Verified Statutory Corpus (17 Source Documents)

All statutory provisions are ingested from verified government repositories and served directly via `GET /pdf/{doc_id}`:

| Jurisdiction | Act / Treaty Title | Authority | Year | Citation Prefix | Source PDF |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **National (India)** | Patents Act 1970 | India Code | 1970 | `Patents Act S.` | [`patents_act_1970.pdf`](data/corpus/patents_act_1970.pdf) |
| **National (India)** | Biological Diversity (Amendment) Act 2023 | India Code | 2023 | `BDA S.` | [`biological_diversity_act_2023.pdf`](data/corpus/biological_diversity_act_2023.pdf) |
| **National (India)** | Biological Diversity Rules 2024 | NBA | 2024 | `BD Rules R.` | [`biological_diversity_rules_2024.pdf`](data/corpus/biological_diversity_rules_2024.pdf) |
| **National (India)** | Biological Diversity (Amendment) Rules 2025 | NBA | 2025 | `BD Amendment Rules R.` | [`biological_diversity_rules_2025.pdf`](data/corpus/biological_diversity_rules_2025.pdf) |
| **National (India)** | Drugs and Cosmetics Act 1940 & Rules 1945 | CDSCO | 2016 | `D&C Rules R. / D&C Act S.` | [`drugs_and_cosmetics_act_1940_and_rules_1945.pdf`](data/corpus/drugs_and_cosmetics_act_1940_and_rules_1945.pdf) |
| **National (India)** | Drugs & Magic Remedies (Objectionable Ads) Act 1954 | India Code | 1954 | `DMR Act S.` | [`drugs_and_magic_remedies_act_1954.pdf`](data/corpus/drugs_and_magic_remedies_act_1954.pdf) |
| **National (India)** | Ayurveda Aahara Regulations 2022 | FSSAI | 2022 | `FSSAI Reg.` | [`ayurveda_aahara_regulations_2022.pdf`](data/corpus/ayurveda_aahara_regulations_2022.pdf) |
| **National (India)** | Phytopharmaceutical Drugs General Guidance | IPC | 2025 | `IPC Phytopharma Guidance` | [`phytopharmaceutical_drugs_guidance_2025.pdf`](data/corpus/phytopharmaceutical_drugs_guidance_2025.pdf) |
| **National (India)** | Trade Marks Act 1999 | India Code | 1999 | `TM Act S.` | [`trademarks_act_1999.pdf`](data/corpus/trademarks_act_1999.pdf) |
| **National (India)** | Copyright Act 1957 | Copyright Office | 1957 | `Copyright Act S.` | [`copyright_act_1957.pdf`](data/corpus/copyright_act_1957.pdf) |
| **National (India)** | GI of Goods Act 1999 | IP India | 1999 | `GI Act S.` | [`geographical_indications_act_1999.pdf`](data/corpus/geographical_indications_act_1999.pdf) |
| **National (India)** | Designs Act 2000 | IP India | 2000 | `Designs Act S.` | [`designs_act_2000.pdf`](data/corpus/designs_act_2000.pdf) |
| **International** | TRIPS Agreement | WTO | 1995 | `TRIPS Art.` | [`trips_agreement.pdf`](data/corpus/trips_agreement.pdf) |
| **International** | Convention on Biological Diversity (CBD) | CBD | 1992 | `CBD Art.` | [`convention_on_biological_diversity.pdf`](data/corpus/convention_on_biological_diversity.pdf) |
| **International** | Nagoya Protocol | CBD | 2010 | `Nagoya Art.` | [`nagoya_protocol.pdf`](data/corpus/nagoya_protocol.pdf) |
| **International** | WIPO GRATK Treaty | WIPO | 2024 | `GRATK Art.` | [`wipo_gratk_treaty_2024.pdf`](data/corpus/wipo_gratk_treaty_2024.pdf) |
| **International** | Patent Cooperation Treaty (PCT) | WIPO | 1970 | `PCT Art.` | [`patent_cooperation_treaty.pdf`](data/corpus/patent_cooperation_treaty.pdf) |

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/ask/stream` | **Primary SSE streaming endpoint** emitting pipeline milestones and live token deltas. |
| `POST` | `/ask` | Synchronous JSON inquiry endpoint returning complete answer, citations, and classification. |
| `GET` | `/pdf/{doc_id}` | Serves verified statutory PDF documents directly from the local corpus directory. |
| `POST` | `/feedback` | Records answer rating (`up` or `down`), diagnostic reason tags, and optional user comments. |
| `GET` | `/conversations` | Lists all persisted conversational session threads. |
| `GET` | `/conversations/{id}` | Retrieves full message history and metadata for a specific conversation ID. |
| `DELETE` | `/conversations/{id}` | Deletes a conversation thread and its associated messages. |
| `GET` | `/corpus` | Lists all 17 ingested statutes, metadata, checksums, and official URLs. |
| `GET` | `/admin/audit` | Returns the last 50 queries from the DPDP-aligned audit log in JSON format. |
| `GET` | `/admin/audit/view` | Read-only administrative HTML dashboard inspecting operational compliance logs. |
| `GET` | `/health` | Diagnostic endpoint reporting API, Vector DB, and CUDA hardware status. |

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# Primary LLM Provider (Groq)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Fallback LLM Provider (Mistral)
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-small-latest

# Optional: Bhashini API Integration (Falls back to LLM translation if absent)
BHASHINI_API_KEY=your_bhashini_api_key_here
BHASHINI_USER_ID=your_bhashini_user_id_here

# Vector DB & Cache Storage
QDRANT_PATH=./qdrant_data
APP_HOST=0.0.0.0
APP_PORT=8000
ENVIRONMENT=development
```

---

## 🚀 Quickstart Guide

### 1. Python Virtual Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Corpus Ingestion & Cache Pre-computation

Ingest all 17 statutory PDF documents from `data/manifest.csv` into Qdrant and compile the BM25 compressed index cache:

```bash
python -c "from app.retrieval.ingest import ingest_all; ingest_all()"
```

> **⚡ Hardware Acceleration (CUDA vs CPU)**:
> Embedding (`BAAI/bge-m3`) and Cross-Encoder reranking (`BAAI/bge-reranker-v2-m3`) automatically detect `torch.cuda.is_available()`. If a CUDA GPU is present, it uses FP16 precision on device `0`, delivering ~300ms retrieval; otherwise, it seamlessly falls back to CPU.

---

### 3. Start Backend & Frontend Servers

#### Backend API (FastAPI + Uvicorn)
```bash
# From workspace root
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive Audit Dashboard: [http://localhost:8000/admin/audit/view](http://localhost:8000/admin/audit/view)
- Corpus Provenance: [http://localhost:8000/corpus](http://localhost:8000/corpus)

#### Frontend Interface (Next.js 16 + Tailwind CSS)
```bash
# In a separate terminal
cd frontend
npm install
npm run build
npm start   # or npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Verification & Automated Testing

Run the comprehensive test and evaluation suites:

```bash
# 1. Retrieval & Reranker Production Benchmark (Recall@5, MRR, Latency)
python eval/production_readiness_benchmark.py

# 2. LLM Client & High-Speed Failover (Groq + Mistral)
python eval/test_llm_client.py

# 3. Session Store, Multi-Turn Memory & Conversations API
python eval/test_session_store_and_api.py

# 4. Direct Source PDF Citation Links (All 17 Acts & Treaties)
python eval/test_pdf_citation_links.py

# 5. Answer Feedback Mechanism (Thumbs Up/Down + Diagnostic Comments)
python eval/test_feedback.py

# 6. DPDP Minimal Regulatory Audit Log & Administrative Dashboard
python eval/test_audit_log.py

# 7. End-to-End Integration Suite
python eval/test_frontend_e2e_integration.py
```

---

## 🔒 Data Protection & Minimal Audit Logging (DPDP Alignment)

IP-SAKTI Sahayak implements a foundational audit trail aligned with the core data-minimization tenets of India's **Digital Personal Data Protection (DPDP) Act, 2023**:

- **Data Minimization (Section 4 & Section 6)**: The system logs strictly operational query/response metadata necessary for statutory compliance tracking, latency profiling, and model governance:
  - Timestamp (UTC ISO 8601)
  - Jurisdiction scope (`national` vs `international`)
  - Query text
  - Formulation classification category (if triggered)
  - LLM inference provider (`groq`, `mistral`, etc.)
  - Response latency (ms)
  - Abstention status (boolean)
  - Ephemeral session correlation ID
- **Zero PII & Anti-Fingerprinting Policy**: To uphold the privacy rights of researchers and practitioners, the audit trail explicitly **does not capture or store**:
  - IP addresses
  - Device fingerprints or User-Agent headers
  - User identifiers, cookies, or location telemetry
- **Inspectable Dual-Storage Architecture**:
  - **Append-Only File**: Persisted to `data/audit_log.csv` and `data/audit_log` for immutable file-based auditing.
  - **Relational Store**: Indexed in SQLite table `audit_logs` (`data/ip_sakti.db`).
  - **Administrative Inspection**: Inspectable via read-only endpoints `GET /admin/audit` (JSON) and `GET /admin/audit/view` (interactive HTML dashboard).

---

## ⚖️ Legal Disclaimer

*IP-SAKTI Sahayak provides statutory information and regulatory guidance for research, education, and compliance preparation. It does not constitute formal legal counsel or create an attorney-client relationship. Inquiries regarding patent prosecution or commercial licensing should be escalated to a qualified patent agent or legal practitioner.*

