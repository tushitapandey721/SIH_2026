"""Corpus ingestion, extraction, and chunking pipeline module."""

from app.ingestion.manifest import load_manifest, get_manifest_summary
from app.ingestion.extract import (
    has_text_layer,
    extract_native,
    extract_scanned,
    clean_text,
    extract_document,
    locate_corpus_file,
)
from app.ingestion.chunk import chunk_document

__all__ = [
    "load_manifest",
    "get_manifest_summary",
    "has_text_layer",
    "extract_native",
    "extract_scanned",
    "clean_text",
    "extract_document",
    "locate_corpus_file",
    "chunk_document",
]
