"""Re-ingest Patents Act 1970 with subclause chunking and evaluate Section 3(p) dense rank."""

import sys
import uuid
import time
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import yaml
import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from app.ingestion.extract import extract_document
from app.ingestion.chunk import chunk_document
from app.retrieval.store import (
    COLLECTION_NAME,
    QDRANT_STORAGE_PATH,
    DEFAULT_MODEL_NAME,
)

SIDECAR_DIR = PROJECT_ROOT / "data" / "sidecars"


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reingest_patents_act():
    doc_id = "IND-PAT-001"
    pdf_path = PROJECT_ROOT / "data" / "corpus" / "national" / "Patents Act, 1970.pdf"
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 80)
    print(f"RE-INGESTING PATENTS ACT 1970 ({doc_id}) ON {device}")
    print("=" * 80)

    client = QdrantClient(path=str(QDRANT_STORAGE_PATH))
    embed_model = SentenceTransformer(DEFAULT_MODEL_NAME, device=device)
    embed_model.max_seq_length = 512

    # 1. Delete old points of IND-PAT-001
    old_sidecar = SIDECAR_DIR / f"{doc_id}.yaml"
    old_chunk_count = 291
    if old_sidecar.exists():
        with open(old_sidecar, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            old_chunk_count = data.get("total_chunks", 291)

    print(f"Purging old {old_chunk_count} points of {doc_id} from Qdrant...")
    old_point_ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_{i}")) for i in range(old_chunk_count + 50)]
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=old_point_ids,
    )
    print("Old points purged successfully.")

    # 2. Extract & chunk with updated sub-clause splitting
    raw_text, _ = extract_document(pdf_path)
    new_chunks = chunk_document(raw_text, chunk_strategy="section")
    print(f"Extracted {len(new_chunks)} refined chunks for {doc_id} (including lettered subclauses).")

    # Verify Section 3(p) chunk
    sec_3p_chunks = [c for c in new_chunks if "3(p)" in c["section_id"] or ("traditional knowledge" in c["text"].lower() and "3" in c["section_id"])]
    print(f"\nFound {len(sec_3p_chunks)} Section 3(p) chunks:")
    for c in sec_3p_chunks:
        print(f"  • Section ID: {c['section_id']}")
        print(f"    Text:       {c['text'][:140]}...")

    # 3. Embed & Upsert
    texts_to_embed = [c["text"] for c in new_chunks]
    start_embed = time.perf_counter()
    embeddings = embed_model.encode(
        texts_to_embed,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    embed_time = time.perf_counter() - start_embed
    print(f"Generated {len(embeddings)} embeddings on {device} in {embed_time:.2f}s.")

    points: list[PointStruct] = []
    for idx, (chunk, vector) in enumerate(zip(new_chunks, embeddings)):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_{idx}"))
        payload = {
            "text": chunk["text"],
            "section": chunk["section_id"],
            "citation_prefix": "Patents Act S.",
            "authority": "CGPDTM (Indian Patent Office)",
            "category": "Patent",
            "jurisdiction": "national",
            "priority": "P1",
            "year": 1970,
            "title": "Patents Act 1970",
            "document_id": doc_id,
            "chunk_index": idx,
        }
        points.append(PointStruct(id=point_id, vector=vector.tolist(), payload=payload))

    # Batch upsert
    for b_start in range(0, len(points), 64):
        b_end = min(b_start + 64, len(points))
        client.upsert(collection_name=COLLECTION_NAME, points=points[b_start:b_end])

    # 4. Update sidecar
    content_hash = compute_content_hash(raw_text)
    sidecar_data = {
        "document_id": doc_id,
        "title": "Patents Act 1970",
        "file_name": "Patents Act, 1970.pdf",
        "jurisdiction": "national",
        "content_hash": content_hash,
        "total_chunks": len(new_chunks),
        "chunk_strategy": "section_with_subclauses",
        "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(old_sidecar, "w", encoding="utf-8") as f:
        yaml.safe_dump(sidecar_data, f, sort_keys=False)
    print(f"Updated sidecar at {old_sidecar} with {len(new_chunks)} chunks.")

    # 5. Evaluate dense rank of Section 3(p)
    print("\n" + "=" * 80)
    print("EVALUATING DENSE SEARCH RANK FOR ISOLATED SECTION 3(p) CHUNK:")
    print("Query: \"Is a classical Ayurvedic formulation patentable?\"")
    print("=" * 80)

    query = "Is a classical Ayurvedic formulation patentable?"
    q_vec = embed_model.encode(query, normalize_embeddings=True).tolist()

    resp = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        query_filter=Filter(must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))]),
        limit=50,
    )

    print(f"Queried top 50 national chunks:")
    found_3p = None
    for rank, pt in enumerate(resp.points, start=1):
        p = pt.payload
        if p.get("title") == "Patents Act 1970" and "3(p)" in p.get("section", ""):
            found_3p = (rank, pt.score, p.get("section"), p.get("text"))
            print(f"\n  >>> [TARGET FOUND] Rank #{rank:2d} (Cosine: {pt.score:.4f}) | Citation: Patents Act {p.get('section')}")
            print(f"      Text: {p.get('text')}\n")
        elif rank <= 5:
            print(f"      Rank #{rank:2d} (Cosine: {pt.score:.4f}) | Citation: {p.get('citation_prefix')} {p.get('section')} | Doc: {p.get('title')}")

    if not found_3p:
        print("  Section 3(p) not in top 50.")
    print("=" * 80)


if __name__ == "__main__":
    reingest_patents_act()
