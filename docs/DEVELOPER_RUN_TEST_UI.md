# Run & Manual UI Test Guide

This guide explains how to run the project locally and perform a quick manual UI test of the frontend.

## Prerequisites
- Python 3.10+ installed (`python3` on Linux)
- Node.js (16+ / 18 recommended) and `npm`
- A Neon PostgreSQL connection URL for the primary backend (`DATABASE_URL`)

Note: The primary backend requires a Neon PostgreSQL URL. Set `DATABASE_URL` in your environment or a `.env` file in the repository root before starting the backend.

## Quick start (recommended)
1. From the repository root, install all dependencies and start all services:

```bash
# install deps for backend, customer service, and frontend
make install

# start backend, customer service, and frontend (dev)
./run-all.sh
```

This will start services on these default ports:
- Frontend: http://localhost:5173
- Primary Backend: http://localhost:8000
- Customer Service Backend: http://localhost:8001

Use `make status` to tail logs and `make stop` to stop the services.

## Manual start (component-by-component)

1. Backend (primary)

```bash
# create a venv and install backend deps (if not done via make)
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# ensure DATABASE_URL is set (Neon URL required)
export DATABASE_URL="postgresql+psycopg://...@...neon.tech/..."

# run the primary backend (FastAPI / uvicorn)
backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000
```

2. Customer Service Backend

```bash
python3 -m venv customer-service-backend/.venv
source customer-service-backend/.venv/bin/activate
pip install -r customer-service-backend/requirements.txt

# default port is 8001 (configurable via .env)
cd customer-service-backend
./run.py
```

3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend uses Vite and runs on port 5173 by default.

## Environment configuration
- The primary backend requires `DATABASE_URL` (Neon PostgreSQL). Example location: add to a `.env` file at the repo root or export in your shell.
- The customer service backend reads `.env` in `customer-service-backend/` (see `app/config.py`).

## Logging and status
- Logs are written to the `logs/` directory when started via `make dev` or `run-all.sh`.
- PIDs are stored in `tmp/pids` when started by the Makefile.

Common commands:

```bash
# show running PIDs + tail logs
make status

# stop all services started via Makefile
make stop

# view logs directly
tail -n 200 logs/backend.log
tail -n 200 logs/frontend.log
tail -n 200 logs/customer-service.log
```

## Manual UI testing checklist
Open the frontend in your browser at http://localhost:5173 and exercise the following pages and checks:

- Home / Dashboard
  - Confirm the app loads without JS errors.
  - Confirm the dashboard shows summary widgets (if available).

- Approvals
  - Navigate to Approvals and verify the list loads.
  - Click an approval row and exercise approve/reject flows.

- Audit / Events
  - Open the Audit/Events page and check events are displayed and timestamps are correct.

- Customer Service / Simulate
  - Use the Simulate or Customer Service page to create a test run.
  - Verify the simulation invokes the backend (check network tab or backend logs).

- Findings / Runs
  - Open Findings and Runs pages and confirm items are displayed.

For each interaction, verify the following:

- Network: Inspect the browser devtools Network tab to ensure API calls return 200 and expected payloads.
- Backend: Check backend logs (`logs/backend.log`) for incoming requests and any errors.
- Customer Service: Check `logs/customer-service.log` for simulated service activity.

## Troubleshooting
- If the backend errors about `DATABASE_URL`, confirm it is exported or present in `.env` and that it points to a Neon PostgreSQL URL.
- If CORS errors appear, confirm the frontend URL is included in `FRONTEND_URL` or `ENVIRONMENT` settings.
- If ports are in use, stop conflicting services or change ports in the Makefile or run commands.

## Notes
- Dev defaults: frontend 5173, backend 8000, customer service 8001 (see `Makefile`).
- The primary backend performs DB initialization in its startup lifecycle; run `make db-init` after installing dependencies to initialize the schema if needed.

---
Created to help developers run and manually test the UI quickly.
