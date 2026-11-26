---
name: triage-machine-failures
description: Watches for test failures that may be caused by the test machine rather than the app or the test (system "not responding" dialogs, device or driver timeouts, blank screen tree, overloaded or swapping host). Invoke after every Maestro run (Android or iOS) that has any failure, and whenever a failure is called flaky or environmental. Labels failures with evidence; never hides, deletes or passes them.
---

# triage-machine-failures

Every failure stays reported. This skill only answers "could the machine be the cause, and what is the evidence?".

## Steps
1. The run scripts call it automatically; always rerun it for the run at hand:
   `python3 -I scripts/triage_issues.py <RUN>`  (needs `collect_issues.py <RUN>` first)
2. Read `runs/issues/<RUN>/triage.md`, then **open the failure screenshot of every failure** and check the label agrees
   with what is on screen. The labels are heuristics.
3. Check the machine: `runs/report/<RUN>/host-metrics.tsv` (load, swap, memory per test), `environment.log`.
4. Report a table: test case, label, evidence, your own judgement, next step. State pass/fail counts **unchanged**.

## Labels
| Label | Meaning | What to do |
|---|---|---|
| APP_DEFECT_SUSPECTED | crash report, fatal exception, or the app itself not responding | report to the app team; never rerun it away |
| MACHINE_SUSPECT | system dialog, device/driver timeout or death, Maestro driver not starting, blank screen tree | fix the machine condition, rerun |
| POSSIBLE_MACHINE | only host overload / swapping, or a dismissed system dialog | check the screenshot, rerun on a quiet machine |
| NEEDS_REVIEW | no machine signal | treat as a real failure |

## Rules
- **A failure is only "invalid (machine)" after both:** machine evidence in this run **and** the same unchanged test
  passing in a rerun on a healthy machine. A rerun alone, or a label alone, is not enough. A human decides.
- Never change `results.json`, screenshots, junit files or issue folders; never delete a failed run. Add reviewer notes
  under "Triage" in `issue.md`.
- A test whose driver never started ran no commands: its end screenshot shows what an earlier test left behind.
- Put reviewer notes under "Triage (fill in)"; a triage rerun replaces everything from "Machine triage" down.
- A device timeout can also be a test design problem (e.g. typing too much in one step): say so when it repeats on a
  healthy machine.
- If the same machine signal appears in two runs, recommend a fix (settle step, fewer parallel devices, free memory,
  restart) instead of rerunning again.
- Thresholds are at the top of `scripts/triage_issues.py`; change them only when asked, and say so.
