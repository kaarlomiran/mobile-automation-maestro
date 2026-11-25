# Prompt 2 - Generator (iOS automation from an approved plan, Page Object Model)

Replace the `<placeholders>`, then paste the block into Claude Code from this repo.

```text
Act as the Generator for the iOS Maestro suite. Follow CLAUDE.md.

INPUT: specs/ios/<area>.md - implement the scenarios I name (or all), one at a
time, in order.

Page Object Model (mandatory):
- Selectors (ids, labels, text) live ONLY in the POM repo
  ../mobile-pom-maestro/ios/pages/, one file per page action:
  <page>_<action>.yaml, header "appId: ${APP_ID}", inputs documented at the top.
- Reuse existing page objects first. ASK before creating a new one.
- Page actions end with an assertion that proves they reached the expected state.
- Flows in flows/ios/ only call page objects with runFlow and pass test data
  through env. No raw selectors and no coordinates in flows.
- Shared setup goes in flows/subflows/ios_*.yaml.

For EACH scenario:
1. Verify every selector on the live simulator before writing it
   (maestro hierarchy). Maestro treats ids and text as regular expressions:
   escape or replace parentheses.
2. Name the flow flows/ios/TC<NN>_<category>_<short_title>.yaml. First line is
   "# TC<NN> [category][area] one-sentence purpose". Add tags (smoke or
   regression), start from launchApp with clearState.
3. Assert the start state, the expected result, and that the app did not crash.
   An action without an assertion is not a test.
4. POM_LOCAL=../mobile-pom-maestro ./scripts/sync-pom.sh
   then run that one flow: maestro test -e APP_ID=org.wikimedia.wikipedia <flow>
5. Fix and re-run until green. Never weaken or delete an assertion, never skip
   a failing test. If it looks like an app bug rather than a selector or driver
   problem, STOP that scenario and report it.
6. Open the end-of-test screenshot and confirm it shows what the assertions claim.
7. Report files created, selectors used and the run result. Move on only when
   this scenario is green.

When all scenarios are done:
- ./scripts/run-ios-report.sh
- invoke the verify-run-outputs skill and report every variance
- add "Status: GENERATED, PASSING (verified <date>, <device>)" to each scenario
  in the plan, and a table: scenario id | flow | status | source citation
- show the diff; commit or push only when I ask
```

## Prompt 3 - Heal (diagnose a failing iOS run)

```text
Diagnose the failed tests in run <RUN_NAME>. Read, in order:
runs/report/<RUN>/summary.md, the failure screenshot in runs/screenshots/<RUN>/,
runs/trace/<RUN>/<test>/ (maestro.log, screen-hierarchy/, app.log) and the
recording if timing matters. State the root cause with evidence before changing
anything. Fix in the page object when it is a selector or timing problem. Re-run,
confirm the screenshot, and say which run is authoritative.
```
