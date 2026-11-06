#!/usr/bin/env bash
# Create (or verify) every AVD listed in config/devices.csv. Idempotent.
# SDK root: ANDROID_HOME (set sdkmanager --sdk_root via ANDROID_HOME/ANDROID_SDK_ROOT). Needs: sdkmanager + avdmanager on PATH (brew install --cask android-commandlinetools), ANDROID_HOME set.
set -euo pipefail
cd "$(dirname "$0")/../.."
ABI=$(uname -m); [[ "$ABI" == "arm64" ]] && ABI=arm64-v8a || ABI=x86_64
LATEST=$( { sdkmanager --list 2>/dev/null | grep -o "system-images[;/]android-[0-9.]*[;/]google_apis[;/]$ABI" | sed 's/.*android-\([0-9.]*\)[;\/].*/\1/';
            ls "${ANDROID_HOME:?set ANDROID_HOME}/system-images" 2>/dev/null | sed -n 's/^android-\([0-9.]*\)$/\1/p'; } | sort -V | tail -1 || true )
echo "Latest Android API with google_apis/$ABI image: ${LATEST:-none found}"
grep -v '^#' config/devices.csv | while IFS=, read -r id avd profile api class enabled notes; do
  [[ "$enabled" == "yes" ]] || { echo "skip $id (disabled)"; continue; }
  [[ "$profile" == "-" ]] && { avdmanager list avd -c | grep -qx "$avd" && echo "ok   $id ($avd exists)" || echo "MISSING existing AVD $avd"; continue; }
  [[ "$api" == "latest" ]] && api=$LATEST
  img="system-images;android-$api;google_apis;$ABI"
  [[ -d "$ANDROID_HOME/system-images/android-$api/google_apis/$ABI" ]] || sdkmanager --install "platforms;android-$api" "$img" >/dev/null
  if avdmanager list avd -c | grep -qx "$avd"; then echo "ok   $id ($avd exists)"; else
    echo no | avdmanager create avd -n "$avd" -k "$img" -d "$profile" --force && echo "made $id ($avd, API $api, $profile)"
  fi
done
