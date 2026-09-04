"""Test script for evaluating PDF extraction against all manifest documents."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.manifest import load_manifest
from app.ingestion.extract import extract_document, locate_corpus_file


def run_corpus_extraction_test():
    manifest_records = load_manifest()
    results = []
    failed_or_flagged = []

    print("=" * 90)
    print(f"{'ID':<12} | {'Method':<8} | {'Chars':<8} | {'Status':<8} | {'Filename'}")
    print("=" * 90)

    for item in manifest_records:
        doc_id = item["id"]
        filename = item["filename"]
        jurisdiction = item["jurisdiction"]

        pdf_path = locate_corpus_file(filename)
        if not pdf_path or not pdf_path.exists():
            print(f"{doc_id:<12} | {'N/A':<8} | {'0':<8} | {'MISSING':<8} | {filename}")
            failed_or_flagged.append({
                "id": doc_id,
                "filename": filename,
                "reason": "File not found in corpus folders",
                "chars": 0
            })
            continue

        try:
            cleaned_text, method = extract_document(pdf_path)
            char_count = len(cleaned_text)
            status = "OK" if char_count >= 500 else "FLAGGED"

            if status == "FLAGGED":
                failed_or_flagged.append({
                    "id": doc_id,
                    "filename": filename,
                    "reason": f"Under 500 characters extracted ({char_count} chars)",
                    "chars": char_count
                })

            print(f"{doc_id:<12} | {method:<8} | {char_count:<8} | {status:<8} | {pdf_path.name}")
            results.append({
                "id": doc_id,
                "filename": pdf_path.name,
                "jurisdiction": jurisdiction,
                "method": method,
                "char_count": char_count,
                "status": status,
            })
        except Exception as e:
            print(f"{doc_id:<12} | {'ERROR':<8} | {'0':<8} | {'FAILED':<8} | {filename} (Error: {e})")
            failed_or_flagged.append({
                "id": doc_id,
                "filename": filename,
                "reason": str(e),
                "chars": 0
            })

    print("=" * 90)
    print(f"\nSummary: {len(results)} processed, {len(failed_or_flagged)} flagged/failed.")

    if failed_or_flagged:
        print("\nFlagged / Failed Documents (< 500 chars or missing):")
        for f in failed_or_flagged:
            print(f" - [{f['id']}] {f['filename']}: {f['reason']}")
    else:
        print("\nAll documents successfully extracted above the 500-character threshold!")

    return results, failed_or_flagged


if __name__ == "__main__":
    run_corpus_extraction_test()
