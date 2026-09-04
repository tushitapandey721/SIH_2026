import time
import requests
import json
import sys
import os
from pathlib import Path
import dotenv

dotenv.load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from app.llm.client import _call_groq, _call_mistral
from app.llm.prompts import SYSTEM_PROMPT

BASE_URL = "http://127.0.0.1:8000"

def evaluate_models_on_query(query: str):
    print("=" * 80)
    print(f"QUERY: \"{query}\"")
    print("=" * 80)
    
    # 1. Fetch retrieved context from running server
    payload = {
        "query": query,
        "jurisdiction": "national",
        "formulation_answers": {},
        "conversation_id": None,
    }
    
    # Direct test of Groq openai/gpt-oss-120b vs Groq openai/gpt-oss-20b vs Mistral mistral-small-latest
    models_to_test = [
        ("openai/gpt-oss-120b", "groq"),
        ("openai/gpt-oss-20b", "groq"),
        ("mistral-small-latest", "mistral"),
    ]
    
    # First get context chunks from the live backend
    resp = requests.post(f"{BASE_URL}/ask/stream", json=payload, stream=True)
    final_data = {}
    for line in resp.iter_lines():
        if line and line.decode("utf-8").startswith("data: "):
            ev = json.loads(line.decode("utf-8")[6:])
            if ev.get("stage") == "complete":
                final_data = ev.get("data", {})
                
    print(f"Live Server Top Citations: {[c.get('section') for c in final_data.get('citations', [])]}")
    print(f"Live Server Provider Used: {final_data.get('provider_used')}")
    print(f"Live Server Answer Excerpt:\n{final_data.get('answer', '')[:250]}...\n")
    print("-" * 80)

def main():
    test_queries = [
        "What does Section 3(p) of the Patents Act prohibit, and how does it contrast with Section 3(d)?",
        "Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India?",
        "What are the labelling requirements for Ayurvedic drugs under Rule 161?",
    ]
    
    for q in test_queries:
        evaluate_models_on_query(q)
        time.sleep(1)

if __name__ == "__main__":
    main()

