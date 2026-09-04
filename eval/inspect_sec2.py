"""Inspect line structure of Section 2 in Patents Act 1970."""

import re
import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.ingestion.extract import extract_native

p_path = Path("data/corpus/national/Patents Act, 1970.pdf")
text = extract_native(p_path)

# Let's search for Section 2 start up to Section 3 start
m = re.search(r"(?:2\.\s+Definitions|Section\s+2\b)(.*?)(?:3\.\s+What\s+are\s+not|CHAPTER\s+II\s+INVENTIONS\s+NOT\s+PATENTABLE)", text, re.DOTALL | re.IGNORECASE)
if m:
    sec2_text = m.group(0)
    lines = [line.strip() for line in sec2_text.split("\n") if line.strip()]
    print(f"Total non-empty lines in Section 2: {len(lines)}")
    print("\n--- First 40 lines of Section 2 ---")
    for idx, l in enumerate(lines[:40], start=1):
        print(f"{idx:3d}: {l}")

    # Search for specific definitions: (j), (ja), (l), (ta)
    print("\n--- Key Definition Lines ---")
    for idx, l in enumerate(lines, start=1):
        if re.match(r"^\([a-z0-9]+\)\s*[\"\“]", l, re.IGNORECASE) or re.match(r"^\([a-z0-9]+\)\s+[a-z]", l):
            print(f"Line {idx:3d}: {l[:100]}")
