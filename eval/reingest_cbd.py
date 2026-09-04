"""Re-ingest CBD (INT-CBD-001) with Article chunking."""

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from app.ingestion.manifest import load_manifest
from app.ingestion.extract import extract_document, locate_corpus_file
from app.ingestion.chunk import chunk_document
from app.retrieval.store import VectorStoreManager, COLLECTION_NAME

manager = VectorStoreManager()
client = manager.client
model = manager.model

manifest = load_manifest()
for item in manifest:
    if item["id"] == "INT-CBD-001":
        doc_id = item["id"]
        title = item["title"]
        filename = item["filename"]
        jurisdiction = item["jurisdiction"]
        category = item["category"]
        authority = item["authority"]
        citation_prefix = item["citation_prefix"]
        priority = item["priority"]
        year = item["year"]
        chunk_strategy = item["chunk_strategy"]

        pdf_path = locate_corpus_file(filename)
        print(f"Re-ingesting {doc_id} ('{filename}')...")

        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="title", match=MatchValue(value=title))]
            ),
        )

        cleaned_text, method = extract_document(pdf_path)
        chunks = chunk_document(cleaned_text, chunk_strategy="article")
        print(f"Extracted {len(chunks)} chunks for CBD.")

        chunk_texts = [c["text"] for c in chunks]
        embeddings = model.encode(chunk_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

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
            client.upsert(collection_name=COLLECTION_NAME, points=points[i : i + 100])

        print(f"Upserted {len(points)} points for CBD.")
        break
