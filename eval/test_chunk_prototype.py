import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding='utf-8')

from app.ingestion.extract import extract_dc_act_rules_targeted, extract_document

# Test prototype chunker
def test_chunking_improvements():
    # 1. Test D&C Rules
    dc_text = extract_dc_act_rules_targeted("data/corpus/national/2016DrugsandCosmeticsAct1940Rules1945.pdf")
    
    # Pre-clean footnote brackets and marginal noise
    cleaned_dc = re.sub(r'(?m)^\s*\d+\[', '', dc_text)
    cleaned_dc = re.sub(r'\[\s*\d+\]', '', cleaned_dc)
    cleaned_dc = re.sub(r'\b\d+\[', '', cleaned_dc)
    cleaned_dc = re.sub(r'(?m)^\s*\d+\.\s+(?:Subs\.|Ins\.|Omitted)\s+by\s+.*$', '', cleaned_dc)

    # Let's inspect Rule 161 matches
    rule_161_match = re.search(r'(?m)(?:^|\n\s*)(?:PART\s+XVII[^\n]*\n+[^\n]*\n+)?(?:Rule\s+)?161\.\s*([^—–\n]+)[—–\s]+([\s\S]*?)(?=(?:\n\s*(?:Rule\s+)?161A|\n\s*(?:Rule\s+)?162|\n\s*PART\s+XVIII|\Z))', cleaned_dc)
    if rule_161_match:
        print("Rule 161 Found successfully!")
        title = rule_161_match.group(1).strip().rstrip(".] ")
        body = rule_161_match.group(2).strip()
        print(f"Title: {title}")
        print(f"Body length: {len(body)}")
        print(f"Body preview:\n{body[:350]}...")
    else:
        print("Rule 161 match failed in prototype.")

    # 2. Test GI Act
    gi_file = Path("data/corpus/national/Geographical Indications of Goods.pdf")
    gi_res = extract_document(gi_file)
    gi_text = gi_res[0] if isinstance(gi_res, tuple) else gi_res

    # Find substantive Section 8 (not TOC)
    sec_8_match = re.search(r'(?m)(?:^|\n\s*)8\.\s+Registration to be in respect of particular goods and area\.[—–\s]+([\s\S]*?)(?=(?:\n\s*9\.\s+Prohibition|\Z))', gi_text)
    if sec_8_match:
        print("\nGI Act Section 8 Found successfully!")
        body = sec_8_match.group(1).strip()
        print(f"Body length: {len(body)}")
        print(f"Body preview:\n{body[:350]}...")
    else:
        print("\nGI Act Section 8 match failed in prototype.")

test_chunking_improvements()
