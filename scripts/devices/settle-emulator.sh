#!/usr/bin/env bash
# Dismiss "<system app> isn't responding" dialogs that slow or freshly booted emulators raise over the app under test
# (seen: "System UI" locally, "Pixel Launcher" on GitHub runners). A dialog for the APP UNDER TEST is never dismissed:
# that is a real failure and the tests must see it.
# Usage: settle-emulator.sh <serial> <app_id> [clean checks in a row, 5 s apart, default 1]
S="$1"; APP="$2"; NEED="${3:-1}"; clean=0
for i in $(seq 1 30); do
  ANR=$(adb -s "$S" shell dumpsys window 2>/dev/null </dev/null | grep -o 'Application Not Responding: [A-Za-z0-9._:]*' | head -1 | awk '{print $NF}')
  if [[ -z "$ANR" ]]; then
    clean=$((clean+1)); [[ $clean -ge $NEED ]] && exit 0; sleep 5; continue
  fi
  if [[ "$ANR" == "$APP"* ]]; then echo "settle: the app under test ($APP) is not responding - leaving the dialog"; exit 0; fi
  clean=0
  BUTTON="Wait"; [[ "$ANR" == *launcher* ]] && BUTTON="Close app"     # a restarted launcher does not re-raise the dialog
  echo "settle: '$ANR' is not responding, choosing '$BUTTON'"
  adb -s "$S" shell uiautomator dump /sdcard/anr.xml >/dev/null 2>&1 </dev/null
  XY=$(adb -s "$S" shell cat /sdcard/anr.xml 2>/dev/null </dev/null | tr '>' '\n' | grep "text=\"$BUTTON\"" | grep -o 'bounds="\[[0-9]*,[0-9]*\]\[[0-9]*,[0-9]*\]"' | head -1 | tr -c '0-9\n' ' ' | awk 'NF==4{print int(($1+$3)/2), int(($2+$4)/2)}')
  [[ -n "$XY" ]] && adb -s "$S" shell input tap $XY </dev/null
  sleep 5
done
echo "settle: a not-responding dialog is still showing after 30 attempts"; exit 1
