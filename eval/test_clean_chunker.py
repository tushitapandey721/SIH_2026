import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding='utf-8')

from app.ingestion.extract import extract_dc_act_rules_targeted, extract_document
from app.ingestion.chunk import clean_legal_text, extract_section_markers, chunk_document

def test_full():
    # 1. D&C Rules
    dc_text = extract_dc_act_rules_targeted("data/corpus/national/2016DrugsandCosmeticsAct1940Rules1945.pdf")
    dc_chunks = chunk_document(dc_text, chunk_strategy="rule")
    print(f"Total D&C chunks produced: {len(dc_chunks)}")
    
    r161_chunks = [c for c in dc_chunks if "161" in c["section_id"] or "161" in c["text"][:100]]
    print(f"Rule 161 related chunks: {len(r161_chunks)}")
    for c in r161_chunks:
        print(f"  • ID: {c['section_id']}\n    Length: {len(c['text'])}\n    Preview: {c['text'][:250]}...\n")

    # 2. GI Act
    gi_file = Path("data/corpus/national/Geographical Indications of Goods.pdf")
    gi_text, _ = extract_document(gi_file)
    gi_chunks = chunk_document(gi_text, chunk_strategy="section")
    print(f"\nTotal GI chunks produced: {len(gi_chunks)}")
    
    sec8_chunks = [c for c in gi_chunks if "Section 8" in c["section_id"] or " 8." in c["text"][:30]]
    print(f"Section 8 related chunks: {len(sec8_chunks)}")
    for c in sec8_chunks:
        print(f"  • ID: {c['section_id']}\n    Length: {len(c['text'])}\n    Preview: {c['text'][:250]}...\n")

if __name__ == "__main__":
    test_full()
