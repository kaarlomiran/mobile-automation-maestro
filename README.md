# Mobile automation with Maestro (Android now, iOS to follow)

End-to-end UI automation of a native mobile app using [Maestro](https://maestro.dev) YAML flows.
Target app for the current version: **Wikipedia for Android** (`org.wikipedia`).
Maestro decides pass/fail; Claude is used as a facilitator to author, debug and review flows.

## What the suite covers

12 automated test cases, each with strong assertions (start state, expected result, absence of wrong/stale state, no crash dialog):

| ID | Category | What it checks |
|---|---|---|
| TC01 | Happy path, smoke | Fresh install: onboarding completes and the Explore feed is shown |
| TC02 | Happy path, search, smoke | Searching "Albert Einstein" lists the article with its description |
| TC03 | Happy path, search | Tapping a result opens the article page |
| TC04 | Functional | Every bottom-navigation tab opens its screen (incl. the first-visit "Introducing Activity" intro) |
| TC05 | Functional, search | The X button clears the query and removes the results |
| TC06 | Functional, search | Search is case-insensitive (lower and upper case give the same result) |
| TC07 | Negative, search | A nonsense query shows "No results" and no stale results |
| TC08 | Negative, search | Markup / SQL-injection-like input is handled safely (no crash, echoed as plain text) |
| TC09 | Boundary, search | Single-character query is accepted and returns suggestions |
| TC10 | Boundary, search | Query limit is 300 characters: exactly 300 is accepted, 301 is rejected with a clear error |
| TC11 | Functional, language | Adding Spanish and switching the search language tab returns Spanish results; switching back restores English |
| TC12 | Functional, article | Scrolling a long article reaches the end of the page (footer license text and browser link) |

iOS test cases will follow the same structure and naming (see [Roadmap](#roadmap)).

## Page Object Model (POM)

Selectors live only in the separate repo **[mobile-pom-maestro](https://github.com/kaarlomiran/mobile-pom-maestro)**
(screen-scoped subflows such as `search_enter_query`, `article_assert_loaded`, `language_add`, `app_assert_no_crash`).
Tests call page actions and never contain raw selectors. The POM is pinned in `pom.lock` and fetched into `./pom` by
`scripts/sync-pom.sh`. Local development against a working copy: `POM_LOCAL=../mobile-pom-maestro ./scripts/sync-pom.sh`.

## Reporting, traces and evidence

Every run produces a complete, separated evidence set. There is one folder **per run inside each category**,
named `YYYY-MM-DD_HHMMSS_cycle-NN_<platform>[_<device>]` (the cycle number restarts at 01 each date, so cycles never mix):

```
runs/screenshots/<RUN>/   NN_TCxx_short-title_PASS|FAIL.png     end-of-test screenshot for every test
runs/recordings/<RUN>/    NN_TCxx_short-title.mp4               screen recording for every test
runs/trace/<RUN>/         NN_TCxx_short-title/                  every executed step: commands, logs, UI hierarchy, step screenshots, logcat
runs/report/<RUN>/        junit/, results.json, summary.md, run-info.json, output-check.md
runs/video/<RUN>/         <RUN>_summary.mp4                     consolidated narrated summary video (max 60 s)
runs/matrix/<date>_<time>_cycle-NN/summary.md                   device x test table for a matrix run
```

- **Traces** let you validate the run and each step the suite executed (what was tapped/asserted, what the screen looked like, device logs).
- **Reports**: JUnit XML per test, a machine-readable `results.json` and a human-readable `summary.md` (device, Android version, screen size, app version, timings).
- **Consolidated summary video**: a narrated (male voice) video of at most 60 seconds covering scope, what was run, risks, issues found and the summary. It is built from the run results, so it can go straight into a test summary report.
- **Output guard**: the `verify-run-outputs` skill (`.claude/skills/verify-run-outputs`) runs after every run and checks that every
  screenshot, recording, trace and report exists for every test case, that names and sequence numbers follow the convention,
  and that the video is within 60 s. It writes `output-check.md` and flags every variance for human review.

## Device and OS matrix

Targets are defined in one file, `config/devices.csv`; add a row to add a device, set `enabled=no` to pause one.

| Device id | Class | Android |
|---|---|---|
| `phone-small` | Small phone (Pixel 2, 5.0") | Latest (Android 17, API 37) |
| `phone-large` | Large phone (Pixel 9 Pro XL) | Latest (Android 17, API 37) |
| `tablet` | Tablet (Pixel Tablet, 10.2") | Latest (Android 17, API 37) |
| `baseline-phone-api31` | Phone | Android 12 (API 31), older-OS baseline |

`./scripts/run-matrix.sh` runs the whole suite on every enabled device (one shared cycle number), then writes a consolidated
test-by-device table. See [docs/DEVICE-MATRIX.md](docs/DEVICE-MATRIX.md).

## Quick start

Prerequisites: JDK 17+, Maestro 2.x, Android SDK (command-line tools, emulator, platform-tools), `ffmpeg` (summary video), `gh`.

```bash
./scripts/sync-pom.sh                     # fetch the page objects
./scripts/devices/create-avds.sh          # create the emulators from config/devices.csv
./scripts/run-android-report.sh           # one device, full evidence set + summary video + output check
./scripts/run-android-report.sh smoke     # only tests tagged smoke
HEADLESS=1 ./scripts/run-matrix.sh        # every device in the matrix
./scripts/run-matrix.sh tablet            # only some devices
```

The app under test is installed from `apps/android.apk` (not committed; use the Wikipedia APK that `maestro download-samples` provides).
`config/android.env` holds the package name.

## Repository layout

```
flows/android/      TC01..TC12 test flows (tagged smoke / regression / happy / negative / boundary / search / functional)
flows/subflows/     shared test setup (fresh start -> search focused)
flows/ios/          placeholder for iOS flows
config/             android.env (app id), devices.csv (device matrix)
scripts/            run-android-report.sh, run-matrix.sh, sync-pom.sh, build_report.py, make_summary_video.py,
                    verify_run_outputs.py, matrix_report.py, devices/create-avds.sh
.claude/skills/     verify-run-outputs (mandatory output guard)
docs/               DEVICE-MATRIX.md
CLAUDE.md           rules for Claude (flow style, mandatory output check, POM rule, assertion rule)
```

Not committed (see `.gitignore`): `runs/` (evidence output), `pom/` (fetched), `apps/` binaries, `*.apk`.

## Conventions

- Prefer accessibility ids and visible text; no coordinates. Selectors only in the POM repo.
- Every test asserts start state, expected result, absence of wrong state and no crash; a bare action is not a test.
- Every flow carries tags and starts from a clean app state.
- No credentials in flows; use `-e` variables.

## Roadmap

- **iOS** (next): simulator setup, `flows/ios`, iOS page objects in `mobile-pom-maestro/ios`, `scripts/run-ios-report.sh`
  with the same run-folder convention and the same output guard.
- CI on GitHub Actions (Android job, then iOS on a macOS runner) with branch protection, and Claude PR review.
