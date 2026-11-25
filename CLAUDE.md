# Mobile automation (Maestro) - rules for Claude

## Purpose
Maestro flows for native Android and iOS apps. Maestro runs decide pass/fail; never claim a flow passes unless it was run.

## Layout
- flows/common: cross-platform flows (use appId: ${APP_ID})
- flows/android, flows/ios: platform-specific flows
- flows/subflows: reusable steps (not run directly)
- tickets/{android,ios}, specs/{android,ios}, docs/prompts/{android,ios}
- config/*.env: per-platform APP_ID; apps.lock pins app versions
- Never commit app binaries or secrets.

## Run
- Android: ./scripts/run-android.sh
- iOS: ./scripts/run-ios.sh
- Prefer the Maestro MCP tools: list_devices, inspect_screen, run, take_screenshot.

## Flow style
- Prefer accessibility ids and visible text; no coordinates.
- Every flow has tags (smoke or regression) and starts with launchApp (clearState where safe).
- Extract repeated steps into flows/subflows and call them with runFlow.
- Test data via -e variables; no credentials in YAML.

## Run outputs (mandatory)
- Runs: ./scripts/run-android-report.sh (one device) or ./scripts/run-matrix.sh (all devices in config/devices.csv); iOS: run-ios-report.sh.
- Outputs: one folder per run inside each of runs/{screenshots,recordings,trace,report,video,issues}/, named <YYYY-MM-DD_HHMMSS>_cycle-<NN>_<platform>[_<device>] (cycle restarts each date).
- Failures: runs/issues/<RUN>/NN_TCxx_short-title_step-SSS_<flow-part>/ (scripts/collect_issues.py), both platforms.
- After a run with ANY failure also invoke triage-machine-failures: label and evidence only; results are never changed.
- After EVERY run on EITHER platform and every device, invoke the verify-run-outputs skill (.claude/skills/verify-run-outputs) and report its variances. Never skip.
- Devices: config/devices.csv (small phone, large phone, tablet on latest Android + API 31 baseline). See docs/DEVICE-MATRIX.md.
- POM: page objects live in the separate repo mobile-pom-maestro, fetched into ./pom by scripts/sync-pom.sh (pinned in pom.lock). Selectors go there only.
- Every test needs assertions on start state, expected result and no-crash; a bare action without an assertion is not a test.

## Tickets -> plan -> automation (Android and iOS kept apart)
- Input: tickets/<platform>/*.md. State: python3 scripts/ticket_status.py. Plans: specs/<platform>/ (same file name,
  with source-sha). Prompts: docs/prompts/<platform>/. Never invent scenarios beyond the ticket.

## Workflow for changes
1. Inspect the screen (inspect_screen) before writing selectors.
2. Run the flow on a device and fix failures.
3. Show the diff and the run result before suggesting a commit.
