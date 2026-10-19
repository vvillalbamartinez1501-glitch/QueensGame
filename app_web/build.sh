#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${API_BASE_URL:-}" ]]; then
  echo "Error: define API_BASE_URL with the public HTTPS URL of the FastAPI backend." >&2
  exit 1
fi

if ! command -v flutter >/dev/null 2>&1; then
  if ! command -v git >/dev/null 2>&1; then
    echo "Error: Flutter is not installed and git is unavailable to download it." >&2
    exit 1
  fi

  flutter_root="${TMPDIR:-/tmp}/flutter-sdk"
  git clone --depth 1 --branch stable https://github.com/flutter/flutter.git "$flutter_root"
  export PATH="$flutter_root/bin:$PATH"
fi

flutter config --enable-web --no-analytics
flutter pub get
flutter build web --release --dart-define="API_BASE_URL=${API_BASE_URL}"
