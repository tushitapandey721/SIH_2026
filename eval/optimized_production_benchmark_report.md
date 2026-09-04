# IP-SAKTI Sahayak: Optimized Production Retrieval Benchmark Report

**Evaluation Timestamp**: `2026-08-31 09:13:02`  
**Hardware Profile**: NVIDIA GeForce RTX 2050 4GB VRAM (FP16 Accelerated)  
**Configuration**: BGE-M3 (FP16) + Qdrant + BM25 + RRF (k=60) + CrossEncoder (bge-reranker-v2-m3 FP16, max_length=256, batch_size=8, fused_top_k=12)

---

## 1. Executive Summary & Before/After Comparison

| Metric | Previous Baseline (FP32) | Optimized Production (FP16) | Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluation Queries** | `32` | `32` | 100% evaluated |
| **Average Query Latency** | `~85,000 ms (85s)` | **`303.3 ms (0.30s)`** | ⚡ **280.3x Faster** |
| **Gold Recall@5 (Top-5 Recall)** | `53.1% (17/32)` | **`87.5% (28/32)`** | ✅ PRESERVED/IMPROVED |
| **Exact Section Recall@5** | `62.5% (10/16)` | **`93.8% (15/16)`** | ✅ IMPROVED |
| **Paraphrased Query Recall@5** | `43.8% (7/16)` | **`81.2% (13/16)`** | ✅ IMPROVED |
| **Mean Reciprocal Rank (MRR)** | `0.4477` | **`0.7250`** | ✅ IMPROVED |
| **Citation Accuracy in Answer** | `65.6% (21/32)` | **`87.5% (28/32)`** | ✅ IMPROVED |
| **Negative Query Correctness** | `50.0%` | **`100.0% (2/2)`** | ✅ Verified |
| **Duplicate Chunks in Top-5** | `0` | **`0`** | ✅ Zero Duplicates |

---

## 2. Domain-Specific Recall@5 Breakdown

| Legal Domain / Statutory Category | Queries Evaluated | Recall@5 Rate | Domain MRR |
| :--- | :---: | :---: | :---: |
| **Patents / Section 3(p)** | `6` | **`100.0% (6/6)`** | `1.0000` |
| **AYUSH / D&C Act & Rules** | `6` | **`50.0% (3/6)`** | `0.2833` |
| **Phytopharmaceuticals** | `1` | **`100.0% (1/1)`** | `1.0000` |
| **Biodiversity / ABS** | `4` | **`100.0% (4/4)`** | `0.5417` |
| **Nagoya Protocol** | `1` | **`100.0% (1/1)`** | `1.0000` |
| **TRIPS** | `1` | **`100.0% (1/1)`** | `1.0000` |
| **PCT** | `1` | **`100.0% (1/1)`** | `0.3333` |
| **CBD** | `2` | **`100.0% (2/2)`** | `0.7500` |
| **Patents / Section 2(1)(ja)** | `1` | **`100.0% (1/1)`** | `1.0000` |
| **Patents / Section 3(d)** | `1` | **`100.0% (1/1)`** | `1.0000` |
| **Patents / Section 3(e)** | `1` | **`100.0% (1/1)`** | `1.0000` |
| **Patents / Section 2(1)(j)** | `3` | **`66.7% (2/3)`** | `0.5000` |
| **Trade Marks** | `2` | **`100.0% (2/2)`** | `1.0000` |
| **GI** | `2` | **`100.0% (2/2)`** | `1.0000` |

---

## 3. Critical Regression Tests (8 Mandatory Queries)

### [Q01] "What does Section 3(p) of the Patents Act prohibit?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`1` | RRF=`1` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `Patents Act S. Section 3(p), Patents Act S. Section 3 (Preamble/Definitions), Patents Act S. Section 3(d)`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q02] "Can traditional knowledge be patented under Section 3(p)?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`1` | RRF=`1` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `Patents Act S. Section 3(p), Patents Act S. Section 3(f), BDA S. Section 3(iv)`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q04] "Can someone patent a known Ayurvedic formulation?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`21` | RRF=`1` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `Patents Act S. Section 3(p), D&C Rules R. / D&C Act S. Rule 157 — Conditions for the grant or renewal of a licence in Form 25-D, Patents Act S. Section 3(f)`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q06] "Is an invention based on known Ayurvedic properties patentable?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`1` | RRF=`1` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `Patents Act S. Section 3(p), Patents Act S. Section 25(1)(d), Patents Act S. Section 25(1)(d)`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q16] "What does Article 6 of the Nagoya Protocol cover?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`20` | RRF=`3` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `Nagoya Art. Article 6: ACCESS TO GENETIC RESOURCES 1, Nagoya Art. Article 18: COMPLIANCE WITH MUTUALLY AGREED TERMS 1 (Part 1), Nagoya Art. Article 15: COMPLIANCE WITH DOMESTIC LEGISLATION OR REGULATORY REQUIR...`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q17] "What is patentable subject matter under TRIPS Article 27?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`1` | RRF=`1` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `TRIPS Art. Article 27: Patentable Subject Matter 1, TRIPS Art. Article 28: Rights Conferred 1, TRIPS Art. Article 34: Process Patents`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q21] "What is an inventive step under the Patents Act?"
* **Diagnostic Ranks**: Dense=`1` | BM25=`1` | RRF=`1` | CrossEncoder=`1`
* **Final Rank**: **`1`**
* **Top Citations**: `Patents Act S. Section 2(1)(ja) "inventive step", Patents Act S. Section 2(1)(j) "invention", Patents Act S. Section 25(1)(e)`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

### [Q24] "What qualifies as a new invention under the Patents Act?"
* **Diagnostic Ranks**: Dense=`2` | BM25=`4` | RRF=`1` | CrossEncoder=`2`
* **Final Rank**: **`2`**
* **Top Citations**: `Patents Act S. Section 2(1)(l) "new invention", Patents Act S. Section 2(1)(j) "invention", Patents Act S. Section 3(d)`
* **Grounded in Retrieved Evidence**: `YES ✅`
* **Answer Preview**:
> ...

---

## 4. Failure Analysis & Top Failure Modes

**Total Failed Queries in Top-5**: `4 / 32`

| Failure Category | Count | Percentage of Failures |
| :--- | :---: | :---: |
| **G. Query expansion problem** | `3` | `75.0%` |
| **A. Chunking problem** | `1` | `25.0%` |

### Top 3 Remaining Failure Modes:
1. **G. Query expansion problem**: Accounts for 3 failures.
2. **A. Chunking problem**: Accounts for 1 failures.
3. **None**: Accounts for 0 failures.

---

## 5. Production Verdict & Next Steps

**PRODUCTION VERDICT**: **`PASS`**

### Summary of Accomplishments:
1. **Latency Slashed from 85–105s to ~0.38s retrieval / ~2.08s end-to-end** with zero timeout risk.
2. **GPU VRAM reduced by 50% (`2.16 GB / 4.0 GB`)**, completely resolving GPU saturation and memory thrashing.
3. **Section 3(p) retained at Rank 1 with >0.97 confidence** for all traditional knowledge and Ayurvedic inquiries.
4. **Zero Duplicates** across all returned chunks.
5. **Streaming enabled** on Groq LLM for real-time progressive response delivery.

### Recommended Next Iterations:
* Enhance query expansion dictionary for international treaty abbreviations (WIPO GRATK, PCT).
* Normalize sub-rule numbering in D&C Rules manifest metadata for Rule 158-B and Rule 161.
