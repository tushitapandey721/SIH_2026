"""Re-ingest entire legal corpus with enhanced Section 2 definition chunks and Treaty Articles."""

import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# Remove old qdrant_data and sidecars to ensure clean state
qdrant_dir = PROJECT_ROOT / "qdrant_data"
sidecars_dir = PROJECT_ROOT / "data" / "sidecars"

if qdrant_dir.exists():
    shutil.rmtree(qdrant_dir, ignore_errors=True)
if sidecars_dir.exists():
    shutil.rmtree(sidecars_dir, ignore_errors=True)

from app.retrieval.store import VectorStoreManager

print("Initializing VectorStoreManager and starting clean ingestion...")
manager = VectorStoreManager()
stats = manager.ingest_all(force=True, batch_size=32)
print("Re-ingestion finished successfully!")
print("Stats:", stats)
