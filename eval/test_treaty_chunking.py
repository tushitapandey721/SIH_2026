"""Test chunking on international treaties."""

import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.ingestion.extract import extract_native, clean_text
from app.ingestion.chunk import chunk_document

treaties = [
    ("Nagoya Protocol.pdf", "article"),
    ("trips_agreement.pdf", "article"),
    ("Convention on Biological Diversity (CBD).pdf", "article"),
    ("PCT (Patent Cooperation Treaty).pdf", "article"),
]

for filename, strategy in treaties:
    for p in Path("data/corpus/international").rglob(f"*{filename}*"):
        raw = extract_native(p)
        cleaned = clean_text(raw)
        chunks = chunk_document(cleaned, chunk_strategy=strategy)
        print(f"\n==================================================")
        print(f"Document: {p.name} -> Total Chunks: {len(chunks)}")
        print("Sample Section IDs:")
        for c in chunks[:12]:
            print(f"  • {c['section_id']}")
