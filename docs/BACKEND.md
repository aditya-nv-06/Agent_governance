# Backend developer notes

Location: `backend/`

Environment

- `DATABASE_URL` — required (Neon PostgreSQL).
- `ENVIRONMENT` — `development` or `production` (affects CORS and reload behaviour).

Running locally

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL="postgresql+psycopg://...@...neon.tech/..."
backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000
```

Database

- The app validates that `DATABASE_URL` points to a Neon PostgreSQL URL. The code will raise if a non-Neon URL is used unless `ALLOW_SQLITE_FOR_TESTS=true` is set and the URL uses SQLite.

Useful targets

- `make install-backend` — create venv and install backend deps
- `make db-init` — run DB initialization logic

Development tips

- Logs are written to `logs/backend.log` when started via the Makefile.
- The startup lifecycle performs DB initialization; if you need to re-run, stop the service and run `make db-init`.
