import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.retrieval.retrieve import get_default_retriever
from app.api.routes import execute_ask_pipeline, AskRequest

r = get_default_retriever()
q = 'Is a classical Ayurvedic polyherbal formulation (such as Triphala churnam or Chyawanprash) patentable under Indian Patent Law?'

print("=== 1. RETRIEVAL TEST ===")
res, profile = r.retrieve(q, jurisdiction='all')
print(f"Chunks retrieved: {len(res)}")
for i, c in enumerate(res[:6]):
    print(f"[{i+1}] Title: {c.get('title')} | Section: {c.get('section')} | Score: {c.get('score')}")
    print(f"    Snippet: {c.get('text', '')[:140]}...\n")

print("=== 2. PIPELINE EXECUTION TEST ===")
req = AskRequest(query=q, jurisdiction='all')
out = execute_ask_pipeline(req)
print(f"Classification: {out.get('classification')}")
print(f"Confidence: {out.get('confidence')}")
print(f"Abstained: {out.get('abstained')}")
print(f"Answer:\n{out.get('answer')}")
print(f"Citations: {out.get('citations')}")
