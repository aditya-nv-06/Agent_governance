# Setup

Prerequisites

- Python 3.10+ (python3)
- Node.js 16+ and npm
- Access to a Neon PostgreSQL database for `DATABASE_URL`

Install everything (recommended):

```bash
# from repository root
make install
```

This runs:
- `make install-backend` — creates a virtualenv and installs backend deps
- `make install-customer-service` — same for customer-service
- `make install-frontend` — runs `npm install` in `frontend`

Virtualenvs

- Backend venv: `backend/.venv`
- Customer service venv: `customer-service-backend/.venv`

Environment variables

- `DATABASE_URL` — required for the primary backend (Neon PostgreSQL URL). Set this in the repo root `.env` or export it in your shell.
- `FRONTEND_URL` — optional override for frontend origin used by CORS in development.

Database initialization

To initialize the DB schema after installing dependencies:

```bash
make db-init
```
