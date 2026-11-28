---
name: verify-run-outputs
description: Mandatory output guard for every Maestro test run (Android and iOS, every device in the matrix). Invoke after EVERY run, and whenever test outputs are generated, checked or reported. Verifies the dated/cycle-numbered per-run folder convention in every output category (screenshots, recordings, trace, report, video, issues), that nothing was skipped for any test case, and highlights variances for human review.
---

# verify-run-outputs

Invoke this skill after **every** test run on **either platform and every device**. Never report a run as finished without it.

## Output convention: one folder PER RUN inside EACH category
```
runs/screenshots/<RUN>/   NN_TCxx_short-title_PASS|FAIL.png
runs/recordings/<RUN>/    NN_TCxx_short-title.mp4
runs/trace/<RUN>/         NN_TCxx_short-title/  (+ NN_..log)    Maestro commands, logs, hierarchy, failure shots
runs/report/<RUN>/        junit/, results.json, summary.md, run-info.json, output-check.md|json
runs/video/<RUN>/         <RUN>_summary.mp4   (<= 60 s narrated summary)
runs/issues/<RUN>/        index.md, issues.json, NN_TCxx_short-title_step-SSS_<flow-part>/ per failed test,
                          00_output-check_variances/ when the guard finds variances; triage.md|json (machine triage)
runs/matrix/<date>_<time>_cycle-NN/summary.md                    device x test table (matrix runs)

<RUN> = YYYY-MM-DD_HHMMSS_cycle-NN_<android|ios>[_<device-id>]
```
- Date = the date the cycle started (a matrix cycle that runs past midnight keeps it) + start time of the run; `cycle-NN` = run cycle counter that **restarts at 01 every date**. All devices of one matrix run share one cycle number, so different cycles never mix.
- `NN` inside a run = test sequence (01, 02, ...), no gaps. `TCxx_short-title` comes from the flow file name / title.
- No loose files directly in a category folder; everything lives in a `<RUN>` subfolder.

## Steps
1. Runs are made with `./scripts/run-android-report.sh` (one device), `./scripts/run-matrix.sh` (all devices in `config/devices.csv`), or `./scripts/run-ios-report.sh` (same convention). They call the guard automatically.
   One test only: `TC=TC07 ./scripts/run-android-report.sh` (or the iOS script). Report such a run as **partial**;
   it never stands in for a full suite run.
2. Always (re)run the guard yourself for every run just produced and read the result:
   `python3 -I scripts/verify_run_outputs.py <RUN>`
3. Read `runs/report/<RUN>/output-check.md`. Exit code 0 = all outputs present; 1 = variances.
4. For every failed test open `runs/issues/<RUN>/index.md` and report test case, step, part of the flow and failed command.
   (Missing folder: `python3 -I scripts/collect_issues.py <RUN>`.) Then report to the user, never silently skipping: the run name(s), pass/fail counts, device and OS, and every variance flagged :warning:
   (missing/empty screenshot, recording, trace or report; naming, sequence or cycle-number breaks; failed test without failure screenshot; loose files; video missing or over 60 s).
   Then, if any test failed, invoke the triage-machine-failures skill and include its labels.
5. Do not fix variances by renaming or fabricating files. Fix the cause (script/device), rerun, and say which run is authoritative.
6. The user reviews outputs themselves: end with the run name(s), folder paths and the variance list (or "no variances").
