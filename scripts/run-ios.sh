#!/usr/bin/env bash
# Quick iOS run without the evidence set (use run-ios-report.sh for real runs).
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -d pom/ios/pages ]] || ./scripts/sync-pom.sh
APP_ID=$(grep '^APP_ID=' config/ios.env | cut -d= -f2)
maestro test -e APP_ID="$APP_ID" "$@" flows/ios
