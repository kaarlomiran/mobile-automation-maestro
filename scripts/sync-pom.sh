#!/usr/bin/env bash
# Fetch the Page Object Model repo into ./pom at the ref pinned in pom.lock.
# Local dev: POM_LOCAL=/path/to/mobile-pom-maestro ./scripts/sync-pom.sh  (copies your working tree)
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf pom
if [[ -n "${POM_LOCAL:-}" ]]; then
  mkdir pom && rsync -a --exclude .git "$POM_LOCAL"/ pom/
else
  REPO=$(grep '^repo=' pom.lock | cut -d= -f2-); REF=$(grep '^ref=' pom.lock | cut -d= -f2-)
  git clone --quiet "$REPO" pom && git -C pom checkout --quiet "$REF"
fi
echo "POM ready in ./pom"
