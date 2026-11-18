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
export CYCLE_DATE="$DATE"; export CYCLE_NO=$(printf '%02d' $(( 10#${LAST:-0} + 1 )))      # one cycle for every device of this matrix run
MDIR="runs/matrix/${DATE}_$(date +%H%M%S)_cycle-$CYCLE_NO"; mkdir -p "$MDIR"
: > "$MDIR/runs.tsv"
WIN=""; [[ -n "${HEADLESS:-}" ]] && WIN="-no-window -no-audio"
while IFS=, read -r id avd profile api class enabled notes <&3; do
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
  # settle: a just-booted emulator can raise "System UI isn't responding" over the app (seen on large/tablet AVDs)
  adb -s "$SER" shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  for k in window_animation_scale transition_animation_scale animator_duration_scale; do adb -s "$SER" shell settings put global $k 0 >/dev/null 2>&1; done
  sleep 60
  for i in 1 2 3 4 5 6; do
    adb -s "$SER" shell uiautomator dump /sdcard/anr.xml >/dev/null 2>&1
    if adb -s "$SER" shell cat /sdcard/anr.xml 2>/dev/null | grep -q "isn't responding"; then
      echo "ANR dialog present after boot on $id, choosing Wait"
      XY=$(adb -s "$SER" shell cat /sdcard/anr.xml | tr '>' '>\n' | grep 'text="Wait"' | grep -o 'bounds="\[[0-9]*,[0-9]*\]\[[0-9]*,[0-9]*\]"' | head -1 | tr -c '0-9\n' ' ' | awk '{print int(($1+$3)/2), int(($2+$4)/2)}')
      [[ -n "$XY" ]] && adb -s "$SER" shell input tap $XY; sleep 10
    else break; fi
  done
  [[ -f apps/android.apk ]] && adb -s "$SER" install -r apps/android.apk >/dev/null 2>&1   # app under test onto the fresh AVD
  OUT=$(DEVICE_SERIAL="$SER" DEVICE_ID="$id" DEVICE_CLASS="$class" ./scripts/run-android-report.sh 2>&1 | tee /dev/stderr)
  RUNDIR=$(echo "$OUT" | sed -n 's/^Run name: //p' | head -1)
  printf '%s\t%s\t%s\n' "$id" "$RUNDIR" "$class" >> "$MDIR/runs.tsv"
  adb -s "$SER" emu kill >/dev/null 2>&1; sleep 5
done 3< <(grep -v '^#' config/devices.csv)   # fd 3: adb/maestro must not swallow the device list from stdin
python3 -I scripts/matrix_report.py "$MDIR"
