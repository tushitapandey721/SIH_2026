"""Benchmark script to test GPU embedding throughput with BAAI/bge-m3."""

import sys
import time
import torch
from sentence_transformers import SentenceTransformer

# Enable flush on all prints
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Detected Device: {device}", flush=True)
if device == "cuda":
    print(f"GPU Name: {torch.cuda.get_device_name(0)}", flush=True)

# Load model on GPU
print("Loading BAAI/bge-m3 on GPU...", flush=True)
try:
    model = SentenceTransformer("BAAI/bge-m3", device=device, local_files_only=True)
except Exception:
    model = SentenceTransformer("BAAI/bge-m3", device=device)

print(f"Model loaded onto: {model.device}", flush=True)

# 10 sample legal sentences
sentences = [
    "Section 3(p) of the Indian Patents Act prohibits patenting traditional knowledge.",
    "The Biological Diversity Act 2002 mandates prior approval for commercial utilization.",
    "Ayurveda Aahara regulations govern food products prepared in accordance with classical texts.",
    "Phytopharmaceutical drugs require submission of safety and pharmacological profile data.",
    "TRIPS Article 27 permits members to exclude diagnostic, therapeutic, and surgical methods.",
    "The Nagoya Protocol provides a transparent legal framework for access and benefit-sharing.",
    "Proprietary Ayurvedic medicines require proof of safety and effectiveness under Rule 158B.",
    "Section 33EEA prohibits manufacture and sale of certain adulterated Ayurvedic drugs.",
    "Trade Marks Act 1999 protects distinctive brand names, logos, and product identifiers.",
    "WIPO GRATK Treaty establishes mandatory disclosure requirements for genetic resources.",
]

# Warmup GPU
print("Warming up GPU...", flush=True)
_ = model.encode(sentences[:2], normalize_embeddings=True)

# Measure batched GPU encoding
print("Encoding 10 sentences with CUDA acceleration...", flush=True)
torch.cuda.synchronize()
start_time = time.perf_counter()
embeddings = model.encode(sentences, batch_size=32, normalize_embeddings=True)
torch.cuda.synchronize()
elapsed_time = time.perf_counter() - start_time

print("\n" + "=" * 60, flush=True)
print("GPU EMBEDDING BENCHMARK RESULT:", flush=True)
print(f"Sentences Encoded: {len(sentences)}", flush=True)
print(f"Embedding Shape:   {embeddings.shape}", flush=True)
print(f"Device Used:       {model.device}", flush=True)
print(f"Elapsed Time:      {elapsed_time:.4f} seconds ({elapsed_time * 1000:.2f} ms)", flush=True)
print("=" * 60, flush=True)
