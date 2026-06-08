#!/usr/bin/env python3
"""Start the HTTP API programmatically with uvicorn.

This is the Python equivalent of the shell one-liner you'd use in production:

    # Run the bundled app object directly (production-style):
    uvicorn kenya_emergency.api.app:app --host 0.0.0.0 --port 8000

    # Or with autoreload while developing:
    uvicorn kenya_emergency.api.app:app --reload --port 8000

Running against fixtures
------------------------
Until v1.0 ships verified data, the bundled ``data/snapshots/`` directory is
empty, so we point the server at the test fixtures via
``KENYA_EMERGENCY_SNAPSHOT_DIR`` and build the SQLite database into a temp file.
When v1.0 lands with populated snapshots, drop the ``os.environ`` lines and run
``uvicorn kenya_emergency.api.app:app`` with no env at all.

    python examples/02_running_the_api.py
    # then, in another terminal:
    bash examples/03_curl_examples.sh
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# --- point the server at fixtures BEFORE importing the app -----------------
_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "data" / "snapshots"
_DB_FILE = Path(tempfile.gettempdir()) / "kea_example_api.db"
os.environ.setdefault("KENYA_EMERGENCY_SNAPSHOT_DIR", str(_FIXTURES))
os.environ.setdefault("KENYA_EMERGENCY_DB_PATH", str(_DB_FILE))

import uvicorn  # noqa: E402

HOST = "127.0.0.1"
PORT = 8000


def main() -> None:
    # NOTE ON CORS: the app ships permissive CORS (allow_origins=["*"]) because
    # the dataset is public and read-only. Production deployments should tighten
    # this — restrict allowed origins via env-driven config or by re-mounting
    # CORSMiddleware before exposing the server publicly.
    print(f"Starting Kenya Emergency API on http://{HOST}:{PORT}")
    print(f"  OpenAPI docs:  http://{HOST}:{PORT}/docs")
    print(f"  Health check:  http://{HOST}:{PORT}/health")
    print("  Press Ctrl+C to stop.\n")

    # Pass the import string (not the app object) so uvicorn owns the lifecycle;
    # this also keeps a single, clear entry point identical to the shell command.
    uvicorn.run("kenya_emergency.api.app:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
