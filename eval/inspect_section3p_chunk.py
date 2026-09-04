"""Inspect exact Qdrant chunk containing Section 3(p) of Patents Act 1970 and its surrounding chunks."""

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

client = QdrantClient(path="qdrant_data")

# 1. Fetch all points for IND-PAT-001 in sequence order
doc_id = "IND-PAT-001"
point_ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_{i}")) for i in range(291)]

points_resp = client.retrieve(
    collection_name="ip_sakti_corpus",
    ids=point_ids,
    with_payload=True,
    with_vectors=False,
)

# Sort points by their original sequence index
points_by_idx = {}
for pt in points_resp:
    # find idx from uuid mapping
    for i in range(291):
        if pt.id == point_ids[i]:
            points_by_idx[i] = pt
            break

print(f"Total retrieved points for {doc_id}: {len(points_by_idx)}")

# Find target index containing 3(p) / traditional knowledge
target_idx = None
for i, pt in points_by_idx.items():
    txt = pt.payload.get("text", "")
    if "traditional knowledge" in txt.lower() or "3(p)" in txt or "(p)" in txt:
        if "Patents Act" in pt.payload.get("title", "") and "CHAPTER II" in pt.payload.get("section", ""):
            target_idx = i
            break

print("\n" + "=" * 90)
print(f"TARGET CHUNK INDEX: {target_idx}")
print("=" * 90)

# Print 2 chunks before, target chunk, and 2 chunks after
start_range = max(0, target_idx - 2) if target_idx is not None else 0
end_range = min(len(points_by_idx), target_idx + 3) if target_idx is not None else 5

for i in range(start_range, end_range):
    pt = points_by_idx.get(i)
    if not pt:
        continue
    p = pt.payload
    is_target = (i == target_idx)
    marker = ">>> [TARGET CHUNK CONTAINING SECTION 3(p)] <<<" if is_target else f"--- [SURROUNDING CHUNK (Index {i})] ---"

    print("\n" + "#" * 90)
    print(marker)
    print(f"Index:           {i}")
    print(f"Point ID:        {pt.id}")
    print(f"Document Title:  {p.get('title')}")
    print(f"Section Field:   '{p.get('section')}'")
    print(f"Citation Prefix: '{p.get('citation_prefix')}'")
    print(f"Jurisdiction:    '{p.get('jurisdiction')}'")
    print(f"Text Length:     {len(p.get('text', ''))} characters")
    print("-" * 90)
    print("FULL RAW TEXT STORED IN QDRANT:")
    print(repr(p.get("text", "")))
    print("-" * 90)
    print("FORMATTED TEXT DISPLAY:")
    print(p.get("text", ""))
    print("#" * 90)
