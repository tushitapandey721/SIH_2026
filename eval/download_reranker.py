"""Download BAAI/bge-reranker-v2-m3 weights with live progress."""

import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from huggingface_hub import hf_hub_download, snapshot_download

# Clean up any corrupt .incomplete blobs
blobs_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--BAAI--bge-reranker-v2-m3" / "blobs"
if blobs_dir.exists():
    for f in blobs_dir.glob("*.incomplete"):
        try:
            print(f"Removing stale incomplete download: {f.name} ({f.stat().st_size / (1024*1024):.1f} MB)")
            f.unlink()
        except Exception as e:
            print(f"Could not remove {f.name}: {e}")

print("\nStarting download of BAAI/bge-reranker-v2-m3 snapshot...")
path = snapshot_download(
    repo_id="BAAI/bge-reranker-v2-m3",
    resume_download=True,
)
print(f"\nModel snapshot downloaded successfully to: {path}")
