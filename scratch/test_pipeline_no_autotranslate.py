# -*- coding: utf-8 -*-
import requests

BASE_URL = "http://localhost:8000"

# 1. Normal English query
res = requests.post(f"{BASE_URL}/ask", json={"query": "Can I patent classical Ayurvedic medicine?", "jurisdiction": "national"})
data = res.json()
print("English query response language:", data.get("language"))
print("Answer starts with:", data.get("answer")[:120])
print("Auto-translated:", data.get("is_translated", False))

# 2. Hindi input query - query translation should still occur to English for retrieval, but answer returned in natural generated language
res2 = requests.post(f"{BASE_URL}/ask", json={"query": "क्या मैं शास्त्रीय आयुर्वेदिक दवा का पेटेंट करा सकता हूँ?", "jurisdiction": "national"})
data2 = res2.json()
print("\nHindi query response:")
print("Detected query language:", data2.get("language"))
print("Answer snippet:", data2.get("answer")[:150])
