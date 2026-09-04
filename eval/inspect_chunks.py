import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding='utf-8')

from app.ingestion.extract import extract_document
from app.ingestion.chunk import chunk_document

print("\n=== INSPECTING GI ACT (SECTION 8) ===")
gi_file = Path("data/corpus/national/Geographical Indications of Goods.pdf")
if gi_file.exists():
    gi_res = extract_document(gi_file)
    gi_text = gi_res[0] if isinstance(gi_res, tuple) else gi_res
    print("GI Text Length:", len(gi_text))
    gi_chunks = chunk_document(gi_text)
    print("Total GI Chunks:", len(gi_chunks))
    for i, c in enumerate(gi_chunks):
        sec = c["section_id"]
        txt = c["text"]
        if "Section 8" in sec or "8." in sec or "Section 8" in txt or "authorised user" in txt.lower() or "application for registration" in txt.lower():
            print(f"Chunk {i:3d} | Section ID: {sec:<45} | Length: {len(txt):4d} | Text: {txt[:120].strip()}...")
