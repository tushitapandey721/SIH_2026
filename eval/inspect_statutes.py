"""Inspect Section 2 formatting in Patents Act and Article formatting in International Treaties."""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.ingestion.extract import extract_native

# 1. Patents Act Section 2
p_path = Path("data/corpus/national/Patents_Act_1970.pdf")
if p_path.exists():
    text = extract_native(p_path)
    m = re.search(r"(?:2\.\s+Definitions|Section\s+2\b)(.*?)(?:3\.\s+What\s+are\s+not|Section\s+3\b)", text, re.DOTALL | re.IGNORECASE)
    if m:
        sec2_text = m.group(0)
        print("=== Patents Act Section 2 Sample ===")
        print(sec2_text[:600])
        # Find subclauses like (j), (ja), (l), (ta)
        clauses = re.findall(r"(?m)^\s*(\([a-z0-9]+\))\s*([^\n]+)", sec2_text)
        print(f"\nFound {len(clauses)} subclauses in Section 2:")
        for c_id, c_head in clauses[:15]:
            print(f"  • {c_id}: {c_head.strip()[:70]}")

# 2. International Treaties
for name in ["Nagoya", "TRIPS", "CBD", "PCT"]:
    for p in Path("data/corpus/international").rglob(f"*{name}*.pdf"):
        t = extract_native(p)
        art_matches = re.findall(r"(?im)^\s*(?:Article|Art\.)\s+(\d+[A-Za-z]?)[\.\:\s—–\-]+([^\n]{2,60})", t)
        print(f"\n=== {p.name} ===")
        print(f"Found {len(art_matches)} Article markers:")
        for a_num, a_title in art_matches[:8]:
            print(f"  • Article {a_num}: {a_title.strip()}")
