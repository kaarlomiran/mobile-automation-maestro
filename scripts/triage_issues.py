#!/usr/bin/env python3
"""Label each failure of one run: could the test machine be the cause? Usage: triage_issues.py <RUN_NAME> [runs_root=runs]

NEVER changes a result: every failure stays FAIL and stays reported. This only adds a label and the evidence for it.
Writes runs/issues/<RUN>/triage.md, triage.json and a 'Machine triage' section in each issue.md.

  APP_DEFECT_SUSPECTED  app crash report / fatal exception / the app itself not responding (outranks machine signals)
  MACHINE_SUSPECT       strong signal: system 'not responding' dialog, device/driver timeout or death, blank screen tree
  POSSIBLE_MACHINE      only supporting signals: overloaded or swapping host, a system dialog had to be dismissed
  NEEDS_REVIEW          no machine signal found: treat as a real failure"""
import json, re, sys, pathlib

LOAD_PER_CPU = 4.0          # 1-minute load average divided by CPU count
SWAP_GROWTH_MB = 1024       # macOS: swap added during one test (a high but steady swap figure is normal on macOS)
MIN_AVAILABLE_SHARE = 0.10  # Linux: available memory compared with physical memory
SUITE_WIDE_SHARE = 0.8      # this share of tests failing identically points at something common to the whole run
DEVICE_ERRORS = r"DEADLINE_EXCEEDED|DeviceServerDiedException|StatusRuntimeException: UNAVAILABLE|device (?:offline|not found)|Unable to launch driver|Maestro iOS driver did not start|Maestro Android driver did not start|MaestroDriverStartupException"
MARK = "\n<!-- machine-triage -->\n"

name = sys.argv[1]; root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "runs").resolve()
idir, rep, trace = root / "issues" / name, root / "report" / name, root / "trace" / name
issues = json.loads((idir / "issues.json").read_text())["issues"]
res = json.loads((rep / "results.json").read_text())
app_id = res.get("app_id", ""); app_word = "Wikipedia"

def read(p):
    try: return p.read_text(errors="ignore")
    except OSError: return ""

def labels(node, out):
    if isinstance(node, list):
        for n in node: labels(n, out)
    elif isinstance(node, dict):
        a = node.get("attributes", node)
        t = [a.get(k) for k in ("accessibilityText", "text", "resource-id") if isinstance(a.get(k), str) and a.get(k)]
        if t: out.append(" ".join(t))
        for k, v in node.items():
            if k != "attributes" and isinstance(v, (dict, list)): labels(v, out)
    return out

def host_samples():
    rows = [l.split("\t") for l in read(rep / "host-metrics.tsv").splitlines()[1:]]
    return [r for r in rows if len(r) == 7]

def suite_wide():
    keys = [(i["flow_part"], i["command"]) for i in issues]
    return {k for k in keys if keys.count(k) >= 3 and keys.count(k) >= SUITE_WIDE_SHARE * res["total"]}

samples, common = host_samples(), suite_wide()
env = read(rep / "environment.log").splitlines()
results = []
for i in issues:
    n = i["test"]; app, strong, weak = [], [], []
    if i.get("app_crash"): app.append("iOS crash report: " + i["app_crash"][:200])
    for f in trace.glob(f"{n}/**/device-logcat.txt"):
        if re.search(r"FATAL EXCEPTION[\s\S]{0,400}?Process: " + re.escape(app_id), read(f)): app.append("fatal exception of the app in logcat")
    trees = sorted(trace.glob(f"{n}/*/screen-hierarchy/*.json"))
    if trees:
        try: texts = labels(json.loads(read(trees[-1])), [])
        except ValueError: texts = None
        if texts is not None:
            for t in texts:
                m = re.search(r"([\w .]+?) (?:isn't responding|isn’t responding|keeps stopping|has stopped)", t)
                if not m: continue
                (app if app_word.lower() in m.group(1).lower() else strong).append(f"dialog on screen: '{m.group(0).strip()}'")
                break
            if len(texts) <= 1: strong.append("screen tree was blank at the failing step (test driver saw nothing)")
    logs = read(trace / f"{n}.log") + "".join(read(p) for p in trace.glob(f"{n}/**/maestro.log"))
    m = re.search(DEVICE_ERRORS, logs)
    if m: strong.append(f"device or driver error in the log: {m.group(0)}")
    for r in (r for r in samples if r[1].startswith(n)):
        load, ncpu, swap, total, avail = float(r[2]), int(r[3]), r[4], r[5], r[6]
        if load / ncpu >= LOAD_PER_CPU: weak.append(f"host load {load:.0f} on {ncpu} CPUs ({r[1].split(':')[-1]} test)")
        if total and avail and int(avail) / int(total) < MIN_AVAILABLE_SHARE: weak.append(f"host memory nearly full: {avail} of {total} MB available")
    used = [int(r[4]) for r in samples if r[1].startswith(n) and r[4] and not r[6]]
    if len(used) > 1 and used[-1] - used[0] >= SWAP_GROWTH_MB: weak.append(f"host swapping: swap grew {used[-1] - used[0]} MB during the test")
    weak += sorted({l.split("\t", 1)[1] for l in env if l.startswith(n + "\t")})
    if (i["flow_part"], i["command"]) in common: weak.append("same step failed in most tests of this run (common cause: environment, setup or app)")
    later = sorted(p.parent.name for p in (root / "report").glob(f"*_{res['platform']}_{res.get('device_id','')}/results.json")
                   if p.parent.name > name and any(t["tc"] == i["tc"] and t["result"] == "PASS" for t in json.loads(p.read_text())["tests"]))
    weak = list(dict.fromkeys(weak))
    verdict = ("APP_DEFECT_SUSPECTED" if app else "MACHINE_SUSPECT" if strong else
               "POSSIBLE_MACHINE" if any(w.startswith(("host ", "settle:")) for w in weak) else "NEEDS_REVIEW")
    action = {"APP_DEFECT_SUSPECTED": "Report to the app team with the crash evidence; do not rerun it away.",
              "MACHINE_SUSPECT": "Free or restart the machine, rerun, and compare. Keep this failure on record.",
              "POSSIBLE_MACHINE": "Check the screenshot, then rerun on a quiet machine before deciding.",
              "NEEDS_REVIEW": "Investigate as a real failure (app, test or data)."}[verdict]
    entry = dict(tc=i["tc"], test=n, folder=i["folder"], verdict=verdict, app_signals=app, machine_signals=strong,
                 supporting_signals=weak, passed_in_later_run=later[:1], action=action)
    results.append(entry)
    f = idir / i["folder"] / "issue.md"
    if f.exists():
        sec = ["## Machine triage (automatic; the test result stays FAIL)", f"- Label: **{verdict}**"]
        sec += [f"- App signal: {s}" for s in app] + [f"- Machine signal: {s}" for s in strong] + [f"- Supporting: {s}" for s in weak]
        sec += [f"- Same test passed later on this device: `{later[0]}` (code may differ between runs)"] if later else []
        sec += [f"- Next step: {action}"]
        f.write_text(read(f).split(MARK)[0].rstrip() + "\n" + MARK + "\n".join(sec) + "\n")

counts = {v: sum(r["verdict"] == v for r in results) for v in ("APP_DEFECT_SUSPECTED", "MACHINE_SUSPECT", "POSSIBLE_MACHINE", "NEEDS_REVIEW")}
(idir / "triage.json").write_text(json.dumps(dict(run=name, failed=len(results), counts=counts, host_samples=len(samples), failures=results), indent=2))
md = [f"# Failure triage for run {name}", "",
      f"All {len(results)} failure(s) remain FAIL. " + ", ".join(f"{k}: {v}" for k, v in counts.items() if v) if results else "No failures to triage.", ""]
if results:
    if not samples: md += ["Host load was not recorded for this run, so host-overload signals cannot appear.", ""]
    md += ["| Test case | Label | Evidence | Passed later? |", "|---|---|---|---|"]
    md += [f"| {r['tc']} | {r['verdict']} | {'; '.join(r['app_signals'] + r['machine_signals'] + r['supporting_signals']).replace('|', '/') or 'none'} | {r['passed_in_later_run'][0] if r['passed_in_later_run'] else 'no'} |" for r in results]
(idir / "triage.md").write_text("\n".join(md) + "\n")
print(f"Triage: " + (", ".join(f"{k}={v}" for k, v in counts.items() if v) or "no failures") + f" -> {idir/'triage.md'}")
