# ANDROID - Heal (diagnose failures of a run)

```text
Follow CLAUDE.md.
Diagnose the failures of android run <RUN_NAME> (default: the newest android run).
Read in order: runs/issues/<RUN>/triage.md and index.md, each issue folder
(failure screenshot, screen hierarchy, log, recording), then runs/trace/<RUN>/.
State the root cause with evidence BEFORE changing anything, and say whether it is
an app defect, test defect, environment/machine, or data. For machine-suspect
failures follow the triage-machine-failures skill (rerun; never delete or relabel
the original result). Fix selector or timing problems in the page object.
Plain `maestro test` runs are fine while debugging, but they leave no run folder.
The rerun you report must be a report run on the same device: TC=TC<NN> ./scripts/run-android-report.sh
Invoke verify-run-outputs on it, then triage-machine-failures if anything failed.
Confirm with the screenshot, and name the authoritative run.
```
