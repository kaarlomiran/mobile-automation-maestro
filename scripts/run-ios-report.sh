#!/usr/bin/env bash
# Run every iOS flow one by one on a booted simulator and archive outputs, one folder PER RUN inside each category
# (same convention and the same mandatory output guard as run-android-report.sh):
#   runs/{screenshots,recordings,trace,report,video,issues}/<YYYY-MM-DD_HHMMSS_cycle-NN_ios[_<device-id>]>/
# Usage: ./scripts/run-ios-report.sh [tag-filter e.g. smoke]
#        TC=TC03 ./scripts/run-ios-report.sh      only these test cases (space separated: TC="TC02 TC05")
# Env:   DEVICE_UDID (default: first booted simulator), DEVICE_ID, DEVICE_CLASS, IOS_APP (.app to install,
#        default apps/Wikipedia.app), CYCLE_NO, CYCLE_DATE, NO_VIDEO=1
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [[ -x .venv/bin/python ]] && PY=.venv/bin/python
[[ -d pom/ios/pages ]] || ./scripts/sync-pom.sh
APP_ID=$(grep '^APP_ID=' config/ios.env | cut -d= -f2)
TAG="${1:-}"
# select the flows first, so a filter that matches nothing creates no empty run folder
FLOWS=()
for f in flows/ios/TC*.yaml; do
  if [[ -n "$TAG" ]] && ! grep -q -E "^tags:.*[[ ,]$TAG[],]" "$f"; then continue; fi
  tc=$(basename "$f" .yaml); tc=${tc%%_*}
  if [[ -n "${TC:-}" && " $TC " != *" $tc "* ]]; then continue; fi
  FLOWS+=("$f")
done
[[ ${#FLOWS[@]} -gt 0 ]] || { echo "No ios test matches tag='$TAG' TC='${TC:-}'"; exit 2; }
SELECTION="${TAG:+tag $TAG }${TC:+test cases $TC}"

DEVICE="${DEVICE_UDID:-}"
[[ -z "$DEVICE" ]] && DEVICE=$(xcrun simctl list devices booted | grep -m1 -oE '[0-9A-F]{8}-([0-9A-F]{4}-){3}[0-9A-F]{12}')
[[ -z "$DEVICE" ]] && { echo "No booted simulator (xcrun simctl boot <udid>)"; exit 2; }
APP="${IOS_APP:-apps/Wikipedia.app}"
[[ -d "$APP" ]] && xcrun simctl install "$DEVICE" "$APP"
CONTAINER=$(xcrun simctl get_app_container "$DEVICE" "$APP_ID" app 2>/dev/null) || { echo "$APP_ID is not installed; set IOS_APP=/path/to/Wikipedia.app"; exit 2; }
APP_VER=$(plutil -extract CFBundleShortVersionString raw "$CONTAINER/Info.plist")
# device name + runtime of this simulator
IFS=$'\t' read -r DEV_NAME OS_REL < <(xcrun simctl list devices -j | python3 -c '
import json,sys
for rt, ds in json.load(sys.stdin)["devices"].items():
    for d in ds:
        if d["udid"] == sys.argv[1]: print(d["name"] + "\t" + rt.split("iOS-")[-1].replace("-", "."))' "$DEVICE")
: "${DEVICE_ID:=$(echo "$DEV_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')}"

RUNS=runs; DATE="${CYCLE_DATE:-$(date +%Y-%m-%d)}"
mkdir -p $RUNS/{screenshots,recordings,trace,report,video,issues}
if [[ -z "${CYCLE_NO:-}" ]]; then
  LAST=$(ls $RUNS/report 2>/dev/null | grep "^${DATE}_" | sed -n 's/.*_cycle-\([0-9]*\)_.*/\1/p' | sort -n | tail -1)
  CYCLE_NO=$(printf '%02d' $(( 10#${LAST:-0} + 1 )))
fi
RUN_NAME="${DATE}_$(date +%H%M%S)_cycle-${CYCLE_NO}_ios_${DEVICE_ID}"
SHOTS=$RUNS/screenshots/$RUN_NAME; RECS=$RUNS/recordings/$RUN_NAME; TRACE=$RUNS/trace/$RUN_NAME
REP=$RUNS/report/$RUN_NAME; VID=$RUNS/video/$RUN_NAME
mkdir -p "$SHOTS" "$RECS" "$TRACE" "$REP/junit" "$VID"
echo "Run name: $RUN_NAME"

xcrun simctl io "$DEVICE" screenshot "$REP/.probe.png" >/dev/null 2>&1
SCREEN=$(sips -g pixelWidth -g pixelHeight "$REP/.probe.png" | awk '/pixel/{print $2}' | paste -sd x -); rm -f "$REP/.probe.png"
printf '{"platform":"ios","cycle":"%s","device_id":"%s","device_class":"%s","simulator":"%s","ios":"%s","screen":"%s","run_id":"%s","device":"%s","app_id":"%s","app_version":"%s","started":"%s","selection":"%s"}\n' \
  "$CYCLE_NO" "$DEVICE_ID" "${DEVICE_CLASS:-}" "$DEV_NAME" "$OS_REL" "$SCREEN" "$RUN_NAME" "$DEVICE" "$APP_ID" "$APP_VER" "$(date +%Y-%m-%dT%H:%M:%S%z)" "$SELECTION" > "$REP/run-info.json"

N=0
for f in "${FLOWS[@]}"; do
  N=$((N+1)); NN=$(printf '%02d' $N)
  base=$(basename "$f" .yaml); tc=${base%%_*}; short=$(echo "${base#*_}" | tr '_' '-')
  name="${NN}_${tc}_${short}"
  echo "== $name"
  mkdir -p "$TRACE/$name"

  xcrun simctl io "$DEVICE" recordVideo --codec=h264 --force "$RECS/$name.mp4" >/dev/null 2>&1 &
  REC=$!
  xcrun simctl spawn "$DEVICE" log stream --style compact --predicate 'process == "Wikipedia"' > "$TRACE/$name/app.log" 2>/dev/null &
  LOG=$!
  "$PY" -I scripts/host_metrics.py "$REP/host-metrics.tsv" "$name:before"
  sleep 1; START=$(date +%s); touch "$TRACE/$name/.start"
  maestro --udid "$DEVICE" test -e APP_ID="$APP_ID" --format=junit --output="$REP/junit/$name.xml" \
    --debug-output="$TRACE/$name" --flatten-debug-output "$f" > "$TRACE/$name.log" 2>&1
  RC=$?; DUR=$(( $(date +%s) - START ))
  "$PY" -I scripts/host_metrics.py "$REP/host-metrics.tsv" "$name:after"
  RESULT=PASS; [[ $RC -ne 0 ]] && RESULT=FAIL

  xcrun simctl io "$DEVICE" screenshot "$SHOTS/${name}_${RESULT}.png" >/dev/null 2>&1
  kill -INT $REC 2>/dev/null; wait $REC 2>/dev/null      # SIGINT finalises the video file
  kill $LOG 2>/dev/null; wait $LOG 2>/dev/null
  # app crash reports written during this test on this simulator (macOS writes them a few seconds late)
  [[ $RESULT == FAIL ]] && sleep 8
  find "$HOME/Library/Logs/DiagnosticReports" -maxdepth 1 -name 'Wikipedia-*.ips' -newer "$TRACE/$name/.start" 2>/dev/null | while read -r ips; do
    grep -q "$DEVICE" "$ips" && { mkdir -p "$TRACE/$name/crash"; cp "$ips" "$TRACE/$name/crash/"; echo "   app crash report: $(basename "$ips")"; }
  done
  rm -f "$TRACE/$name/.start"

  REASON=""
  [[ $RESULT == FAIL ]] && REASON=$(grep -m1 -E "FAILED|Assertion|Element not found" "$TRACE/$name.log" | tr -d '"\\' | cut -c1-200)
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$NN" "$tc" "$short" "$RESULT" "$DUR" "$(grep -m1 '^tags:' "$f" | sed 's/tags: *//')" "$REASON" >> "$REP/.rows.tsv"
  sed -n '1s/^# //p' "$f" >> "$REP/.titles.txt"
  echo "   $RESULT (${DUR}s)"
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
