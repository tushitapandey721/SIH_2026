"""Test refined Section marker pattern on Patents Act."""

import re
import sys
from pathlib import Path
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.ingestion.extract import extract_native, clean_text

p = Path("data/corpus/national/Patents Act, 1970.pdf")
text = clean_text(extract_native(p))

SECTION_RULE_PATTERN = re.compile(
    r"(?m)(?:^|\n\s*)("
    r"(?:Section|Sec\.)\s+\d+[A-Za-z]?(?:[\.\:\—–\-]+|\s+[A-Z][a-zA-Z0-9\s,\—–\-]{2,60}(?:\.|\—|\-)?)"
    r"|(?:Rule|Regulation|Reg\.)\s+\d+[A-Za-z]?(?:[\.\:\—–\-]+|\s+[A-Z][a-zA-Z0-9\s,\—–\-]{2,60}(?:\.|\—|\-)?|\b)"
    r"|\b\d+[A-Za-z]?\.\s+[A-Z][a-zA-Z0-9\s,—–\(\)\/]{2,60}(?:\.|\—|\-)?"
    r")"
)

matches = list(SECTION_RULE_PATTERN.finditer(text))
for idx, m in enumerate(matches):
    if "2. Definitions" in m.group(1):
        start_p = m.start()
        end_p = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sec2_text = text[start_p:end_p]
        print(f"=== Found Section 2: Length {len(sec2_text)} chars ===")
        print(f"Next section marker is: {repr(matches[idx+1].group(1))}")
        
        # Test subclause extraction
        sub_pattern = re.compile(r'(?m)(?:^|\n\s*)(\([a-z0-9]{1,3}\))\s*(?:[\"“]([^\"”\n]+)[\"”])?', re.IGNORECASE)
        sub_matches = list(sub_pattern.finditer(sec2_text))
        print(f"Total subclauses extracted from Section 2: {len(sub_matches)}")
        for sm in sub_matches:
            c_let = sm.group(1)
            c_term = sm.group(2) or ""
            print(f"  • {c_let} {c_term}")
        break
