#!/bin/bash
# Builds a signed release APK. Needs signing/keystore.properties (not stored in git).
set -e
cd "$(dirname "$0")"
[ -f signing/keystore.properties ] || { echo "Missing signing/keystore.properties"; exit 1; }
get() { grep "^$1=" signing/keystore.properties | cut -d= -f2-; }
./gradlew assembleMadaniRelease -PdisableFirebase \
  -PSTORE_FILE="$PWD/$(get STORE_FILE)" \
  -PSTORE_PASSWORD="$(get STORE_PASSWORD)" \
  -PKEY_ALIAS="$(get KEY_ALIAS)" \
  -PKEY_PASSWORD="$(get KEY_PASSWORD)"
echo
echo "APK: app/build/outputs/apk/madani/release/"
ls -lh app/build/outputs/apk/madani/release/*.apk
