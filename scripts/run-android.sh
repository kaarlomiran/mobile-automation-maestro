#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -d pom ]] || ./scripts/sync-pom.sh
APP_ID=$(grep '^APP_ID=' config/android.env | cut -d= -f2)
# extra arguments (for example --format=junit --output=report-android.xml) pass through
DIRS=()
for d in flows/common flows/android; do
  ls "$d"/*.yaml >/dev/null 2>&1 && DIRS+=("$d")
done
maestro test -e APP_ID="$APP_ID" "$@" "${DIRS[@]}"
