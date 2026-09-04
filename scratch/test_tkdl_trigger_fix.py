import requests

queries = [
    ("Is a classical Ayurvedic formulation patentable under Indian Patent Law?", True),
    ("Can I patent traditional knowledge?", True),
    ("My grandmother gave me a family recipe for a herbal oil, can I patent it?", True),
    ("What are the labeling requirements under Rule 161 of the Drugs and Cosmetics Rules?", False),
    ("What safety and efficacy proof is required for a new Ayurvedic drug vs classical medicine?", False),
    ("Does an Ayurvedic company need NBA approval before exporting Indian biological resources?", False),
]

for q, expected in queries:
    res = requests.post("http://127.0.0.1:8000/compliance/tkdl", json={"query": q}, timeout=10)
    data = res.json()
    triggered = data.get("triggered")
    print(f"Query: '{q[:45]}...' -> Triggered: {triggered} (Expected: {expected})")
    assert triggered == expected, f"Failed for query: {q}"

print("\n>>> ALL TKDL TRIGGER VERIFICATIONS PASSED!")
