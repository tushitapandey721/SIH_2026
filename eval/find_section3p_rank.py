"""Find exact dense rank of Section 3(p) in Qdrant."""

import sys
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

client = QdrantClient(path="qdrant_data")
model = SentenceTransformer("BAAI/bge-m3", device="cuda")
model.max_seq_length = 512

query = "Is a classical Ayurvedic formulation patentable?"
q_vec = model.encode(query, normalize_embeddings=True).tolist()

resp = client.query_points(
    collection_name="ip_sakti_corpus",
    query=q_vec,
    query_filter=Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))]),
    limit=80,
)

print(f"Total points returned: {len(resp.points)}")
patents_act_hits = []
for rank, pt in enumerate(resp.points, start=1):
    title = pt.payload.get("title", "")
    sec = pt.payload.get("section", "")
    txt = pt.payload.get("text", "")
    if "Patents Act" in title:
        patents_act_hits.append((rank, pt.score, sec, txt[:100]))

print(f"\nPatents Act hits in top {len(resp.points)}:")
for r, s, sec, t in patents_act_hits:
    print(f"  • Rank #{r:2d} (Cosine: {s:.4f}) | Sec: {sec} | Snippet: {t}...")
