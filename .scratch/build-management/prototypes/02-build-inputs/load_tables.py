"""Time reading the extracted tables (gzipped CSV) back into rows: the cost a lightweight Snapshot would pay
instead of reading and parsing the raw archive. Usage: python load_tables.py out/<snapshot_id>"""
import csv, gzip, sys, time
from pathlib import Path

folder = Path(sys.argv[1])
started = time.perf_counter()
counts = {}
for path in sorted(folder.glob("*.csv.gz")):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        counts[path.name] = sum(1 for _ in csv.DictReader(f))
print(counts)
print(f"read all tables: {time.perf_counter() - started:.2f} s")
