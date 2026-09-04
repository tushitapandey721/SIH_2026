"""Test script for evaluating document chunking and section extraction across all corpus PDFs."""

import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.manifest import load_manifest
from app.ingestion.extract import extract_document, locate_corpus_file
from app.ingestion.chunk import chunk_document


def run_chunking_sanity_check():
    manifest_records = load_manifest()
    total_corpus_chunks = 0

    print("=" * 100)
    print("LEGAL CORPUS CHUNKING SANITY CHECK (17 DOCUMENTS)")
    print("=" * 100)

    for item in manifest_records:
        doc_id = item["id"]
        title = item["title"]
        filename = item["filename"]
        strategy = item["chunk_strategy"]
        jurisdiction = item["jurisdiction"]

        pdf_path = locate_corpus_file(filename)
        if not pdf_path or not pdf_path.exists():
            print(f"\n[!] SKIPPING {doc_id}: File '{filename}' not found.")
            continue

        cleaned_text, _ = extract_document(pdf_path)
        chunks = chunk_document(cleaned_text, chunk_strategy=strategy)
        total_corpus_chunks += len(chunks)

        print(f"\n[{doc_id}] {title} ({jurisdiction.upper()})")
        print(f"File: {pdf_path.name} | Strategy: {strategy} | Produced Chunks: {len(chunks)}")
        print("-" * 100)

        # Print 2 sample chunks (first and middle)
        if len(chunks) == 1:
            samples = [chunks[0]]
        elif len(chunks) == 2:
            samples = [chunks[0], chunks[1]]
        else:
            samples = [chunks[0], chunks[len(chunks) // 2]]

        for i, sample in enumerate(samples, start=1):
            sec_id = sample["section_id"]
            preview = sample["text"][:160].replace("\n", " ") + "..." if len(sample["text"]) > 160 else sample["text"].replace("\n", " ")
            print(f"  Sample {i} -> [{sec_id}] ({len(sample['text'])} chars): \"{preview}\"")

    print("\n" + "=" * 100)
    print(f"TOTAL CHUNKS PRODUCED ACROSS ENTIRE CORPUS: {total_corpus_chunks}")
    print("=" * 100)


if __name__ == "__main__":
    run_chunking_sanity_check()
