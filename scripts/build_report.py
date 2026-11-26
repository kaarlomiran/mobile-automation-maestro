#!/usr/bin/env python3
"""Build report/results.json and report/summary.md for one run folder."""
import json, sys, pathlib
root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "runs"); rep = root / "report" / sys.argv[1]
info = json.loads((rep / "run-info.json").read_text())
titles = (rep / ".titles.txt").read_text().splitlines() if (rep / ".titles.txt").exists() else []
tests = []
for i, line in enumerate((rep / ".rows.tsv").read_text().splitlines()):
    nn, tc, short, result, dur, tags, reason = (line.split("\t") + [""] * 7)[:7]
    tests.append(dict(seq=nn, tc=tc, short=short, name=f"{nn}_{tc}_{short}", result=result,
                      seconds=int(dur or 0), tags=[t.strip() for t in tags.strip("[]").split(",") if t.strip()],
                      title=titles[i] if i < len(titles) else "", reason=reason))
passed = sum(t["result"] == "PASS" for t in tests)
res = dict(info, total=len(tests), passed=passed, failed=len(tests) - passed,
           seconds=sum(t["seconds"] for t in tests), tests=tests)
(rep / "results.json").write_text(json.dumps(res, indent=2))
osline = f"iOS {info.get('ios','?')} ({info.get('simulator','')})" if info["platform"] == "ios" else f"Android {info.get('android','?')} (API {info.get('api','?')})"
md = [f"# Test run {info['run_id']}", "",
      f"- Platform: {info['platform']} | Device: {info.get('device_id','')} ({info['device']}, {info.get('device_class','')}) | {osline} | Screen {info.get('screen','?')} | App: {info['app_id']} {info['app_version']}",
      f"- Result: **{passed}/{len(tests)} passed**, {res['failed']} failed, {res['seconds']}s total",
      *([f"- Selection: **partial run**, {info['selection'].strip()} only"] if info.get("selection") else []), "",
      "| # | Test | Result | Time | Tags | Note |", "|---|---|---|---|---|---|"]
for t in tests:
    md.append(f"| {t['seq']} | {t['tc']} {t['short']} | {t['result']} | {t['seconds']}s | {', '.join(t['tags'])} | {t['reason']} |")
(rep / "summary.md").write_text("\n".join(md) + "\n")
print(f"Report: {passed}/{len(tests)} passed -> {rep/'summary.md'}")
