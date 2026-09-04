"""Test enhanced chunking for Section 2 definitions and Treaty articles."""

import re
import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.ingestion.extract import extract_native, clean_text

# Test Section 2 subclause extraction on Patents Act 1970
p_path = Path("data/corpus/national/Patents Act, 1970.pdf")
text = clean_text(extract_native(p_path))

# Pattern for Section 2
m = re.search(r"(?:2\.\s+Definitions|Section\s+2\b)(.*?)(?:3\.\s+What\s+are\s+not|CHAPTER\s+II)", text, re.DOTALL | re.IGNORECASE)
sec2_text = m.group(0)

# Subclause pattern capturing (a), (j), (ja), (l), (ta) with optional definition term
sub_pattern = re.compile(r'(?m)(?:^|\n\s*)(\([a-z0-9]{1,3}\))\s*(?:[\"“]([^\"”\n]+)[\"”])?', re.IGNORECASE)
matches = list(sub_pattern.finditer(sec2_text))
print(f"=== Patents Act Section 2 Sub-Clauses ({len(matches)} found) ===")
for idx, match in enumerate(matches):
    clause_letter = match.group(1).strip("()")
    term = match.group(2)
    start_p = match.start()
    end_p = matches[idx + 1].start() if idx + 1 < len(matches) else len(sec2_text)
    clause_body = sec2_text[start_p:end_p].strip()
    
    label = f"Section 2(1)({clause_letter})" + (f' "{term}"' if term else "")
    if clause_letter in ["j", "ja", "l", "ta", "ac", "w"]:
        print(f"  • [{label}] -> {clause_body[:100]}...\n")

# Test Treaty Article extraction
treaties = [
    ("Nagoya Protocol.pdf", "Nagoya Protocol"),
    ("trips_agreement.pdf", "TRIPS Agreement"),
    ("Convention on Biological Diversity (CBD).pdf", "CBD"),
    ("PCT (Patent Cooperation Treaty).pdf", "PCT"),
]

art_pattern = re.compile(r"(?im)(?:^|\n\s*)(?:ARTICLE|Article|Art\.)\s+(\d+[A-Za-z]?)(?:[\.\:\s—–\-]+([^\n]{2,80}))?")

for filename, doc_name in treaties:
    for p in Path("data/corpus/international").rglob(f"*{filename}*"):
        raw = clean_text(extract_native(p))
        art_matches = list(art_pattern.finditer(raw))
        print(f"=== {doc_name} Articles ({len(art_matches)} found) ===")
        for idx, match in enumerate(art_matches[:8]):
            art_num = match.group(1)
            art_title = match.group(2) or ""
            label = f"Article {art_num}" + (f": {art_title.strip()}" if art_title else "")
            print(f"  • {label}")
