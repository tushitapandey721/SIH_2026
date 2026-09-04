import requests
import json

sample_answer = (
    "Under Section 3(p) of the Patents Act, 1970, classical Ayurvedic formulations are not patentable "
    "because traditional knowledge belongs to the public domain. However, a novel, non-obvious synergistic "
    "herbal combination with proven experimental efficacy may be considered under Section 3(e). "
    "This is informational guidance, not legal advice."
)

sample_citations = [
    {"source": "Patents Act, 1970", "section": "Section 3(p)", "title": "Patents Act, 1970"},
    {"source": "Patents Act, 1970", "section": "Section 3(e)", "title": "Patents Act, 1970"},
]

languages = [
    ("en", "English", "Latin"),
    ("hi", "Hindi", "Devanagari"),
    ("pa", "Punjabi", "Gurmukhi"),
    ("ml", "Malayalam", "Malayalam"),
    ("ta", "Tamil", "Tamil"),
]

print("=" * 70)
print("TESTING POST /translate ON ALL 5 TARGET LANGUAGES")
print("=" * 70)

results = {}

for code, name, script in languages:
    payload = {
        "answer_text": sample_answer,
        "citations": sample_citations,
        "target_language": code,
    }
    
    res = requests.post("http://127.0.0.1:8000/translate", json=payload, timeout=20)
    assert res.status_code == 200, f"Failed for {code}: {res.status_code} {res.text}"
    
    data = res.json()
    trans_text = data.get("translated_text", "")
    ret_citations = data.get("citations", [])
    
    assert trans_text, f"Empty translation for {code}"
    assert data.get("target_language") == code, f"Target language mismatch: {data.get('target_language')}"
    # Citations must remain untranslated and identical
    assert ret_citations == sample_citations, f"Citations modified for {code}!"
    
    results[code] = {
        "name": name,
        "script": script,
        "translated_text": trans_text,
    }
    
    print(f"\n[{code.upper()} - {name} ({script} script)]")
    print(f"Preserved Citations count: {len(ret_citations)}")
    print(f"Translated Text:\n{trans_text}\n")
    print("-" * 50)

print("\n>>> ALL 5 LANGUAGES TRANSLATED SUCCESSFULLY WITH INTACT CITATIONS! <<<")
