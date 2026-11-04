"""PROTOTYPE, throwaway. Dumps one stored ps-validation-1 run into PROTOTYPE-validation-layout.html (inlined),
with ticket 01/02's per-Cluster figures computed from the records (prototype-only).

Whole-Cluster Jaccard is a STAND-IN: |D'| is not stored, so it is approximated as Hennig's J x retention
(exact when the best match D' equals the surviving tags C'). Every other figure is real.

Run: .venv/Scripts/python -I .scratch/validation-review/prototypes/06-validation-layout/dump_validation.py <build_dir> <dataset> <g> <s>
"""
import csv, glob, json, math, sys
from pathlib import Path

build, dataset, g, s = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
names = {}
for f in (build / "datasets").glob("top100_*.csv"):
    for row in csv.DictReader(open(f, encoding="utf-8-sig")):
        for t, n in zip(row["tag_ids"].split(";"), row["tags"].split(";")):
            if t:
                names.setdefault(int(t), n)
run = None
for f in glob.glob(str(build / "app_cache/parameter_selection/validation/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    k = d["validation_key"]
    if k["grid_key"]["dataset"] == dataset and k["g"] == g and k["s"] == s:
        run = d
        break
assert run, "no such validation"
summ = run["summary"]
subs = [r for r in run["records"] if r["kind"] == "subsample"]


def wilson(k, n, z=1.959964):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - h), min(1.0, c + h)]


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def mean_se(xs):
    if not xs:
        return None, None
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    return m, sd / math.sqrt(len(xs))


arms = {}
for arm in ("reselected", "at_resolution"):
    base = summ["subsample"][arm]["clusters"]
    nondeg = [r["arms"][arm] for r in subs if not r["arms"][arm]["degenerate"]]
    out = []
    for i, c in enumerate(base):
        size = len(c["members"])
        hj, wj = [], []
        for a in nondeg:
            j, ret = a["jaccard"][i], a["retention"][i]
            surv = round((ret or 0) * size)
            wj.append((j or 0.0) * (ret or 0.0))  # stand-in
            if surv >= 2 and j is not None:
                hj.append(j)
        b = len(hj)
        m, se = mean_se(hj)
        wm, wse = mean_se(wj)
        k_diss = sum(1 for x in hj if x <= 0.5)
        k_rec = sum(1 for x in hj if x > 0.75)
        wi = wilson(k_diss, b)
        out.append({
            "label": c["label"], "members": [names.get(t, str(t)) for t in c["members"]], "size": size,
            "b": b, "s": len(nondeg),
            "mean": m, "se": se, "p10": pct(hj, .1), "p90": pct(hj, .9),
            "diss": k_diss, "diss_ci": wi, "rec": k_rec, "rec_ci": wilson(k_rec, b),
            "w_mean": wm, "w_se": wse, "w_p10": pct(wj, .1), "w_p90": pct(wj, .9),
            "retention": c["mean_retention"],
            "status": "not_assessable" if b == 0 else ("dissolved" if k_diss > b / 2 else None),
            "borderline": bool(wi and wi[0] <= .5 <= wi[1]),
            "rarely": b > 0 and b < len(nondeg) / 2,
            "old_dissolved": c["dissolved"],
        })
    arms[arm] = out
data = {"dataset": dataset, "g": g, "s": s, "build": build.name, "summary": summ, "clusters": arms}
import re
dest = Path(__file__).with_name("PROTOTYPE-validation-layout.html")  # inlined: the preview opens the file as a snapshot
blob = "<!--DATA--><script>window.DATA = " + json.dumps(data, ensure_ascii=False) + ";</script><!--/DATA-->"
html = dest.read_text(encoding="utf-8")
dest.write_text(re.sub(r"<!--DATA-->.*?<!--/DATA-->", lambda _: blob, html, flags=re.S), encoding="utf-8")
for arm, cs in arms.items():
    print(arm, [(c["label"], c["size"], c["b"], round(c["mean"] or 0, 3), c["diss"], c["status"], c["borderline"]) for c in cs])
