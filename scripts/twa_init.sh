
#!/usr/bin/env bash
set -euo pipefail
if ! command -v bubblewrap >/dev/null 2>&1; then
  echo "Install bubblewrap: npm i -g @bubblewrap/cli"
  exit 1
fi
: "${DOMAIN:?Set DOMAIN env to your site host (e.g., app.example.com)}"
bubblewrap init --manifest https://$DOMAIN/manifest.json
echo "Project generated. Open in Android Studio to build the APK/AAB."
