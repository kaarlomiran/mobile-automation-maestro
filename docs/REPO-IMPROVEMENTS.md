# Review of the suggested repo improvements

Source: a reviewer's chat, text pasted in on 2026-11-26.
Checked against `main` at `9ea043c`. The recommended changes were applied and tested on 2026-11-27.

## Summary

- Most of the review is accurate. Its practical points are worth carrying over, mostly in adapted form.
- The two new skills and the shared Android/iOS skill are not recommended.
- Everything recommended was covered by changes A-G, prepared before the review arrived.
- The review missed a larger problem: 10 of 17 test flows contain selectors, which breaks the page object rule.
- **Status: A-H applied and tested.** See [Applied and verified](#applied-and-verified).

## Suggestions

| # | Suggestion | Practical value | Verdict | Change |
|---|---|---|---|---|
| 1 | `heal.md` should invoke `verify-run-outputs` on its rerun | High: a fix can be reported without any output check | **Carry over, adapted** | A |
| 2 | Add a `plan-from-ticket` skill | Low: it restates the planner prompt and enforces nothing | **Skip**, use a check script | F (instead) |
| 3 | Add a `generate-flow-from-plan` skill | Low: same reason | **Skip**, use a check script | F (instead) |
| 4 | Merge the Android and iOS prompts into a shared skill | Limited: the files are short and differ little | **Skip**, check for drift | F (instead) |
| 5 | Add "Follow CLAUDE.md" to `planner.md` and `heal.md` | Low: Claude Code loads it anyway | **Carry over** (trivial) | B |
| 6 | Check that the paths named in `CLAUDE.md` exist | Medium: found outdated guidance | **Done**, carry over the fixes | C, D, E |

### 1. Output check on the heal rerun

- **Confirmed.** Neither `heal.md` mentions `verify-run-outputs`.
- **Why adapted:** adding that sentence alone is not enough. A plain `maestro test` rerun creates no run folder, so there is nothing to check.
- **Change:** the rerun you report must use the report script, then the output check, then triage if anything failed. A single-test filter (`TC=TC07`) keeps it quick.

### 2 and 3. New skills for planning and flow generation

- **Partly confirmed.** `ticket_status.py` already checks `source-sha` and scenario status. Heading format, flow tags, assertions and the page object rule are not checked by anything.
- **Why skip:** a skill is also written instructions, so it would not close that gap.
- **Instead:** `scripts/lint_suite.py` checks flow headers, tags, `launchApp`, assertions, the crash check, page object use and inputs, plan format and flow references. It runs on every pull request.
- **Limit:** no script can judge whether an assertion proves the right thing. That stays a review task.

### 4. Shared skill for both platforms

- **Mostly confirmed.** After ignoring the platform name, `pipeline.md` and `heal.md` are identical. `planner.md` and `generator.md` each differ by 3 lines.
- **Why skip:** Android and iOS tickets, plans and prompts are kept separate by requirement, and the duplication is small.
- **Instead:** the check script flags shared wording that differs between platforms.
- **Cost of skipping:** shared edits are still made twice, and lines that name platform tools (such as emulator or simulator) are exempt from the drift check.

### 5. "Follow CLAUDE.md"

- **Confirmed** for both planner and both heal prompts. Four one-line edits.

### 6. Paths named in the docs

| Path | Exists | Finding | Change |
|---|---|---|---|
| `scripts/run-android.sh`, `scripts/run-ios.sh` | Yes | `CLAUDE.md` presents them as the way to run, but they produce no evidence | Report scripts become standard (C) |
| `flows/common` | Yes, empty | `CLAUDE.md` describes it as in use | Marked as reserved (C) |
| `apps.lock` | Yes | Placeholders only; no script reads it | Deleted (C) |
| `sessions/` | No | Named only in the two planner prompts | Sentence removed (D) |
| README repository layout | - | Omits the paths above | Updated (E) |

## Corrections to the review

- `verify-run-outputs` checks six folder types, not five: it also checks `issues`. The skill's description is out of date (fixed in D).
- `CLAUDE.md` never mentions `sessions/`.
- "Nothing checks them mechanically" is not quite right: `ticket_status.py` checks part of the plan rules.

## What the review missed

| Finding | Detail | Handling |
|---|---|---|
| Selectors in test flows | 41 selector steps in 10 of 17 test flows (7 Android, 3 iOS), although `CLAUDE.md` says selectors go in the page object repo only and the README says tests never contain them | Applied: change G moved them into page objects |
| Onboarding timing weakness | `onboarding_complete` checks for "Forward" only four times, so a slow device can be left on onboarding | Applied: change H waits for the first screen and loops until "Forward" is gone |

## Applied: files and risk

| Change | Files | Risk |
|---|---|---|
| A | Both `heal.md`, both report scripts, `build_report.py` | Medium: touches run scripts |
| B | Both `planner.md`, both `heal.md` | Very low |
| C | `CLAUDE.md`, `apps.lock`, `run-android.sh`, `.vscode/tasks.json` | Very low |
| D | Both `planner.md`, `verify-run-outputs/SKILL.md` | Very low |
| E | `README.md` | Low |
| F | `lint_suite.py`, `pr-checks.yml`, `requirements.txt` | Low |
| G | 10 flows, 1 Android test plan, 17 new page objects in the page object repo | Highest: changes what runs |
| H | `onboarding_complete` page object | Medium: every Android test uses it |

## Found while retesting

The first Android reruns on 2026-11-26 (before H) finished 9/12 and 1/12. Further fixes came out of them:

| Finding | Fix |
|---|---|
| Software graphics overloaded the emulator and the Mac | `run-matrix.sh` uses hardware graphics on macOS (`EMU_GPU`) |
| Maestro's Android driver did not start in time | Android report script allows 90 s |
| Erasing 400 characters could exceed Maestro's 120 s device timeout | `search_enter_query` taps the clear button |
| Triage did not recognise a driver start failure | Signal added to `triage_issues.py` and its skill |
| Generator and pipeline prompts did not run the new check | Lint step added to both platforms |

## Applied and verified

Run of 2026-11-27, cycle 01, with the changed flows, page objects and scripts:

| Check | Result |
|---|---|
| `scripts/lint_suite.py` | Pass (17 flows, 16 documents) |
| Android small phone, Android 17 | 12/12, output check pass |
| Android tablet, Android 17 | 12/12, output check pass |
| iPhone 18 Pro, iOS 27.2 | 5/5, output check pass |

**Not verified:** the large phone, the Android 12 baseline, the iPad and the weekly CI job have not been run with these
changes. The `TC=` single-test filter was run once on Android (`TC=TC07`), not on iOS. The pull request check runs on
GitHub for the first time with the pull request.

**Limit:** `docs/RUN-LOCALLY.md` and this file are not covered by the check script.
