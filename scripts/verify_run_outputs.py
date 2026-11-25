#!/usr/bin/env python3
"""Output guard for one test run (Android or iOS). Exit 0 = all outputs present and conventional; 1 = variances.
Usage: verify_run_outputs.py <RUN_NAME> [runs_root=runs]
Layout checked (one folder per run inside EACH category):
  runs/{screenshots,recordings,trace,report,video,issues}/<YYYY-MM-DD_HHMMSS_cycle-NN_<platform>[_<device>]>/
Writes report/<RUN>/output-check.md + .json so a human can review variances."""
import json, re, sys, pathlib, subprocess
name = sys.argv[1]; root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "runs").resolve()
CATS = ("screenshots", "recordings", "trace", "report", "video", "issues")
d = {c: root / c / name for c in CATS}
issues, ok = [], []
def bad(m): issues.append(m)
def good(m): ok.append(m)

m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})_(\d{6})_cycle-(\d{2,3})_(android|ios)(?:_([a-z0-9-]+))?", name)
(good if m else bad)(f"run name '{name}' " + ("matches YYYY-MM-DD_HHMMSS_cycle-NN_<platform>[_<device>]" if m else "does NOT match YYYY-MM-DD_HHMMSS_cycle-NN_<platform>[_<device>]"))
for c in CATS:
    (good if d[c].is_dir() else bad)(f"{c}/{name}/ " + ("exists" if d[c].is_dir() else "MISSING"))
if m:  # cycle numbering: unique per date+device, no duplicates, restarts at 01 each date
    date, cyc = m.group(1), int(m.group(3))
    same = sorted(p.name for p in (root / "report").glob(f"{date}_*") if p.is_dir())
    cycles = sorted({int(re.search(r"_cycle-(\d+)_", n).group(1)) for n in same if re.search(r"_cycle-(\d+)_", n)})
    (good if cycles and cycles[0] == 1 and cycles == list(range(1, cycles[-1] + 1)) else bad)(
        f"cycle numbers for {date}: {cycles} " + ("start at 01 with no gaps" if cycles and cycles[0] == 1 and cycles == list(range(1, cycles[-1] + 1)) else "have a gap or do not start at 01 (variance)"))

rj = d["report"] / "results.json"; tests = []
if rj.exists(): tests = json.loads(rj.read_text())["tests"]; good("report/results.json present")
else: bad("report/results.json MISSING")
if not tests: bad("no test results recorded (nothing ran?)")

ne_file = lambda p: p.exists() and p.stat().st_size > 0
pat = re.compile(r"\d{2}_TC\d{2}_[a-z0-9][a-z0-9-]*")
ne = lambda p: p.exists() and p.stat().st_size > 0
for i, t in enumerate(tests, 1):
    n = t["name"]
    if not pat.fullmatch(n): bad(f"{n}: name does not follow NN_TCxx_short-title")
    if int(t["seq"]) != i: bad(f"{n}: sequence {t['seq']} expected {i:02d} (gap or reorder)")
    for label, p in (("screenshot", d["screenshots"] / f"{n}_{t['result']}.png"), ("recording", d["recordings"] / f"{n}.mp4"),
                     ("junit report", d["report"] / "junit" / f"{n}.xml")):
        (good if ne(p) else bad)(f"{n}: {label} " + ("ok" if ne(p) else f"MISSING or empty ({p.relative_to(root)})"))
    tr = d["trace"] / n; has = tr.is_dir() and any(tr.rglob("*"))
    (good if has else bad)(f"{n}: trace " + ("ok" if has else "MISSING or empty"))
    if t["result"] == "FAIL" and has and not any(tr.rglob("screenshots/*.png")):
        bad(f"{n}: FAIL but no Maestro failure screenshot in trace (variance, check manually)")
for c in ("screenshots", "recordings"):
    for p in (d[c].glob("*") if d[c].is_dir() else []):
        if not pat.match(p.stem.rsplit("_PASS", 1)[0].rsplit("_FAIL", 1)[0]): bad(f"{c}/{name}/{p.name}: unexpected file name")
# stray loose files directly inside category roots (mixing runs)
for c in CATS:
    for p in (root / c).glob("*") if (root / c).is_dir() else []:
        if p.is_file(): bad(f"{c}/{p.name}: loose file outside a run folder (runs would mix)")
# every failed test needs its own issue folder (built by collect_issues.py)
if d["issues"].is_dir():
    (good if ne_file(d["issues"] / "index.md") else bad)("issues/index.md " + ("ok" if ne_file(d["issues"] / "index.md") else "MISSING"))
    for t in tests:
        if t["result"] != "FAIL": continue
        found = [p for p in d["issues"].glob(f"{t['name']}_step-*") if ne_file(p / "issue.md")]
        (good if found else bad)(f"{t['name']}: issue folder " + (f"ok ({found[0].name})" if found else "MISSING"))
vids = list(d["video"].glob("*.mp4")) if d["video"].is_dir() else []
if vids:
    try:
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(vids[0])]).decode())
        (good if dur <= 60 else bad)(f"summary video {dur:.1f}s " + ("<= 60s" if dur <= 60 else "EXCEEDS 60s"))
    except Exception as e: bad(f"summary video not readable: {e}")
else: bad("summary video MISSING (video/<RUN>/*.mp4)")

# record the guard's own variances next to the test failures so all detected issues sit in one place
vd = d["issues"] / "00_output-check_variances"
if issues:
    vd.mkdir(parents=True, exist_ok=True)
    (vd / "issue.md").write_text(f"# Output check variances for {name}\n\n" + "".join(f"- {m}\n" for m in issues))
elif vd.is_dir():
    (vd / "issue.md").unlink(missing_ok=True); vd.rmdir()
d["report"].mkdir(parents=True, exist_ok=True)
(d["report"] / "output-check.json").write_text(json.dumps(dict(run=name, ok=len(ok), variances=issues, passed_checks=ok), indent=2))
md = [f"# Output check: {name}", "", f"**{'PASS' if not issues else 'VARIANCES FOUND'}**: {len(ok)} checks ok, {len(issues)} variance(s)", ""]
md += [f"- :warning: {x}" for x in issues] or ["- none"]
(d["report"] / "output-check.md").write_text("\n".join(md) + "\n")
print(("OUTPUT CHECK PASS" if not issues else "OUTPUT CHECK VARIANCES:\n  " + "\n  ".join(issues)), f"({len(ok)} ok)")
sys.exit(1 if issues else 0)
