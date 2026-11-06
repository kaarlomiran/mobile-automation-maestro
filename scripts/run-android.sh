#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
APP_ID=$(grep '^APP_ID=' config/android.env | cut -d= -f2)
# extra arguments (for example --format=junit --output=report-android.xml) pass through
maestro test -e APP_ID="$APP_ID" "$@" flows/common flows/android
