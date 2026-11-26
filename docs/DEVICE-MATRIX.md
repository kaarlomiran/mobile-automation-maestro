# Device matrix

Targets live in one file: `config/devices.csv`. Add a row to add a device, set `enabled=no` to pause one, change `api` to move OS.

| id | class | OS |
|---|---|---|
| phone-small | small phone 5.0in | latest Android |
| phone-large | large phone 6.8in | latest Android |
| tablet | tablet 10.2in | latest Android |
| baseline-phone-api31 | existing phone | Android 12 (API 31) |

## Commands
```bash
./scripts/devices/create-avds.sh          # create/verify AVDs (needs sdkmanager/avdmanager)
./scripts/run-matrix.sh                   # all enabled devices, sequentially
./scripts/run-matrix.sh tablet phone-small   # only some
HEADLESS=1 ./scripts/run-matrix.sh        # no emulator windows
EMU_GPU=auto ./scripts/run-matrix.sh      # emulator graphics mode; the default on macOS is host (the Mac's GPU)
```
Hardware graphics matter: with software drawing (the AVD default) a local run overloaded the machine and tests timed
out. If you start an emulator yourself, add `-gpu host`.

Each device gets its own run folder in every output category; all devices of one matrix run share one cycle number (naming in the verify-run-outputs skill). The matrix summary
(`runs/matrix/<date>_<time>_cycle-NN/summary.md`) shows pass/fail per test per device. Update the
"latest" OS by re-running `create-avds.sh` after `sdkmanager --update`; it picks the highest API available.
