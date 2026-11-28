# ANDROID - Generator (automation from the plan, Page Object Model)

```text
Act as the Generator for the android Maestro suite. Follow CLAUDE.md.

INPUT: every scenario in specs/android/*.md not marked "**Status:** GENERATED"
(`python3 scripts/ticket_status.py android`), or the ones I name. One at a time.

Page Object Model (mandatory):
- Selectors live ONLY in ../mobile-pom-maestro/android/pages/, one file per page
  action <page>_<action>.yaml, header "appId: ${APP_ID}", inputs documented on top.
- Reuse existing page objects first. ASK before creating a new one.
- Page actions end with an assertion that proves the expected state was reached.
- Flows in flows/android/ only call page objects and pass test data through env.
  Shared setup: flows/subflows/*.yaml.

For EACH scenario:
1. Verify every selector on a booted Android emulator before writing it. Off-screen web view text can be in the accessibility tree (Android 17): visibility alone does not prove scrolling. Tablets show some panels side by side.
2. File flows/android/TC<NN>_<category>_<short_title>.yaml; first line
   "# TC<NN> [category][area] purpose"; tags include smoke or regression.
3. Assert the start state, the expected result and no crash.
4. POM_LOCAL=../mobile-pom-maestro ./scripts/sync-pom.sh
   then run that flow alone: maestro test -e APP_ID=<id from config/android.env> <flow>
5. Fix and re-run until green. Never weaken or delete an assertion, never skip a
   failing test. A suspected app defect: STOP that scenario and report it.
6. Open the end screenshot and confirm it shows what the assertions claim.
7. Set "**Status:** GENERATED, PASSING (verified <date>, <device>)" in the plan,
   or "GENERATED, FAILING on <device> (<issue id>)" if it exposes a defect.

Then run: ./scripts/run-matrix.sh (all devices in config/devices.csv), or ./scripts/run-android-report.sh for one device
Invoke verify-run-outputs, then triage-machine-failures if anything failed.
Run .venv/bin/python scripts/lint_suite.py and fix what it reports.
New defects go into docs/KNOWN-ISSUES.md. Show the diff; commit only when I ask.
Note: the POM repo must be merged before the test repo, which reads it from main.
```
