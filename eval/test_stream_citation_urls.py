"""
Test SSE stream endpoint (/ask/stream) to verify citations in the final complete event contain URLs.
"""

import sys
import json
import urllib.request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

req = urllib.request.Request(
    "http://localhost:8000/ask/stream",
    data=json.dumps({"query": "What is Section 3(p) under Indian law?", "jurisdiction": "national"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

complete_payload = None
with urllib.request.urlopen(req, timeout=60) as resp:
    for line in resp:
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("data:"):
            data_json = line_str[5:].strip()
            try:
                parsed = json.loads(data_json)
                if parsed.get("stage") == "complete":
                    complete_payload = parsed.get("data")
                    break
            except Exception:
                pass

print("=" * 80)
print("STREAMING VERIFICATION FOR CITATION URLS")
print("=" * 80)
assert complete_payload is not None, "Did not receive complete stage from /ask/stream"
citations = complete_payload.get("citations", [])
print(f"Citations received in streaming complete event: {len(citations)}")
for cit in citations:
    print(f"  Section: {cit.get('section')} | Source: {cit.get('source')} | URL: {cit.get('url')}")
    assert cit.get("url") == "https://www.indiacode.nic.in/handle/123456789/1392", f"Unexpected URL: {cit.get('url')}"

print("\nSTREAMING CITATION URL TEST PASSED SUCCESSFULLY!")
print("=" * 80)
