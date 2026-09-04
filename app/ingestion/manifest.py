"""Manifest loader and validator for IP-SAKTI Sahayak legal and regulatory corpus."""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "manifest.csv"


def load_manifest(manifest_path: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    """Loads the corpus manifest CSV into a list of dictionaries.

    Args:
        manifest_path: Optional custom path to manifest.csv. Defaults to /data/manifest.csv.

    Returns:
        List of dicts representing each document row in the manifest.
    """
    path = Path(manifest_path) if manifest_path else DEFAULT_MANIFEST_PATH

    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found at: {path}")

    records: List[Dict[str, Any]] = []
    with open(path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys and values
            cleaned_row = {k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
            records.append(cleaned_row)

    return records


def get_manifest_summary(records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, int]:
    """Computes summary statistics (such as jurisdiction counts) from the manifest.

    Args:
        records: Optional pre-loaded records list.

    Returns:
        Dictionary containing counts of national, international, and total documents.
    """
    if records is None:
        records = load_manifest()

    national_count = sum(1 for doc in records if doc.get("jurisdiction", "").lower() == "national")
    international_count = sum(1 for doc in records if doc.get("jurisdiction", "").lower() == "international")

    return {
        "national": national_count,
        "international": international_count,
        "total": len(records)
    }


if __name__ == "__main__":
    docs = load_manifest()
    summary = get_manifest_summary(docs)
    print(f"Loaded {summary['total']} total documents from manifest.")
    print(f"National documents: {summary['national']}")
    print(f"International documents: {summary['international']}")
