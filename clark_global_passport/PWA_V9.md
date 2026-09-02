# Clark Global Passport v9 — PWA

## What this version does

Clark Global Passport can now be installed from a supported browser and open like a standalone app.

The PWA intentionally uses a privacy-conscious offline design:

- CSS, JavaScript, icons, manifest, and the offline page are cached.
- Secure authenticated pages are fetched from the server and are not placed in the service-worker cache.
- Essay and reflection drafts can be stored locally on the student's own device.
- When offline, submitting to the server is not attempted successfully; the local draft remains available.
- Once connected again, the student reopens the task and submits normally.

## After uploading v9 to GitHub

Render should automatically redeploy if automatic deploys are enabled.

Check:

1. `/health` still returns `{"status":"ok"}`.
2. `/sw.js` displays JavaScript.
3. `/static/manifest.webmanifest` displays the manifest.
4. Open the app over HTTPS.
5. Chrome/Edge may show an install icon in the address bar or the in-app Install App button.

## Important privacy note

Do not make the service worker cache teacher dashboards, consultation notes, adviser notes, or other student records unless the school has approved an explicit offline data-storage policy.
