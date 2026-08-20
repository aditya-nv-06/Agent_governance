# AI Agent Governance Platform

A full-stack governance layer for LLM-powered agents. The platform enforces which tools, data sources, and actions are allowed, applies usage guardrails, records audit events, and provides a human-in-the-loop approval flow for higher-risk operations.

Jump to detailed developer docs in `docs/`.

## Brief approach

This project places a governance layer between LLM-powered agents and external systems to ensure safe, auditable, and policy-driven behavior. Key elements:

- Policy evaluation: each agent action is validated against behavior profiles (allowed tools, data sources, and actions).
- Guardrails and enforcement: the system can block or allow actions, apply warning/critical thresholds, and require human approval for higher-risk operations.
- Observability: findings, runs, approvals, and audit events are recorded for traceability and post-hoc review.
- Architecture: decoupled services — FastAPI backend (policy + DB), React + Vite frontend (UI), and a small customer-service backend for simulations; Neon Postgres is used for runtime persistence.
- Developer ergonomics: a `Makefile` and `run-all.sh` provide a repeatable local dev environment; developer docs live in `docs/`.

# Architecture diagram
![diagram](docs/architecture.png)


Quick links
- `docs/README.md` — project docs index
- `docs/SETUP.md` — prerequisites and install
- `docs/RUN.md` — how to run services locally
- API docs (when running primary backend): `/docs` (FastAPI)

What’s included
- Backend: FastAPI + SQLAlchemy (Postgres required for runtime; SQLite allowed for tests)
- Frontend: React + Vite + Tailwind CSS dashboard
- Governance: policy evaluation, findings, approvals, enforcement

Project layout

```
backend/            Python API, models, governance engine, tests
frontend/           React dashboard, API client
customer-service-backend/  auxiliary demo service
docs/               Developer documentation and run instructions
```

Quickstart (recommended)

Prereqs: Python 3.10+, Node.js 16+ (Node 18 recommended), Chrome for devtools

From the repository root the fastest path is:

```bash
# install deps for backend, customer-service, and frontend
make install

# start all dev services (frontend, primary backend, customer service)
./run-all.sh
```

This starts services on these defaults:
- Frontend: http://localhost:5173
- Primary Backend: http://localhost:8000
- Customer Service Backend: http://localhost:8001

Manual component start

- Primary backend (create venv if needed):

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# ensure DATABASE_URL is set (Neon Postgres URL)
export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@host.neon.tech/dbname"

backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000
```

- Customer service:

```bash
python3 -m venv customer-service-backend/.venv
source customer-service-backend/.venv/bin/activate
pip install -r customer-service-backend/requirements.txt
cd customer-service-backend
./run.py
```

- Frontend:

```bash
cd frontend
npm install
npm run dev
```

Notes on environment
- `DATABASE_URL` (required for primary backend) should point to a Neon PostgreSQL instance. You may set it in a `.env` file at the repository root or export it in your shell.
- The customer service backend reads `.env` in `customer-service-backend/`.
- For tests only, `ALLOW_SQLITE_FOR_TESTS=true` allows using SQLite test DBs.

Logs and control
- `make status` — show running PIDs and tail logs
- `make stop` — stop services started via the Makefile
- Logs: `logs/backend.log`, `logs/frontend.log`, `logs/customer-service.log`

Testing
- Backend tests: `make install-backend` then run `pytest` or the project's test commands from `backend/`.
- Frontend: build check with `cd frontend && npm run build`.

Contribution & docs
- See `docs/CONTRIBUTING.md` for contribution guidance.
- See `docs/DEVELOPER_RUN_TEST_UI.md` for a manual UI testing checklist and troubleshooting tips.

License & CI
- CI workflows validate backend tests and frontend build in `.github/workflows/`.

