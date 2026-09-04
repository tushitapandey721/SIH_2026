"""Check Section 2 chunks in Qdrant."""

import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

client = QdrantClient(path="qdrant_data")
points, _ = client.scroll(
    collection_name="ip_sakti_corpus",
    limit=5000,
    with_payload=True,
    with_vectors=False,
)

print(f"Total points in Qdrant: {len(points)}")
sec2_points = []
nagoya_points = []
trips_points = []

for pt in points:
    p = pt.payload
    title = p.get("title", "")
    sec = p.get("section", "")
    if "Patents Act" in title and "Section 2" in sec:
        sec2_points.append(p)
    if "Nagoya" in title:
        nagoya_points.append(p)
    if "TRIPS" in title:
        trips_points.append(p)

print(f"\nFound {len(sec2_points)} Section 2 points in Patents Act:")
for p in sec2_points[:15]:
    print(f"  • {p['section']}: {p['text'][:80]}...")

print(f"\nFound {len(nagoya_points)} points in Nagoya Protocol:")
for p in nagoya_points[:10]:
    print(f"  • {p['section']}")

print(f"\nFound {len(trips_points)} points in TRIPS Agreement:")
for p in trips_points[:10]:
    print(f"  • {p['section']}")
