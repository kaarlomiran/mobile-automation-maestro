#!/usr/bin/env python3
"""Consolidate one matrix run: tests x devices table in <matrix dir>/summary.md (and summary.json)."""
import json, sys, pathlib
m = pathlib.Path(sys.argv[1]); rows = []
for line in (m / "runs.tsv").read_text().splitlines():
    p = line.split("\t")
    if len(p) < 2: continue
    dev, rundir = p[0], p[1]
    if rundir in ("BOOT_FAILED", ""): rows.append((dev, None, None)); continue
    r = pathlib.Path("runs/report") / rundir; rj = r / "results.json"; oc = r / "output-check.json"
    rows.append((dev, json.loads(rj.read_text()) if rj.exists() else None, json.loads(oc.read_text()) if oc.exists() else None))
tcs = sorted({t["tc"] + " " + t["short"] for _, res, _ in rows if res for t in res["tests"]})
md = [f"# Device matrix run {m.name}", "", "| Device | Passed | Failed | Output check | Run folder |", "|---|---|---|---|---|"]
for dev, res, oc in rows:
    if not res: md.append(f"| {dev} | - | - | BOOT/RUN FAILED | - |"); continue
    chk = "PASS" if oc and not oc["variances"] else f"{len(oc['variances'])} variance(s)" if oc else "missing"
    md.append(f"| {dev} | {res['passed']}/{res['total']} | {res['failed']} | {chk} | runs/*/{res['run_id']} |")
md += ["", "## Test x device", "", "| Test | " + " | ".join(d for d, _, _ in rows) + " |", "|---|" + "---|" * len(rows)]
for tc in tcs:
    cells = []
    for _, res, _ in rows:
        t = next((t for t in (res or {"tests": []})["tests"] if t["tc"] + " " + t["short"] == tc), None)
        cells.append(t["result"] if t else "-")
    md.append(f"| {tc} | " + " | ".join(cells) + " |")
(m / "summary.md").write_text("\n".join(md) + "\n"); print(f"Matrix summary: {m/'summary.md'}")
