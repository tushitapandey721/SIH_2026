"""Find exact dense rank of the isolated Section 3(p) chunk."""

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
    limit=150,
)

print(f"Total points searched: {len(resp.points)}")
found = False
for rank, pt in enumerate(resp.points, start=1):
    p = pt.payload
    if p.get("title") == "Patents Act 1970" and "3(p)" in p.get("section", ""):
        print(f"\nTarget Section 3(p) found at:")
        print(f"  • Dense Rank:  #{rank}")
        print(f"  • Cosine Score: {pt.score:.4f}")
        print(f"  • Section ID:  {p.get('section')}")
        print(f"  • Text:        {p.get('text')}")
        found = True
        break

if not found:
    print("Section 3(p) was not found in top 150.")
