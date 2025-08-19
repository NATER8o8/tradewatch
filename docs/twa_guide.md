
# Trusted Web Activity (TWA) wrapper (Android)

This app is installable as a PWA. If you want a Play‑distributable APK, wrap it with a TWA.

## Quick path (Bubblewrap)
1. Install Node 18+.
2. `npm i -g @bubblewrap/cli`
3. Ensure your site is served at **https://your-domain** (valid cert; self‑signed is not enough for push).
4. Run: `bubblewrap init --url https://your-domain --manifest https://your-domain/manifest.json`
5. Open Android Studio, import the generated project, set package name & signing.
6. Build → Generate Signed App Bundle / APK.

**Notes**
- Web Push requires a trusted certificate; use a real domain and cert (Let’s Encrypt).
- Keep your PWA manifest `start_url`, `scope`, and icons consistent.

For reference, see `/webapp/public/manifest.json` and `scripts/run_https.sh` (for local testing).
