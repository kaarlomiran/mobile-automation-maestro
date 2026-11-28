# Run the tests locally from the terminal

Commands for running the Android and iOS Maestro tests in this repo, with what each one does.
Run every command from the repo root unless noted. Verified against the repo scripts and Maestro 2.12.1.

- Text in `<angle brackets>` is a value you replace.
- Run **one test run at a time** and do not touch the emulator or simulator while it runs.

## 1. The commands you will use most

| Goal | Command |
|---|---|
| Android, full suite on one running emulator | `./scripts/run-android-report.sh` |
| Android, smoke tests only | `./scripts/run-android-report.sh smoke` |
| Android, boot the small phone and run everything | `./scripts/run-matrix.sh phone-small` |
| Android, every enabled device | `./scripts/run-matrix.sh` |
| iOS, full suite on the booted simulator | `./scripts/run-ios-report.sh` |
| One test with full evidence | `TC=TC07 ./scripts/run-android-report.sh` |
| One test, quick check | `maestro test -e APP_ID=org.wikipedia flows/android/<file>.yaml` |
| Check the suite rules (no device) | `.venv/bin/python scripts/lint_suite.py` |

## 2. One-time setup

### Check the tools

| Command | What it does |
|---|---|
| `maestro --version` | Shows the Maestro version (this repo uses 2.12.1) |
| `java -version` | Maestro needs JDK 17 or later |
| `command -v maestro adb emulator ffmpeg python3 gh` | Shows where each tool is; a missing line means it is not on your PATH |
| `xcodebuild -version` | Shows the Xcode version (iOS only) |

If Android tools are not found, add these to `~/.zshrc` (or paste them into the terminal):

```bash
export JAVA_HOME=$(/usr/libexec/java_home)
export ANDROID_HOME=~/Library/Android/sdk ANDROID_SDK_ROOT=~/Library/Android/sdk
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:/opt/homebrew/bin:$HOME/.maestro/bin:$PATH"
```

### Prepare the repo

| Command | What it does |
|---|---|
| `python3 -m venv .venv` | Creates the project's Python environment |
| `.venv/bin/pip install -r scripts/requirements.txt` | Installs the Python packages for reports, video and the suite check |
| `./scripts/sync-pom.sh` | Downloads the page objects into `./pom` |

### App under test (not committed to git)

| Platform | Where it goes |
|---|---|
| Android | `apps/android.apk` (the `wikipedia.apk` inside `https://storage.googleapis.com/mobile.dev/samples/samples.zip`) |
| iOS | `apps/Wikipedia.app`, a simulator build from Xcode (found under `~/Library/Developer/Xcode/DerivedData/Wikipedia-*/Build/Products/Debug-iphonesimulator/`) |

The app ids are in `config/android.env` (`org.wikipedia`) and `config/ios.env` (`org.wikimedia.wikipedia`).

## 3. Page objects (`./pom`)

| Command | What it does |
|---|---|
| `./scripts/sync-pom.sh` | Replaces `./pom` with the page objects from GitHub at the ref in `pom.lock` |
| `POM_LOCAL=../mobile-pom-maestro ./scripts/sync-pom.sh` | Replaces `./pom` with a copy of your local page object repo, including uncommitted changes |
| `git -C pom log --oneline -1` | Shows which page object commit is in `./pom` (works after a GitHub sync, not a local copy) |

- The sync **deletes** `./pom` first. Edit page objects in `../mobile-pom-maestro`, never in `./pom`.
- The run scripts sync only when `./pom` is missing. After changing page objects, sync again yourself.

## 4. Android

### Devices and emulators

| Command | What it does |
|---|---|
| `cat config/devices.csv` | Shows the device list: id, emulator name, Android level, enabled |
| `./scripts/devices/create-avds.sh` | Creates or checks the emulators in `config/devices.csv`; may download system images |
| `emulator -list-avds` | Lists the emulators on this machine |
| `emulator -avd maestro_phone_small -no-snapshot-save -gpu host` | Starts an emulator using the Mac's GPU; the terminal stays busy, so open a second one |
| `adb devices` | Lists running devices and their serials, such as `emulator-5554` |
| `adb shell getprop sys.boot_completed` | Prints `1` when the emulator has finished booting |
| `adb install -r apps/android.apk` | Installs or updates the app on the running device |
| `adb -s <serial> emu kill` | Shuts down that emulator |

| Device id | Emulator name | Class |
|---|---|---|
| `phone-small` | `maestro_phone_small` | Small phone, latest Android |
| `phone-large` | `maestro_phone_large` | Large phone, latest Android |
| `tablet` | `maestro_tablet` | Tablet, latest Android |
| `baseline-phone-api31` | `Pixel_3a_API_31_arm64-v8a_Mobile_View` | Android 12 (API 31) baseline |

### Run the suite on one device (standard run, full evidence)

Start the emulator and install the app first. This script does not do either.

| Command | What it does |
|---|---|
| `./scripts/run-android-report.sh` | Runs every Android test, then builds the report, video, issue folders, triage and output check |
| `./scripts/run-android-report.sh smoke` | Runs only the tests with that tag (see [Tags](#6-tags)) |
| `TC=TC07 ./scripts/run-android-report.sh` | Runs one test case; the report marks it as a partial run |
| `TC="TC02 TC07" ./scripts/run-android-report.sh` | Runs several chosen test cases |
| `NO_VIDEO=1 ./scripts/run-android-report.sh` | Same run without the summary video (the output check then reports the video as missing) |
| `DEVICE_SERIAL=emulator-5554 ./scripts/run-android-report.sh` | Chooses the device when more than one is connected |
| `DEVICE_ID=phone-small DEVICE_CLASS="small phone" ./scripts/run-android-report.sh` | Adds the device name to the run folder name and report |

### Run on the device matrix

This script boots each emulator, waits for it to settle, installs `apps/android.apk`, runs the suite and shuts it down.
It **shuts down any emulator already running** before it starts.

| Command | What it does |
|---|---|
| `./scripts/run-matrix.sh` | Every enabled device, one after another, under one cycle number |
| `./scripts/run-matrix.sh phone-small` | Only that device |
| `./scripts/run-matrix.sh phone-small tablet` | Only those devices |
| `HEADLESS=1 ./scripts/run-matrix.sh` | No emulator windows |
| `NO_VIDEO=1 ./scripts/run-matrix.sh phone-small` | Skips the summary videos |
| `EMU_GPU=auto ./scripts/run-matrix.sh phone-small` | Uses another graphics mode (default on macOS: `host`) |

The matrix always runs the full suite (no tag filter). A device set to `enabled=no` is skipped even if you name it.

### Quick runs (debugging only, no evidence set)

| Command | What it does |
|---|---|
| `./scripts/run-android.sh` | Runs all Android flows with plain Maestro output |
| `./scripts/run-android.sh --include-tags=smoke` | Quick run of one tag |
| `maestro test -e APP_ID=org.wikipedia flows/android/TC07_negative_no_results.yaml` | Runs one test |
| `maestro --udid emulator-5554 test -e APP_ID=org.wikipedia flows/android/<file>.yaml` | Runs one test on a chosen device |
| `maestro test -e APP_ID=org.wikipedia flows/android/<file1>.yaml flows/android/<file2>.yaml` | Runs several chosen tests |

## 5. iOS

### Simulators

| Command | What it does |
|---|---|
| `xcrun simctl list devices available` | Lists simulators with their UDIDs |
| `xcrun simctl list devices booted` | Shows which simulators are running |
| `xcrun simctl boot <udid>` | Starts a simulator |
| `xcrun simctl bootstatus <udid> -b` | Waits until it has finished booting (boots it if needed) |
| `open /Applications/Xcode.app/Contents/Applications/DeviceHub.app` | Opens the window where you can watch the simulator |
| `xcrun simctl install <udid> apps/Wikipedia.app` | Installs the app by hand (the report run does this itself) |
| `xcrun simctl shutdown <udid>` | Shuts down one simulator (`all` shuts down every one) |

### Run the suite (standard run, full evidence)

Boot a simulator first.

| Command | What it does |
|---|---|
| `./scripts/run-ios-report.sh` | Installs `apps/Wikipedia.app`, runs every iOS test on the first booted simulator, then report, video, issues, triage and output check |
| `./scripts/run-ios-report.sh smoke` | Only the tests with that tag |
| `DEVICE_UDID=<udid> ./scripts/run-ios-report.sh` | Chooses the simulator |
| `DEVICE_UDID=<udid> DEVICE_ID=iphone-18-pro DEVICE_CLASS="iPhone" ./scripts/run-ios-report.sh` | Chooses the simulator and names it in the run folder and report |
| `IOS_APP=<path to .app> ./scripts/run-ios-report.sh` | Tests a different app build |
| `TC=TC03 ./scripts/run-ios-report.sh` | Runs one test case; the report marks it as a partial run |
| `NO_VIDEO=1 ./scripts/run-ios-report.sh` | Skips the summary video (the output check reports it as missing) |

For an iPad, boot an iPad simulator and pass its UDID. Known iPad problems are in [KNOWN-ISSUES.md](KNOWN-ISSUES.md).

### Quick runs (debugging only, no evidence set)

| Command | What it does |
|---|---|
| `./scripts/run-ios.sh` | Runs all iOS flows with plain Maestro output |
| `./scripts/run-ios.sh --include-tags=smoke` | Quick run of one tag |
| `maestro --udid <udid> test -e APP_ID=org.wikimedia.wikipedia flows/ios/<file>.yaml` | Runs one test on that simulator |

## 6. Tags

| Tag | Android tests | iOS tests |
|---|---|---|
| `smoke` | TC01, TC02 | TC01, TC02 |
| `regression` | TC03-TC12 | TC03-TC05 |
| `happy` | TC01-TC03 | TC01, TC02 |
| `functional` | TC01, TC04-TC06, TC11, TC12 | TC01, TC04, TC05 |
| `negative` | TC07, TC08 | TC03 |
| `search` | TC02, TC03, TC05-TC11 | TC02, TC03 |
| `boundary` | TC09, TC10 | none |
| `article` | TC12 | TC05 |
| `language` | TC11 | none |
| `saved` | none | TC04 |

Run all of `smoke` and `regression` together to cover every test (the same as running with no tag).

## 7. Check the results

Each standard run gets a name such as `2026-11-26_040129_cycle-02_android_phone-small`, printed as `Run name:`.

**The script's exit code reports the output check, not the test results.** `0` means every output file is present,
`1` means the check found a variance, `2` means no device or app. A run can exit `0` with failed tests, so always read the summary.

```bash
RUN=$(ls runs/report | tail -1)                    # newest run
open runs/report/$RUN/summary.md                   # pass/fail per test
open runs/report/$RUN/output-check.md              # missing or irregular outputs
open runs/issues/$RUN/index.md                     # failed tests, step by step
open runs/issues/$RUN/triage.md                    # machine-related labels (exists when triage ran)
open runs/video/$RUN/${RUN}_summary.mp4            # narrated summary video
open runs/screenshots/$RUN runs/recordings/$RUN    # screenshots and recordings
ls -t runs/matrix | head -3                        # recent matrix runs; each has summary.md
```

| Folder | Contents |
|---|---|
| `runs/report/<RUN>/` | `summary.md`, `results.json`, `run-info.json`, JUnit files, output check, machine load |
| `runs/issues/<RUN>/` | One folder per failed test with the failing step and evidence |
| `runs/screenshots/<RUN>/` | End-of-test screenshot for each test |
| `runs/recordings/<RUN>/` | Screen recording for each test |
| `runs/trace/<RUN>/` | Maestro commands, logs and screen details |
| `runs/video/<RUN>/` | Summary video (60 seconds at most) |

Quick runs write only Maestro's own output, under `~/.maestro/tests/`.

### Rebuild parts of a past run

These rebuild or check files from an existing run. They do not rerun tests or change a pass or fail.

| Command | What it does |
|---|---|
| `python3 -I scripts/verify_run_outputs.py $RUN` | Checks that all outputs are present (needs `ffprobe` on the PATH) |
| `python3 -I scripts/collect_issues.py $RUN` | Rebuilds the failure index and evidence copies; keeps an existing `issue.md` |
| `python3 -I scripts/triage_issues.py $RUN` | Rebuilds the machine-failure labels (run `collect_issues.py` first). It **replaces** the "Machine triage" section of each `issue.md` and anything written below it. Write your notes under "Triage (fill in)", which is kept |
| `.venv/bin/python -I scripts/build_report.py $RUN` | Rebuilds `results.json` and `summary.md` |
| `.venv/bin/python -I scripts/make_summary_video.py $RUN` | Rebuilds the summary video |
| `NARRATION_VOICE=<voice> .venv/bin/python -I scripts/make_summary_video.py $RUN` | Uses another macOS voice (default `Daniel`; `say -v '?'` lists voices) |
| `python3 -I scripts/matrix_report.py runs/matrix/<folder>` | Rebuilds a matrix summary |

## 8. Debug a test

| Command | What it does |
|---|---|
| `maestro list-devices` | Lists the devices Maestro can see |
| `maestro hierarchy` | Prints the current screen's elements, for writing selectors |
| `maestro --udid <id> hierarchy --compact` | Same, shorter, for a chosen device |
| `maestro check-syntax <flow>.yaml` | Checks a flow file without running it |
| `maestro test -c -e APP_ID=<app id> <flow>.yaml` | Reruns the flow each time you save the file |
| `maestro test -e APP_ID=<app id> --debug-output=<folder> <flow>.yaml` | Saves the debug files where you choose |
| `maestro test -e APP_ID=<app id> --format=junit --output=report.xml <flow>.yaml` | Writes a JUnit report |
| `maestro record --local -e APP_ID=<app id> <flow>.yaml <video>.mp4` | Runs a flow and renders a video of it |
| `maestro test smoke/smoke-settings.yaml` | Android only: checks Maestro can drive the device (opens Settings) |
| `adb logcat -d > logcat.txt` | Saves the Android device log |
| `adb exec-out screencap -p > screen.png` | Takes an Android screenshot |
| `xcrun simctl io <udid> screenshot screen.png` | Takes an iOS screenshot |

## 9. Tickets and status

| Command | What it does |
|---|---|
| `python3 scripts/ticket_status.py` | Shows each ticket as NEW, CHANGED, TO_GENERATE or DONE |
| `python3 scripts/ticket_status.py android` | One platform (`ios` for the other) |
| `python3 scripts/ticket_status.py --sha tickets/<platform>/<file>.md` | Prints the value a test plan records as `source-sha` |

## 10. Check the suite without a device

| Command | What it does |
|---|---|
| `.venv/bin/python scripts/lint_suite.py` | Checks flows, page object calls, test plans, paths named in docs and Android/iOS prompt wording (needs `./pom`) |
| `for f in scripts/*.sh scripts/devices/*.sh; do bash -n "$f"; done` | Checks shell script syntax |

The same checks run on every pull request (`.github/workflows/pr-checks.yml`). They read page objects from GitHub
`main`, so merge page object changes first.

## 11. GitHub run from the terminal (optional)

These run on GitHub, not on your machine, and need `gh auth status` to show you are signed in.

| Command | What it does |
|---|---|
| `gh workflow run weekly-android.yml --ref main` | Starts the weekly Android workflow now |
| `gh run list --workflow weekly-android.yml --limit 5` | Lists recent runs and their ids |
| `gh run watch <run id>` | Follows a run until it ends |
| `gh run download <run id> --dir <folder>` | Downloads the run evidence |

## 12. Settings you can pass in

| Variable | Used by | Effect |
|---|---|---|
| `TC` | Report runs | Only these test cases, such as `TC07` or `"TC02 TC07"` |
| `EMU_GPU` | Matrix run | Emulator graphics mode (default on macOS: `host`) |
| `MAESTRO_DRIVER_STARTUP_TIMEOUT` | Android report run | Milliseconds to wait for Maestro's driver (default here: `90000`) |
| `DEVICE_SERIAL` | Android report run | Which Android device |
| `DEVICE_UDID` | iOS report run | Which simulator |
| `DEVICE_ID` | Report runs | Short device name in the run folder name |
| `DEVICE_CLASS` | Report runs | Device description in the report |
| `IOS_APP` | iOS report run | Path to the app build |
| `NO_VIDEO=1` | Report and matrix runs | Skips the summary video |
| `HEADLESS=1` | Matrix run | No emulator windows |
| `CYCLE_NO`, `CYCLE_DATE` | Report runs | Reuses a cycle number or date (the matrix sets these itself) |
| `POM_LOCAL` | `sync-pom.sh` | Copies page objects from a local folder |
| `NARRATION_VOICE` | Summary video | Narration voice |

## 13. When something goes wrong

| Symptom | What to try |
|---|---|
| `No device` | Start an emulator and check `adb devices` |
| `No booted simulator` | `xcrun simctl boot <udid>` |
| `... is not installed` (iOS) | Put the build at `apps/Wikipedia.app` or set `IOS_APP` |
| `command not found` | Set the PATH shown in [section 2](#2-one-time-setup) |
| Page object file not found | `./scripts/sync-pom.sh` |
| Driver start-up or 120 s device timeouts | Check the emulator uses the Mac's GPU (`-gpu host`) and that the Mac is not overloaded |
| "System UI isn't responding", slow first tests | Let the emulator settle a few minutes after boot; close other heavy apps |
| Machine is slow or swapping | `uptime` and `sysctl vm.swapusage` show load and swap; run one device and restart the Mac if swap stays high |
| A run was interrupted | Check `adb devices` and `pgrep -fl 'maestro|screenrecord|recordVideo'` before starting again |
