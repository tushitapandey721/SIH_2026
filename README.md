# IP-SAKTI Sahayak (Legal & Ayurvedic Regulatory Intelligence)

> **Multilingual, Citation-Grounded Statutory AI for Ayurvedic Intellectual Property, Traditional Knowledge & Regulatory Affairs.**

---

## 🏛️ System Overview

**IP-SAKTI Sahayak** is a production-grade regulatory and patent intelligence co-pilot tailored for Indian Ayurveda and traditional knowledge practitioners, researchers, and enterprises. It strictly isolates and grounds responses in **17 verified statutory authorities and international treaties** with zero unverified hallucinations.

### Key Capabilities
- **Hierarchical Statutory Ingestion**: Dense vector embeddings (`BAAI/bge-m3`) + BM25 keyword matching + `BAAI/bge-reranker-v2-m3` Cross-Encoder reranking.
- **Formulation Decision Tree**: Conversational classification into *Classical Medicine*, *Proprietary Medicine*, *New Drug (Rule 158-B)*, *Phytopharmaceutical*, *Nutraceutical (Ayurveda Aahara)*, or *Cosmetic*.
- **Multilingual Support**: Real-time language detection and native translation with statutory citation preservation.
- **Strict Grounding & Abstention**: Automatic abstention when verified statutory provisions are absent, prompting direct escalation to the *Human IP Facilitation Cell*.
- **High-Availability LLM Client**: Primary inference via Groq (`openai/gpt-oss-120b`) with zero-downtime fallback to Mistral API (`Mistral Small 4`).
- **Real-Time Pipeline Streaming**: Server-Sent Events (SSE) broadcasting live stage milestones (`/ask/stream`).

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# Primary LLM Provider (Groq)
GROQ_API_KEY=your_groq_api_key_here

# Fallback LLM Provider (Mistral)
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional: Bhashini API Integration
BHASHINI_API_KEY=your_bhashini_api_key_here
BHASHINI_USER_ID=your_bhashini_user_id_here

# Qdrant Vector DB Storage (defaults to local ./qdrant_data directory)
QDRANT_PATH=./qdrant_data
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

### 2. Corpus Ingestion & Embedding

Ingest all 17 statutory PDF documents from `data/manifest.csv` into the hybrid search engine:

```bash
python -c "from app.retrieval.ingest import ingest_all; ingest_all()"
```

> **⚡ Hardware Acceleration (GPU vs CPU)**:
> Embedding and Cross-Encoder reranking automatically detect hardware acceleration via `torch.cuda.is_available()`. If a CUDA-compatible GPU is present, it will run on CUDA device `0`; otherwise, it smoothly defaults to multi-threaded CPU execution.

---

### 3. Start Backend & Frontend Servers

#### Backend API (FastAPI + Uvicorn)
```bash
# From workspace root
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- Corpus Provenance: [http://localhost:8000/corpus](http://localhost:8000/corpus)

#### Frontend Interface (Next.js + Tailwind CSS)
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## 📜 Verified Corpus Provenance (17 Source Documents)

| Jurisdiction | Act / Treaty Title | Authority | Year | Citation Prefix |
| :--- | :--- | :--- | :--- | :--- |
| **National (India)** | Patents Act 1970 | India Code | 1970 | `Patents Act S.` |
| **National (India)** | Biological Diversity (Amendment) Act 2023 | India Code | 2023 | `BDA S.` |
| **National (India)** | Biological Diversity Rules 2024 | NBA | 2024 | `BD Rules R.` |
| **National (India)** | Biological Diversity (Amendment) Rules 2025 | NBA | 2025 | `BD Amendment Rules R.` |
| **National (India)** | Drugs and Cosmetics Act 1940 & Rules 1945 | CDSCO | 2016 | `D&C Rules R. / D&C Act S.` |
| **National (India)** | Drugs & Magic Remedies (Objectionable Ads) Act 1954 | India Code | 1954 | `DMR Act S.` |
| **National (India)** | Ayurveda Aahara Regulations 2022 | FSSAI | 2022 | `FSSAI Reg.` |
| **National (India)** | Phytopharmaceutical Drugs General Guidance | IPC | 2025 | `IPC Phytopharma Guidance` |
| **National (India)** | Trade Marks Act 1999 | India Code | 1999 | `TM Act S.` |
| **National (India)** | Copyright Act 1957 | Copyright Office | 1957 | `Copyright Act S.` |
| **National (India)** | GI of Goods Act 1999 | IP India | 1999 | `GI Act S.` |
| **National (India)** | Designs Act 2000 | IP India | 2000 | `Designs Act S.` |
| **International** | TRIPS Agreement | WTO | 1995 | `TRIPS Art.` |
| **International** | Convention on Biological Diversity (CBD) | CBD | 1992 | `CBD Art.` |
| **International** | Nagoya Protocol | CBD | 2010 | `Nagoya Art.` |
| **International** | WIPO GRATK Treaty | WIPO | 2024 | `GRATK Art.` |
| **International** | Patent Cooperation Treaty (PCT) | WIPO | 1970 | `PCT Art.` |

---

## 🧪 Verification & Testing

Run the automated test suites:

```bash
# 1. LLM Client & High-Speed Fallback (Groq + Mistral)
python eval/test_llm_client.py

# 2. Session Store, Multi-Turn Memory & Conversations API
python eval/test_session_store_and_api.py

# 3. Direct PDF Citation Links (All 17 Acts & Treaties)
python eval/test_pdf_citation_links.py

# 4. Answer Feedback Mechanism (Thumbs Up/Down + Comments)
python eval/test_feedback.py

# 5. DPDP Minimal Audit Log & Administrative Views
python eval/test_audit_log.py

# 6. End-to-End Integration Suite
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

> [!NOTE]
> **Scope & Roadmap**: This implementation is designed as a foundational audit-logging mechanism scoped as an honest starting point for DPDP alignment within a hackathon timeline, rather than claiming full statutory certification. Full enterprise DPDP compliance in a production deployment requires additional institutional infrastructure—specifically AES-256 encryption at rest, cryptographically enforced Role-Based Access Control (RBAC) on the admin inspection interface, and automated data retention/expunction schedules.

---

## ⚖️ Legal Disclaimer
*IP-SAKTI Sahayak provides statutory information and regulatory guidance for research and compliance preparation. It does not constitute formal legal counsel.*
