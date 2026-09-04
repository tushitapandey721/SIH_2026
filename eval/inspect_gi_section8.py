import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding='utf-8')

from app.ingestion.extract import extract_document
from app.ingestion.chunk import chunk_document

gi_file = Path("data/corpus/national/Geographical Indications of Goods.pdf")
gi_res = extract_document(gi_file)
gi_text = gi_res[0] if isinstance(gi_res, tuple) else gi_res

print("=== SEARCHING FOR SECTION 8 IN RAW GI ACT TEXT ===")
matches = [m.start() for m in re.finditer(r"\b8\.\s+|\bSection\s+8\b", gi_text, re.IGNORECASE)]
for pos in matches:
    snippet = gi_text[max(0, pos-50):min(len(gi_text), pos+300)]
    print("-" * 60)
    print(snippet)

print("\n=== SEARCHING FOR SECTION 8 IN GI CHUNKS ===")
gi_chunks = chunk_document(gi_text)
for i, c in enumerate(gi_chunks):
    if "Section 8." in c["section_id"] or "Section 8 " in c["section_id"] or c["section_id"] == "Section 8" or "Section 8." in c["text"][:100]:
        print(f"FOUND CHUNK {i}: [{c['section_id']}]\n{c['text'][:300]}")
