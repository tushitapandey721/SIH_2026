"""Script to delete old IND-DRUG-001 chunks from Qdrant, re-extract targeted ASU provisions, and re-embed on GPU."""

import sys
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import torch
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PointIdsList,
)
from sentence_transformers import SentenceTransformer

from app.retrieval.store import (
    COLLECTION_NAME,
    QDRANT_STORAGE_PATH,
    DEFAULT_MODEL_NAME,
    VectorStoreManager,
    default_store_manager,
)
from app.ingestion.extract import extract_document, locate_corpus_file
from app.ingestion.chunk import chunk_document


def reingest_dc_act_trimmed():
    manager = default_store_manager
    client = manager.client
    model = manager.model

    doc_id = "IND-DRUG-001"
    title = "Drugs and Cosmetics Act 1940 and Rules 1945"
    filename = "2016DrugsandCosmeticsAct1940Rules1945.pdf"
    jurisdiction = "national"
    category = "Drug"
    authority = "CDSCO / Ministry of AYUSH"
    citation_prefix = "D&C Rules R."
    priority = "P0"
    year = "1940"
    chunk_strategy = "rule"

    print("=" * 80)
    print(f"TRIMMING & RE-INGESTING {doc_id}")
    print(f"Device: {manager.device} ({torch.cuda.get_device_name(0) if manager.device == 'cuda' else 'CPU'})")
    print("=" * 80)

    pdf_path = locate_corpus_file(filename)
    if not pdf_path or not pdf_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {filename}")

    # 1. Delete all old IND-DRUG-001 points from Qdrant
    print(f"\n[1/4] Deleting old points for {doc_id} from Qdrant collection '{COLLECTION_NAME}'...")
    sidecar_old = manager.get_sidecar(doc_id)
    old_chunks_count = sidecar_old.get("total_chunks", 3203) if sidecar_old else 3203

    old_point_ids = [
        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_{i}"))
        for i in range(old_chunks_count + 100)
    ]
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=PointIdsList(points=old_point_ids),
    )
    print(f"Successfully deleted {old_chunks_count} old points.")

    # 2. Extract targeted text
    print(f"\n[2/4] Extracting targeted ASU/Ayurveda statutory & regulatory provisions...")
    cleaned_text, method = extract_document(pdf_path)
    print(f"Extraction method: {method}")
    print(f"Cleaned targeted text length: {len(cleaned_text)} characters")

    # 3. Chunk targeted text
    print(f"\n[3/4] Chunking targeted text with strategy '{chunk_strategy}'...")
    chunks = chunk_document(cleaned_text, chunk_strategy=chunk_strategy)
    print(f"New trimmed chunks produced: {len(chunks)}")

    # 4. Embed and upsert to Qdrant on GPU
    print(f"\n[4/4] Generating GPU embeddings for {len(chunks)} chunks using {DEFAULT_MODEL_NAME}...")
    chunk_texts = [c["text"] for c in chunks]

    start_time = time.time()
    embeddings = model.encode(
        chunk_texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    emb_time = time.time() - start_time
    print(f"Embeddings generated in {emb_time:.2f}s ({len(chunks) / emb_time:.1f} chunks/sec).")

    points = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_{idx}"))
        payload = {
            "text": chunk["text"],
            "section": chunk["section_id"],
            "citation_prefix": citation_prefix,
            "authority": authority,
            "category": category,
            "jurisdiction": jurisdiction.lower(),
            "priority": priority,
            "year": str(year),
            "title": title,
        }
        points.append(PointStruct(id=point_id, vector=emb.tolist(), payload=payload))

    for i in range(0, len(points), 100):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i : i + 100],
        )

    # 5. Save updated sidecar
    current_hash = manager.compute_file_hash(pdf_path)
    sidecar_data = {
        "id": doc_id,
        "title": title,
        "jurisdiction": jurisdiction.lower(),
        "content_hash": current_hash,
        "total_chunks": len(chunks),
        "extraction_method": method,
        "last_ingested_at": datetime.now(timezone.utc).isoformat(),
        "targeted_trimmed": True,
    }
    manager.save_sidecar(doc_id, sidecar_data)

    stats = manager.get_collection_stats()

    print("\n" + "=" * 80)
    print("TRIMMED RE-INGESTION COMPLETED")
    print("=" * 80)
    print(f"IND-DRUG-001 Old Chunks:      {old_chunks_count}")
    print(f"IND-DRUG-001 New Chunks:      {len(chunks)} (reduction of {old_chunks_count - len(chunks)} noise chunks)")
    print(f"New National Chunks:          {stats['national_chunks']}")
    print(f"International Chunks:         {stats['international_chunks']}")
    print(f"New Total Chunks Overall:     {stats['total_chunks']}")
    print("=" * 80)


if __name__ == "__main__":
    reingest_dc_act_trimmed()
