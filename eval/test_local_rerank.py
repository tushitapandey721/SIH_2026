"""Test CrossEncoder with local_files_only=True for instant offline loading."""

import sys
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import torch
from sentence_transformers import CrossEncoder
from huggingface_hub import snapshot_download

snapshot_path = snapshot_download("BAAI/bge-reranker-v2-m3", local_files_only=True)
reranker = CrossEncoder(snapshot_path, device="cuda")

query = "Is a classical Ayurvedic formulation patentable?"

sec3p = "(p) an invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components."
dc = "Drugs and Cosmetics Act, 1940: patent or proprietary medicine means in relation to Ayurvedic, Siddha or Unani Tibb systems of medicine all formulations containing only such ingredients mentioned in the formulae described in the authoritative books of Ayurveda."

scores = reranker.predict([[query, sec3p], [query, dc]], batch_size=2)
sigmoids = torch.sigmoid(torch.tensor(scores)).tolist()

print("Query:", query)
print(f"1. Section 3(p) (Patents Act) Logit: {scores[0]:+.4f} | Sigmoid: {sigmoids[0]:.4f} ({sigmoids[0]*100:.1f}%)")
print(f"2. D&C Act Section 3(h) Logit:       {scores[1]:+.4f} | Sigmoid: {sigmoids[1]:.4f} ({sigmoids[1]*100:.1f}%)")
