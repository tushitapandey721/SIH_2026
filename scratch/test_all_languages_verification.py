# -*- coding: utf-8 -*-
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

SAMPLE_ANSWER = (
    "Under Section 3(p) of the Patents Act, 1970, an invention which in effect is traditional knowledge "
    "or which is an aggregation or duplication of known properties of traditionally known component or components "
    "is not an invention and is non-patentable. Furthermore, Section 3(e) excludes mere admixtures resulting only in the "
    "aggregation of the properties of the components. Therefore, a classical Ayurvedic medicine formulation cannot be patented."
)

SAMPLE_CITATIONS = [
    {"source": "Patents Act, 1970", "section": "Section 3(p)"},
    {"source": "Patents Act, 1970", "section": "Section 3(e)"}
]

LANGUAGES = [
    ("en", "English", "Latin", 0x0041, 0x007A),
    ("hi", "Hindi", "Devanagari", 0x0900, 0x097F),
    ("pa", "Punjabi", "Gurmukhi", 0x0A00, 0x0A7F),
    ("ml", "Malayalam", "Malayalam", 0x0D00, 0x0D7F),
    ("ta", "Tamil", "Tamil", 0x0B80, 0x0BFF)
]

def verify_script(text, start_cp, end_cp):
    count = sum(1 for ch in text if start_cp <= ord(ch) <= end_cp)
    return count

def main():
    results = {}
    print("Testing /translate endpoint across all 5 languages...\n")

    for code, name, script_name, start_cp, end_cp in LANGUAGES:
        payload = {
            "answer_text": SAMPLE_ANSWER,
            "citations": SAMPLE_CITATIONS,
            "target_language": code
        }
        res = requests.post(f"{BASE_URL}/translate", json=payload, timeout=40)
        if res.status_code != 200:
            print(f"FAILED {name} ({code}): HTTP {res.status_code}")
            continue

        data = res.json()
        translated_text = data.get("translated_text", "")
        returned_citations = data.get("citations", [])

        script_count = verify_script(translated_text, start_cp, end_cp) if code != "en" else len(translated_text)
        has_patents_act = "Patents Act, 1970" in translated_text or "Section 3(p)" in translated_text
        citations_intact = len(returned_citations) == 2 and returned_citations[0]["section"] == "Section 3(p)"

        results[code] = {
            "name": name,
            "script": script_name,
            "script_char_count": script_count,
            "citations_preserved_in_text": has_patents_act,
            "citations_object_intact": citations_intact,
            "sample_output": translated_text[:300] + "..." if len(translated_text) > 300 else translated_text
        }

    with open("scratch/translation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Verification complete. Results saved to scratch/translation_results.json")

if __name__ == "__main__":
    main()
