# Mobile automation (Maestro) - rules for Claude

## Purpose
Maestro flows for native Android and iOS apps. Maestro runs decide pass/fail; never claim a flow passes unless it was run.

## Layout
- flows/common: cross-platform flows (use appId: ${APP_ID})
- flows/android, flows/ios: platform-specific flows
- flows/subflows: reusable steps (not run directly)
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

## Workflow for changes
1. Inspect the screen (inspect_screen) before writing selectors.
2. Run the flow on a device and fix failures.
3. Show the diff and the run result before suggesting a commit.
