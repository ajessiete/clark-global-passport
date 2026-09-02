# Clark Global Passport v8 — Free Online Deployment

This version can run locally with SQLite or online with PostgreSQL.

## Local use
No online database is required.

```bash
python -m pip install -r requirements.txt
python app.py
```

Open:
http://127.0.0.1:5000

## Free online architecture
Recommended prototype setup:

- GitHub — private repository
- Render — free Flask web service
- Neon or another PostgreSQL provider with a suitable free tier — database
- Render-generated HTTPS URL

The app reads these environment variables:

- `SECRET_KEY`
- `DATABASE_URL`
- `PORT` (hosting platforms usually provide this automatically)

If `DATABASE_URL` is missing, the app automatically uses local SQLite.

## Render settings
Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
gunicorn app:app
```

Health check:

```text
/health
```

## Database URL
Paste your PostgreSQL connection string into Render as the `DATABASE_URL`
environment variable.

The code automatically converts legacy `postgres://` URLs to
`postgresql://`.

## Important
The free online version is intended for development, demonstrations, and
small pilots. Do not use real student data until the school has approved
the hosting, privacy, access-control, backup, and data-retention setup.

Do not commit:
- `.env`
- SQLite database files
- secret keys

The included `.gitignore` prevents these from being uploaded to GitHub.
