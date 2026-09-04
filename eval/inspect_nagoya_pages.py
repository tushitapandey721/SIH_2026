"""Inspect Nagoya Protocol page by page."""

import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import fitz

p = next(Path("data/corpus/international").rglob("*Nagoya*.pdf"))
doc = fitz.open(p)
print(f"Nagoya Protocol total pages: {len(doc)}")
for i in range(len(doc)):
    page_text = doc[i].get_text("text")
    lines = [l.strip() for l in page_text.split("\n") if l.strip()]
    for l_idx, l in enumerate(lines):
        if "ARTICLE" in l.upper():
            print(f"Page {i+1} line {l_idx}: {repr(l)}")
            # Print next 3 lines
            for next_l in lines[l_idx+1:l_idx+4]:
                print(f"    next: {repr(next_l)}")
