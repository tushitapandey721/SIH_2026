import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding='utf-8')

from app.ingestion.extract import extract_document, extract_dc_act_rules_targeted
from app.ingestion.chunk import chunk_document

print("=== INSPECTING GI ACT CHUNKS 40 TO 60 ===")
gi_file = Path("data/corpus/national/Geographical Indications of Goods.pdf")
gi_text = extract_document(gi_file)[0]
gi_chunks = chunk_document(gi_text)
for i in range(min(len(gi_chunks), 60)):
    sec = gi_chunks[i]["section_id"]
    txt = gi_chunks[i]["text"]
    if "8" in sec or "9" in sec or "11" in sec or "17" in sec:
        print(f"GI Chunk {i:2d} | [{sec}] | len={len(txt)} | {txt[:100]}...")

print("\n=== INSPECTING D&C RULES (RULE 161) ===")
dc_text = extract_dc_act_rules_targeted("data/corpus/national/2016DrugsandCosmeticsAct1940Rules1945.pdf")
dc_chunks = chunk_document(dc_text)
for i, c in enumerate(dc_chunks):
    sec = c["section_id"]
    txt = c["text"]
    if "161" in sec or "Labelling" in sec:
        print(f"D&C Chunk {i:3d} | [{sec}] | len={len(txt)} | {txt[:120]}...")
