# Dash spike re-run on Python 3.14 (ticket 22)

Reuses the ticket 17 app unchanged: `../17-dash-cytoscape-spike/app.py` (copy it here, or run it in place; it regenerates `synthetic_graph.json` next to itself).

    uv python install 3.14.8
    uv venv --python 3.14.8 .venv
    uv pip install -r requirements-py314.txt
    python -m compileall -q .venv/Lib/site-packages   # or install with --compile-bytecode

- `imports_check.py`: clean import + per-module import time (run with `-W default`).
- `leiden_check.py` / `leiden_hash.py`: seeded `RBConfigurationVertexPartition` run twice; hash of memberships for cross-process / cross-version comparison. Need `synthetic_graph.json` (created by importing `app`).
- `warn_check.py`: drives the normal callbacks via Flask's test client with Deprecation/Pending/FutureWarning as errors.
- `requirements-py314.txt`: exact versions resolved on 2026-10-04.
