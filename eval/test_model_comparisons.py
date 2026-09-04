import time
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

def compare_models(test_name: str, context: str, user_query: str):
    print("=" * 80)
    print(f"BENCHMARK SCENARIO: {test_name}")
    print(f"QUERY: \"{user_query}\"")
    print("=" * 80)
    
    user_prompt = (
        f"User Inquiry: {user_query}\n"
        f"Jurisdiction Scope: National\n"
        f"Classified Formulation Category: None (Legal Basis: Direct Inquiry)\n\n"
        f"RETRIEVED STATUTORY CONTEXT CHUNKS:\n"
        f"{context}\n\n"
        f"Please provide your legally grounded JSON response adhering strictly to all system rules."
    )
    
    models = [
        ("openai/gpt-oss-120b", "groq"),
        ("qwen/qwen3.8-27b", "groq"),
        ("mistral-small-latest", "mistral"),
    ]
    
    for model_id, prov in models:
        t0 = time.perf_counter()
        raw = ""
        try:
            if prov == "groq":
                raw = _call_groq(SYSTEM_PROMPT, user_prompt, max_tokens=1024, model=model_id)
            else:
                raw = _call_mistral(SYSTEM_PROMPT, user_prompt, max_tokens=1024, model=model_id)
            lat = (time.perf_counter() - t0) * 1000
            
            # parse json
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
            
            citations = [f"[{c.get('source', '')}] {c.get('section', '')}" for c in data.get("citations", [])]
            confidence = data.get("confidence", "unknown")
            answer = data.get("answer", "")
            
            print(f"[{model_id} ({prov.upper()})] (Latency: {lat:.1f}ms / {lat/1000:.2f}s)")
            print(f"  Confidence : {confidence}")
            print(f"  Citations  : {citations}")
            print(f"  Answer     : {answer[:250]}...\n")
        except Exception as e:
            print(f"[{model_id} ({prov.upper()})] Error: {e}\n")
        time.sleep(1)

def main():
    # Scenario 1: Section 3(p) Traditional Knowledge vs Section 3(d) Enhanced Efficacy
    context_1 = (
        "--- Source [1] ---\n"
        "Act/Treaty: Patents Act 1970\n"
        "Citation Prefix: Patents Act S.\n"
        "Section/Article: Section 3(p)\n"
        "Content: What are not inventions: (p) an invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components.\n\n"
        "--- Source [2] ---\n"
        "Act/Treaty: Patents Act 1970\n"
        "Citation Prefix: Patents Act S.\n"
        "Section/Article: Section 3(d)\n"
        "Content: What are not inventions: (d) the mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy of that substance or the mere discovery of any new property or new use for a known substance or of the mere use of a known process, machine or apparatus unless such known process results in a new product or employs at least one new reactant. Explanation.—For the purposes of this clause, salts, esters, ethers, polymorphs, metabolites, pure form, particle size, isomers, mixtures of isomers, complexes, combinations and other derivatives of known substance shall be considered to be the same substance, unless they differ significantly in properties with regard to efficacy."
    )
    q1 = "Can a novel, structurally modified synthetic derivative of a chemical compound found in an Ayurvedic plant be patented in India, and how do Section 3(p) and Section 3(d) apply?"
    compare_models("Section 3(p) vs Section 3(d) Distinction", context_1, q1)
    
    # Scenario 2: Rule 161 Labelling
    context_2 = (
        "--- Source [1] ---\n"
        "Act/Treaty: Drugs and Cosmetics Act 1940 and Rules 1945\n"
        "Citation Prefix: D&C Rules R. / D&C Act S.\n"
        "Section/Article: Rule 161\n"
        "Content: Rule 161 — Labelling, packing and limit of alcohol in Ayurvedic (including Siddha) or Unani drugs.—(1) There shall be conspicuously displayed on the label of the container or package of an Ayurvedic (including Siddha) or Unani drug—(a) a true list of all ingredients in respect of drugs other than Patent or Proprietary Medicines, together with the quantity of each ingredient, and in case of Patent or Proprietary Medicines, the true list of all active ingredients with the botanical name of each plant ingredient and part of the plant used; (b) the name of the drug as specified in the Ayurvedic (including Siddha) or Unani Pharmacopoeias or Ayurvedic, Siddha or Unani Formulary of India or authoritative books."
    )
    q2 = "What are the exact statutory labelling requirements for Ayurvedic patent and proprietary medicines under Rule 161?"
    compare_models("Rule 161 Ayurvedic Drug Labelling Requirements", context_2, q2)

if __name__ == "__main__":
    main()
