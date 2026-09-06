import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.retrieval.retrieve import get_default_retriever
from app.api.routes import execute_ask_pipeline, AskRequest

retriever = get_default_retriever()

queries = [
    ("What are the rules regarding Prior Informed Consent under Nagoya Protocol Article 6?", "international"),
    ("What does Article 27.3(b) of TRIPS say about plant varieties and micro-organisms?", "international"),
    ("What are the mandatory disclosure requirements under Article 3 of the WIPO GRATK Treaty?", "international"),
    ("What are the provisions of Patent Cooperation Treaty Article 8 on claiming priority?", "international"),
    ("Can neem and turmeric traditional formulations be patented in India under Section 3(p)?", "national"),
]

for q, jur in queries:
    print(f"\n==================================================")
    print(f"QUERY: {q} [{jur}]")
    print(f"==================================================")
    chunks, _ = retriever.retrieve(q, jurisdiction=jur)
    for i, c in enumerate(chunks[:3], 1):
        print(f"  {i}. [{c.get('title')}] {c.get('section')}: score={round(c.get('score', 0), 4)}")
        print(f"     {c.get('text', '')[:100]}...")
    
    req = AskRequest(query=q, jurisdiction=jur)
    resp = execute_ask_pipeline(req)
    print(f"  -> Confidence: {resp.get('confidence')}")
    print(f"  -> Abstained:  {resp.get('abstained')}")
    print(f"  -> Provider:   {resp.get('provider_used')}")
    print(f"  -> Citations:  {resp.get('citations')}")
    print(f"  -> Answer:     {resp.get('answer', '')[:200]}...")
