#!/usr/bin/env bash
set -euo pipefail

if ! command -v flutter >/dev/null 2>&1; then
  if ! command -v git >/dev/null 2>&1; then
    echo "Error: Flutter is not installed and git is unavailable to download it." >&2
    exit 1
  fi

  flutter_root="${TMPDIR:-/tmp}/flutter-sdk"
  if [[ ! -x "$flutter_root/bin/flutter" ]]; then
    git clone --depth 1 --branch stable https://github.com/flutter/flutter.git "$flutter_root"
  fi
  export PATH="$flutter_root/bin:$PATH"
fi

flutter config --enable-web --no-analytics
flutter pub get
flutter build web --release --web-renderer html
