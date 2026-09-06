import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.retrieval.retrieve import get_default_retriever
from app.api.routes import execute_ask_pipeline, AskRequest

retriever = get_default_retriever()
q = "Is a classical Ayurvedic formulation patentable?"
print(f"Testing Query: '{q}'")

chunks, diag = retriever.retrieve(q, jurisdiction="national")
print(f"\nRetrieved {len(chunks)} chunks:")
for i, c in enumerate(chunks, 1):
    print(f"  {i}. [{c.get('title')}] {c.get('section')} (score={round(c.get('score', 0), 4)})")
    print(f"     {c.get('text', '')[:150]}...")

req = AskRequest(query=q, jurisdiction="national")
res = execute_ask_pipeline(req)
print(f"\nPipeline Result:")
print(f"  Confidence: {res.get('confidence')}")
print(f"  Abstained:  {res.get('abstained')}")
print(f"  Answer:     {res.get('answer')}")
print(f"  Citations:  {res.get('citations')}")
