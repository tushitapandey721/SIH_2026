"""Qdrant vector store management, BGE-M3 local embedding generation, and incremental manifest ingestion."""

import os
import sys
import time
import uuid
import yaml
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from app.ingestion.manifest import load_manifest
from app.ingestion.extract import extract_document, locate_corpus_file
from app.ingestion.chunk import chunk_document

# Constants
COLLECTION_NAME = "ip_sakti_corpus"
VECTOR_SIZE = 1024
DEFAULT_MODEL_NAME = "BAAI/bge-m3"
QDRANT_STORAGE_PATH = PROJECT_ROOT / "qdrant_data"
SIDECARS_DIR = PROJECT_ROOT / "data" / "sidecars"


def get_device() -> str:
    """Detects available hardware acceleration (CUDA vs CPU).
    Falls back to CPU if running in Hugging Face ZeroGPU or if FORCE_CPU is enabled.
    """
    if os.getenv("SPACES_ZERO_GPU") == "true" or os.getenv("FORCE_CPU") == "1":
        return "cpu"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return device


class VectorStoreManager:
    """Manages Qdrant vector database connection, embeddings, and corpus indexing."""

    def __init__(
        self,
        storage_path: Optional[str | Path] = None,
        model_name: str = DEFAULT_MODEL_NAME,
        collection_name: str = COLLECTION_NAME,
    ):
        self.storage_path = Path(storage_path) if storage_path else QDRANT_STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.collection_name = collection_name
        self.device = get_device()

        self._client: Optional[QdrantClient] = None
        self._model: Optional[SentenceTransformer] = None

    @property
    def client(self) -> QdrantClient:
        """Initializes and returns the Qdrant local client instance."""
        if self._client is None:
            self._client = QdrantClient(path=str(self.storage_path))
            self._ensure_collection()
        return self._client

    @property
    def model(self) -> SentenceTransformer:
        """Loads and returns the BAAI/bge-m3 embedding model on the detected device."""
        if self._model is None:
            print(f"Loading SentenceTransformer('{self.model_name}', device='{self.device}')...")
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
            except Exception:
                self._model = SentenceTransformer(self.model_name, device=self.device)
            # Bound sequence length to 512 tokens
            self._model.max_seq_length = 512
            print(f"Model {self.model_name} loaded successfully on {self.device} (max_seq_length={self._model.max_seq_length}).")
        return self._model

    def _ensure_collection(self) -> None:
        """Ensures that the Qdrant target collection exists with 1024-dim Cosine configuration."""
        existing_collections = [c.name for c in self._client.get_collections().collections]
        if self.collection_name not in existing_collections:
            print(f"Creating Qdrant collection '{self.collection_name}' (dim: {VECTOR_SIZE}, metric: Cosine)...")
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def compute_file_hash(self, file_path: Path) -> str:
        """Calculates SHA256 hash of a file for incremental caching."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_sidecar(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Reads sidecar YAML metadata if present."""
        sidecar_path = SIDECARS_DIR / f"{doc_id}.yaml"
        if sidecar_path.exists():
            try:
                with open(sidecar_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Warning reading sidecar {sidecar_path}: {e}")
        return None

    def save_sidecar(self, doc_id: str, data: Dict[str, Any]) -> None:
        """Writes sidecar YAML metadata."""
        SIDECARS_DIR.mkdir(parents=True, exist_ok=True)
        sidecar_path = SIDECARS_DIR / f"{doc_id}.yaml"
        with open(sidecar_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def ingest_all(self, force: bool = False, batch_size: int = 32) -> Dict[str, Any]:
        """Loops through manifest, extracts + chunks documents, batch-embeds on GPU, and upserts to Qdrant.

        Includes automatic CUDA OOM fallback to batch_size=8.

        Args:
            force: If True, re-indexes all documents regardless of hash match.
            batch_size: Initial batch size for model.encode().

        Returns:
            Dictionary with counts, device used, elapsed time, and summary statistics.
        """
        start_time = time.time()
        manifest_records = load_manifest()
        total_manifest_docs = len(manifest_records)
        processed_count = 0
        skipped_count = 0

        print("\n" + "=" * 80)
        print(f"STARTING CORPUS INGESTION ({total_manifest_docs} documents) | Device: {self.device}")
        if self.device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        print("=" * 80)

        for item_idx, item in enumerate(manifest_records, start=1):
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
            if not pdf_path or not pdf_path.exists():
                print(f"[{item_idx}/{total_manifest_docs}] SKIPPING {doc_id}: '{filename}' not found in corpus.")
                continue

            current_hash = self.compute_file_hash(pdf_path)
            sidecar = self.get_sidecar(doc_id)

            if not force and sidecar and sidecar.get("content_hash") == current_hash:
                recorded_chunks = sidecar.get("total_chunks", 0)
                print(f"[{item_idx}/{total_manifest_docs}] Skipping {doc_id} (hash unchanged: {current_hash[:8]}, {recorded_chunks} chunks).")
                skipped_count += 1
                continue

            cleaned_text, method = extract_document(pdf_path)
            chunks = chunk_document(cleaned_text, chunk_strategy=chunk_strategy)

            if not chunks:
                print(f"[{item_idx}/{total_manifest_docs}] WARNING: No chunks produced for {doc_id}. Skipping.")
                continue

            print(f"[{item_idx}/{total_manifest_docs}] Processing {doc_id}: {len(chunks)} chunks, embedding...")
            chunk_texts = [c["text"] for c in chunks]

            # Batch encode on GPU with OOM fallback handling
            try:
                embeddings = self.model.encode(
                    chunk_texts,
                    batch_size=batch_size,
                    show_progress_bar=True,
                    normalize_embeddings=True,
                )
            except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
                if "out of memory" in str(e).lower() and self.device == "cuda":
                    print(f"[{doc_id}] CUDA OOM encountered with batch_size={batch_size}. Clearing cache and retrying with batch_size=8 on CUDA...")
                    torch.cuda.empty_cache()
                    embeddings = self.model.encode(
                        chunk_texts,
                        batch_size=8,
                        show_progress_bar=True,
                        normalize_embeddings=True,
                    )
                else:
                    raise e

            # Build Qdrant points with exact payload fields
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

            # Upsert points to Qdrant in batches of 100
            for i in range(0, len(points), 100):
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points[i : i + 100],
                )

            # Save sidecar metadata
            sidecar_data = {
                "id": doc_id,
                "title": title,
                "jurisdiction": jurisdiction.lower(),
                "content_hash": current_hash,
                "total_chunks": len(chunks),
                "extraction_method": method,
                "last_ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            self.save_sidecar(doc_id, sidecar_data)
            processed_count += 1
            print(f"[{item_idx}/{total_manifest_docs}] Done {doc_id}: {len(chunks)} chunks indexed.")

        elapsed_time = time.time() - start_time
        stats = self.get_collection_stats()

        print("\n" + "=" * 80)
        print("INGESTION COMPLETED")
        print("=" * 80)
        print(f"Device Used:          {self.device}")
        if self.device == "cuda":
            print(f"GPU Model:            {torch.cuda.get_device_name(0)}")
        print(f"Processed Documents:  {processed_count}")
        print(f"Skipped Documents:    {skipped_count}")
        print(f"National Chunks:      {stats['national_chunks']}")
        print(f"International Chunks: {stats['international_chunks']}")
        print(f"Total Chunks Overall: {stats['total_chunks']}")
        print(f"Total Elapsed Time:   {elapsed_time:.2f} seconds ({elapsed_time / 60:.2f} minutes)")
        print("=" * 80)

        return {
            "device": self.device,
            "processed_documents": processed_count,
            "skipped_documents": skipped_count,
            "national_chunks": stats["national_chunks"],
            "international_chunks": stats["international_chunks"],
            "total_chunks": stats["total_chunks"],
            "elapsed_time_seconds": elapsed_time,
        }

    def get_collection_stats(self) -> Dict[str, int]:
        """Calculates exact chunk counts partitioned by jurisdiction."""
        try:
            total = self.client.count(collection_name=self.collection_name, exact=True).count
            national = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="jurisdiction", match=MatchValue(value="national"))]
                ),
                exact=True,
            ).count
            international = self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(key="jurisdiction", match=MatchValue(value="international"))]
                ),
                exact=True,
            ).count
        except Exception as e:
            print(f"Error fetching collection stats: {e}")
            total, national, international = 0, 0, 0

        return {
            "national_chunks": national,
            "international_chunks": international,
            "total_chunks": total,
        }


# Singleton manager instance
default_store_manager = VectorStoreManager()


def ingest_all(force: bool = False, batch_size: int = 32) -> Dict[str, Any]:
    """Convenience function to run corpus ingestion."""
    return default_store_manager.ingest_all(force=force, batch_size=batch_size)


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ingest_all()
