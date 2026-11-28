# IOS - Generator (automation from the plan, Page Object Model)

```text
Act as the Generator for the ios Maestro suite. Follow CLAUDE.md.

INPUT: every scenario in specs/ios/*.md not marked "**Status:** GENERATED"
(`python3 scripts/ticket_status.py ios`), or the ones I name. One at a time.

Page Object Model (mandatory):
- Selectors live ONLY in ../mobile-pom-maestro/ios/pages/, one file per page
  action <page>_<action>.yaml, header "appId: ${APP_ID}", inputs documented on top.
- Reuse existing page objects first. ASK before creating a new one.
- Page actions end with an assertion that proves the expected state was reached.
- Flows in flows/ios/ only call page objects and pass test data through env.
  Shared setup: flows/subflows/ios_*.yaml.

For EACH scenario:
1. Verify every selector on a booted iOS simulator before writing it. Maestro treats ids and text as regular expressions: escape or replace parentheses. iPhone and iPad layouts differ (the Contents panel is a sidebar on iPad).
2. File flows/ios/TC<NN>_<category>_<short_title>.yaml; first line
   "# TC<NN> [category][area] purpose"; tags include smoke or regression.
3. Assert the start state, the expected result and no crash.
4. POM_LOCAL=../mobile-pom-maestro ./scripts/sync-pom.sh
   then run that flow alone: maestro test -e APP_ID=<id from config/ios.env> <flow>
5. Fix and re-run until green. Never weaken or delete an assertion, never skip a
   failing test. A suspected app defect: STOP that scenario and report it.
6. Open the end screenshot and confirm it shows what the assertions claim.
7. Set "**Status:** GENERATED, PASSING (verified <date>, <device>)" in the plan,
   or "GENERATED, FAILING on <device> (<issue id>)" if it exposes a defect.

Then run: ./scripts/run-ios-report.sh (one booted simulator; repeat per device with DEVICE_UDID and DEVICE_ID)
Invoke verify-run-outputs, then triage-machine-failures if anything failed.
Run .venv/bin/python scripts/lint_suite.py and fix what it reports.
New defects go into docs/KNOWN-ISSUES.md. Show the diff; commit only when I ask.
Note: the POM repo must be merged before the test repo, which reads it from main.
```
