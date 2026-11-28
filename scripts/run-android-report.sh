#!/usr/bin/env bash
# Run every Android flow one by one and archive outputs, one folder PER RUN inside each category:
#   runs/screenshots/<RUN>/NN_TCxx_short-title_PASS|FAIL.png     end-of-test screen
#   runs/recordings/<RUN>/NN_TCxx_short-title.mp4                screen recording per test
#   runs/trace/<RUN>/NN_TCxx_short-title/                        Maestro commands, logs, hierarchy, failure shots
#   runs/report/<RUN>/                                           junit/, results.json, summary.md, run-info.json, output-check.*
#   runs/video/<RUN>/<RUN>_summary.mp4                           <=60 s narrated summary
#   runs/issues/<RUN>/NN_TCxx_.._step-SSS_<flow-part>/         one folder per failed test (evidence + issue.md)
# <RUN> = YYYY-MM-DD_HHMMSS_cycle-NN_<platform>[_<device-id>]   (cycle-NN restarts at 01 every date)
# Usage: ./scripts/run-android-report.sh [tag-filter e.g. smoke]
#        TC=TC07 ./scripts/run-android-report.sh      only these test cases (space separated: TC="TC02 TC07")
# Env:   DEVICE_SERIAL, DEVICE_ID, DEVICE_CLASS, CYCLE_NO, CYCLE_DATE (all set by run-matrix.sh), NO_VIDEO=1
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [[ -x .venv/bin/python ]] && PY=.venv/bin/python   # project venv (pillow) if present: scripts/requirements.txt
[[ -d pom ]] || ./scripts/sync-pom.sh
APP_ID=$(grep '^APP_ID=' config/android.env | cut -d= -f2)
TAG="${1:-}"
# a slow emulator can need longer than Maestro's default to start its driver; without this the test never runs
export MAESTRO_DRIVER_STARTUP_TIMEOUT="${MAESTRO_DRIVER_STARTUP_TIMEOUT:-90000}"   # milliseconds
# select the flows first, so a filter that matches nothing creates no empty run folder
FLOWS=()
for f in flows/android/TC*.yaml; do
  if [[ -n "$TAG" ]] && ! grep -q -E "^tags:.*\b$TAG\b" "$f"; then continue; fi
  tc=$(basename "$f" .yaml); tc=${tc%%_*}
  if [[ -n "${TC:-}" && " $TC " != *" $tc "* ]]; then continue; fi
  FLOWS+=("$f")
done
[[ ${#FLOWS[@]} -gt 0 ]] || { echo "No android test matches tag='$TAG' TC='${TC:-}'"; exit 2; }
SELECTION="${TAG:+tag $TAG }${TC:+test cases $TC}"

RUNS=runs; DATE="${CYCLE_DATE:-$(date +%Y-%m-%d)}"      # a matrix cycle keeps the date it started on (even past midnight)
mkdir -p $RUNS/{screenshots,recordings,trace,report,video,issues}
if [[ -z "${CYCLE_NO:-}" ]]; then
  LAST=$(ls $RUNS/report 2>/dev/null | grep "^${DATE}_" | sed -n 's/.*_cycle-\([0-9]*\)_.*/\1/p' | sort -n | tail -1)
  CYCLE_NO=$(printf '%02d' $(( 10#${LAST:-0} + 1 )))
fi
DEV_SEG=""; [[ -n "${DEVICE_ID:-}" ]] && DEV_SEG="_${DEVICE_ID}"
RUN_NAME="${DATE}_$(date +%H%M%S)_cycle-${CYCLE_NO}_android${DEV_SEG}"
SHOTS=$RUNS/screenshots/$RUN_NAME; RECS=$RUNS/recordings/$RUN_NAME; TRACE=$RUNS/trace/$RUN_NAME
REP=$RUNS/report/$RUN_NAME; VID=$RUNS/video/$RUN_NAME
mkdir -p "$SHOTS" "$RECS" "$TRACE" "$REP/junit" "$VID"
echo "Run name: $RUN_NAME"

DEVICE="${DEVICE_SERIAL:-}"
[[ -z "$DEVICE" ]] && DEVICE=$(adb devices | awk '$2=="device"{print $1; exit}')
[[ -z "$DEVICE" ]] && { echo "No device"; exit 2; }
APP_VER=$(adb -s "$DEVICE" shell dumpsys package "$APP_ID" | awk -F= '/versionName/{print $2; exit}' | tr -d '\r')
OS_REL=$(adb -s "$DEVICE" shell getprop ro.build.version.release | tr -d '\r'); API=$(adb -s "$DEVICE" shell getprop ro.build.version.sdk | tr -d '\r')
SCREEN=$(adb -s "$DEVICE" shell wm size | awk -F": " '{print $2}' | tr -d '\r'); AVD=$(adb -s "$DEVICE" emu avd name 2>/dev/null | head -1 | tr -d '\r')
printf '{"platform":"android","cycle":"%s","device_id":"%s","device_class":"%s","avd":"%s","android":"%s","api":"%s","screen":"%s","run_id":"%s","device":"%s","app_id":"%s","app_version":"%s","started":"%s","selection":"%s"}\n' \
  "$CYCLE_NO" "${DEVICE_ID:-default}" "${DEVICE_CLASS:-}" "$AVD" "$OS_REL" "$API" "$SCREEN" "$RUN_NAME" "$DEVICE" "$APP_ID" "$APP_VER" "$(date -Iseconds)" "$SELECTION" > "$REP/run-info.json"

# environment hygiene (logged to report/<RUN>/environment.log): clear system "not responding" dialogs before testing
./scripts/devices/settle-emulator.sh "$DEVICE" "$APP_ID" 4 | sed "s/^/suite-start\t/" | tee -a "$REP/environment.log"

N=0
for f in "${FLOWS[@]}"; do
  N=$((N+1)); NN=$(printf '%02d' $N)
  base=$(basename "$f" .yaml); tc=${base%%_*}; short=$(echo "${base#*_}" | tr '_' '-')
  name="${NN}_${tc}_${short}"
  echo "== $name"

  ./scripts/devices/settle-emulator.sh "$DEVICE" "$APP_ID" | sed "s/^/$name\t/" | tee -a "$REP/environment.log"
  "$PY" -I scripts/host_metrics.py "$REP/host-metrics.tsv" "$name:before"
  adb -s "$DEVICE" shell rm -f /sdcard/rec.mp4
  adb -s "$DEVICE" shell screenrecord --time-limit 170 /sdcard/rec.mp4 >/dev/null 2>&1 &
  REC=$!; sleep 1; START=$(date +%s)
  maestro test --udid "$DEVICE" -e APP_ID="$APP_ID" --format=junit --output="$REP/junit/$name.xml" \
    --debug-output="$TRACE/$name" --flatten-debug-output "$f" > "$TRACE/$name.log" 2>&1
  RC=$?; DUR=$(( $(date +%s) - START ))
  "$PY" -I scripts/host_metrics.py "$REP/host-metrics.tsv" "$name:after"
  RESULT=PASS; [[ $RC -ne 0 ]] && RESULT=FAIL

  adb -s "$DEVICE" exec-out screencap -p > "$SHOTS/${name}_${RESULT}.png"
  adb -s "$DEVICE" shell pkill -2 screenrecord >/dev/null 2>&1; sleep 2; wait $REC 2>/dev/null
  adb -s "$DEVICE" pull /sdcard/rec.mp4 "$RECS/$name.mp4" >/dev/null 2>&1

  REASON=""
  [[ $RESULT == FAIL ]] && REASON=$(grep -m1 -E "FAILED|Assertion|Element not found" "$TRACE/$name.log" | tr -d '"\\' | cut -c1-200)
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$NN" "$tc" "$short" "$RESULT" "$DUR" "$(grep -m1 '^tags:' "$f" | sed 's/tags: *//')" "$REASON" >> "$REP/.rows.tsv"
  sed -n '1s/^# //p' "$f" >> "$REP/.titles.txt"
done

"$PY" -I scripts/build_report.py "$RUN_NAME"
[[ -z "${NO_VIDEO:-}" ]] && "$PY" -I scripts/make_summary_video.py "$RUN_NAME"
"$PY" -I scripts/collect_issues.py "$RUN_NAME"     # one folder per failed test, with the failing step
"$PY" -I scripts/triage_issues.py "$RUN_NAME"      # label machine-suspect failures (results are never changed)
# MANDATORY output guard (skill: verify-run-outputs). Never skip.
"$PY" -I scripts/verify_run_outputs.py "$RUN_NAME"
GUARD=$?
echo "Done: $RUN_NAME  (output check exit=$GUARD; see $REP/output-check.md)"
exit $GUARD
