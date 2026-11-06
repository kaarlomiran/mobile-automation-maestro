#!/usr/bin/env bash
# Run the whole suite on every enabled device in config/devices.csv, one after another.
# Usage: ./scripts/run-matrix.sh [device-id ...]      HEADLESS=1 for no emulator windows; NO_VIDEO=1 to skip videos
# Output: one run folder per device in each category folder (see verify-run-outputs skill), all sharing ONE cycle number,
#         plus runs/matrix/<date>_<time>_cycle-NN/summary.md
set -uo pipefail
cd "$(dirname "$0")/.."
ONLY=("$@")
mkdir -p runs/matrix runs/report; DATE=$(date +%Y-%m-%d)
LAST=$( { ls runs/report 2>/dev/null | grep "^${DATE}_" | sed -n 's/.*_cycle-\([0-9]*\)_.*/\1/p'; ls runs/matrix 2>/dev/null | grep "^${DATE}_" | sed -n 's/.*_cycle-\([0-9]*\)$/\1/p'; } | sort -n | tail -1)
export CYCLE_NO=$(printf '%02d' $(( 10#${LAST:-0} + 1 )))      # one cycle for every device of this matrix run
MDIR="runs/matrix/${DATE}_$(date +%H%M%S)_cycle-$CYCLE_NO"; mkdir -p "$MDIR"
: > "$MDIR/runs.tsv"
WIN=""; [[ -n "${HEADLESS:-}" ]] && WIN="-no-window -no-audio"
grep -v '^#' config/devices.csv | while IFS=, read -r id avd profile api class enabled notes; do
  [[ "$enabled" == "yes" ]] || continue
  if [[ ${#ONLY[@]} -gt 0 ]] && ! printf '%s\n' "${ONLY[@]}" | grep -qx "$id"; then continue; fi
  echo "##### $id ($avd)"
  adb devices | awk '/^emulator/{print $1}' | while read s; do adb -s "$s" emu kill >/dev/null 2>&1; done; sleep 5
  nohup emulator -avd "$avd" -no-snapshot-save $WIN > "$MDIR/emulator-$id.log" 2>&1 &
  for i in $(seq 1 60); do
    SER=$(adb devices | awk '/^emulator.*device$/{print $1; exit}')
    [[ -n "$SER" && "$(adb -s "$SER" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]] && break; sleep 5
  done
  if [[ -z "${SER:-}" ]]; then echo "BOOT FAILED $id"; printf '%s\tBOOT_FAILED\t\n' "$id" >> "$MDIR/runs.tsv"; continue; fi
  [[ -f apps/android.apk ]] && adb -s "$SER" install -r apps/android.apk >/dev/null 2>&1   # app under test onto the fresh AVD
  OUT=$(DEVICE_SERIAL="$SER" DEVICE_ID="$id" DEVICE_CLASS="$class" ./scripts/run-android-report.sh 2>&1 | tee /dev/stderr)
  RUNDIR=$(echo "$OUT" | sed -n 's/^Run name: //p' | head -1)
  printf '%s\t%s\t%s\n' "$id" "$RUNDIR" "$class" >> "$MDIR/runs.tsv"
  adb -s "$SER" emu kill >/dev/null 2>&1; sleep 5
done
python3 -I scripts/matrix_report.py "$MDIR"
