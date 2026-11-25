#!/usr/bin/env python3
"""Collect every failed test of one run (Android or iOS) into its own issue folder.
Usage: collect_issues.py <RUN_NAME> [runs_root=runs]

  runs/issues/<RUN>/index.md, issues.json                      always written ("no failed tests" if clean)
  runs/issues/<RUN>/NN_TCxx_short-title_step-SSS_<flow-part>/  one per failed test
        issue.md, failure-step.png, end-screen.png, screen-hierarchy.json, recording.mp4, maestro.log, junit.xml, *.ips (iOS app crash)
  runs/issues/<RUN>/00_output-check_variances/issue.md         written by verify_run_outputs.py when it finds variances

SSS = Maestro's step number (same number as the step-SSS screenshot in the trace).
<flow-part> = the innermost page object / subflow that failed ("test-flow" if the step is in the test file itself)."""
import json, re, shutil, sys, pathlib

name = sys.argv[1]; root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "runs").resolve()
rep, trace = root / "report" / name, root / "trace" / name
res = json.loads((rep / "results.json").read_text())
out = root / "issues" / name; out.mkdir(parents=True, exist_ok=True)
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def describe(entry):
    """Readable text for a Maestro command, with variables already substituted when available."""
    cmd = (entry.get("metadata", {}).get("evaluatedCommand") or entry["command"])
    kind, body = next(iter(cmd.items()))
    def sel(s):
        parts = [f'{k.replace("Regex", "")} "{v}"' for k, v in s.items() if k.endswith("Regex")]
        return ", ".join(parts) or json.dumps(s)[:120]
    if kind == "assertConditionCommand":
        c = body.get("condition", {})
        for key, word in (("visible", "assert visible"), ("notVisible", "assert NOT visible")):
            if key in c: return f"{word}: {sel(c[key])}"
    if kind == "inputTextCommand":
        return f'type text ({len(body.get("text", ""))} characters)'
    if kind in ("tapOnElement", "scrollUntilVisible"):
        return f"{'tap on' if kind == 'tapOnElement' else 'scroll until visible'}: {sel(body.get('selector', {}))}"
    return kind


def crash_summary(path):
    """Signal and the app's own frames from a macOS .ips crash report."""
    try:
        b = json.loads(path.read_text().split("\n", 1)[1])
        frames = b.get("lastExceptionBacktrace") or b["threads"][b.get("faultingThread", 0)]["frames"]
        mine = [f"{f.get('symbol')} ({pathlib.Path(f['sourceFile']).name}:{f.get('sourceLine')})" for f in frames if f.get("sourceFile") and f.get("sourceLine")]
        return f"{b['exception'].get('type')} {b['exception'].get('signal', '')}: " + " <- ".join(mine[:3])
    except Exception as e:
        return f"crash report present, could not parse ({e})"


def failed_step(tdir):
    """-> (step number, command text, error message, [flow chain], step screenshot, hierarchy file) or None."""
    for cj in sorted(tdir.glob("*/commands.json")):
        entries = json.loads(cj.read_text()); chain = {}; hit = None
        # a command that crashed (e.g. device timeout) stays RUNNING instead of becoming FAILED
        bad = "FAILED" if any(e.get("metadata", {}).get("status") == "FAILED" for e in entries) else "RUNNING"
        for e in entries:
            md = e.get("metadata", {}); kind = next(iter(e["command"])); depth = md.get("depth", 0)
            if md.get("status") != bad: continue
            if kind == "runFlowCommand":
                src = e["command"][kind].get("sourceDescription")
                chain = {d: s for d, s in chain.items() if d < depth}
                if src: chain[depth] = src
            else:
                hit = (e, depth, [chain[d] for d in sorted(chain) if d < depth])
        if not hit: continue
        e, _, flows = hit; md = e["metadata"]; step = md.get("sequenceNumber", 0) + 1   # Maestro's step files are 1-based
        pick = lambda sub: next(iter(sorted((cj.parent / sub).glob(f"step-{step:03d}-*"))), None)
        error = md.get("error", {}).get("message", "") or ("command did not finish (crash or device timeout)" if bad == "RUNNING" else "")
        return step, describe(e), error, flows, pick("screenshots"), pick("screen-hierarchy")
    return None


issues = []
for t in (t for t in res["tests"] if t["result"] == "FAIL"):
    n = t["name"]; info = failed_step(trace / n)
    step, command, error, flows, shot, tree = info or (None, "unknown (no Maestro step data)", t.get("reason", ""), [], None, None)
    part = slug(pathlib.Path(flows[-1]).stem) if flows else ("test-flow" if info else "unknown")
    folder = f"{n}_step-{step:03d}_{part}" if step is not None else f"{n}_step-unknown_{part}"
    d = out / folder; d.mkdir(parents=True, exist_ok=True)
    copies = [("failure-step.png", shot), ("screen-hierarchy.json", tree),
              ("end-screen.png", root / "screenshots" / name / f"{n}_FAIL.png"),
              ("recording.mp4", root / "recordings" / name / f"{n}.mp4"),
              ("maestro.log", trace / f"{n}.log"), ("junit.xml", rep / "junit" / f"{n}.xml")]
    present = []
    for target, src in copies:
        if src and src.exists(): shutil.copyfile(src, d / target); present.append(target)
    crashes = sorted((trace / n / "crash").glob("*.ips"))
    for c in crashes:
        shutil.copyfile(c, d / c.name); present.append(c.name)
    crash = "; ".join(crash_summary(c) for c in crashes)
    path = " > ".join([t["tc"]] + [pathlib.Path(f).stem for f in flows])
    device = f"{res.get('device_id', res.get('device'))} ({res['platform']} {res.get('ios') or res.get('android', '?')})"
    md = [f"# {t['tc']} failed at step {step if step is not None else '?'}: {part}", "",
          "| Field | Value |", "|---|---|",
          f"| Run | `{name}` |", f"| Device | {device} |", f"| Test case | {t['tc']} {t['short']} |",
          f"| Purpose | {t.get('title', '')} |", f"| Failed step | {step if step is not None else 'unknown'} |",
          f"| Part of the flow | {path} |", f"| Failed command | {command.replace('|', chr(92) + '|')} |",
          f"| Error | {error.replace('|', chr(92) + '|')} |", f"| Duration | {t['seconds']} s |",
          *([f"| **App crashed** | {crash.replace('|', chr(92) + '|')} |"] if crash else []), "",
          "Evidence in this folder: " + (", ".join(present) or "none"),
          f"Full trace: `runs/trace/{name}/{n}/`", "",
          "## Triage (fill in)", "- Cause: app defect / test defect / environment / data", "- Notes:"]
    # keep a reviewer's triage notes if this is a re-run of the collector
    if not (d / "issue.md").exists(): (d / "issue.md").write_text("\n".join(md) + "\n")
    issues.append(dict(tc=t["tc"], test=n, step=step, flow_part=part, flow_path=path, command=command, error=error, app_crash=crash, folder=folder))

(out / "issues.json").write_text(json.dumps(dict(run=name, failed=len(issues), issues=issues), indent=2))
md = [f"# Issues for run {name}", "", f"{res['passed']}/{res['total']} tests passed. Failed tests: {len(issues)}.", ""]
if issues:
    md += ["| Test case | Step | Part of the flow | Failed command | Folder |", "|---|---|---|---|---|"]
    md += [f"| {i['tc']} | {i['step'] if i['step'] is not None else '?'} | {i['flow_path']} | {i['command'].replace('|', chr(92) + '|')}{' **(app crashed)**' if i['app_crash'] else ''} | `{i['folder']}/` |" for i in issues]
else:
    md.append("No failed tests in this run.")
(out / "index.md").write_text("\n".join(md) + "\n")
print(f"Issues: {len(issues)} failed test(s) -> {out}")
