# Development Guide

This guide helps contributors set up and work on the project locally.

Prerequisites
-------------

- Python 3.11+
- Node.js 18+
- PostgreSQL (recommended) or SQLite for lightweight testing

Backend setup
-------------

1. Create and activate a virtual environment, then install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create `backend/.env` (example):

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/agent_governance
AUTH_SECRET=super-secret-value
OPENAI_API_KEY=your-key-if-live-decisions-are-enabled
# Optional for allowing SQLite in tests
ALLOW_SQLITE_FOR_TESTS=true
```

3. Seed demo data (optional):

```bash
source .venv/bin/activate
python seed.py
```

4. Run the API for development:

```bash
uvicorn app.main:app --reload --port 8000
```

Open the interactive docs at `http://127.0.0.1:8000/docs`.

Frontend setup
--------------

1. Install and run the Vite dev server:

```bash
cd frontend
npm install
npm run dev
```

2. The frontend proxies `/api` to the backend in dev mode. If your backend is on a different host/port, set `VITE_API_URL` in your environment.

Testing and validation
----------------------

Backend unit tests:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Frontend build check:

```bash
cd frontend
npm run build
```

Key development notes
---------------------

- Agent creation: the backend requires a `profile` payload when creating an agent. The frontend `Agents` form submits a `profile` object alongside the agent; review `frontend/src/components/Agents.jsx` if you change the UI.
- Sessions: the frontend stores per-admin sessions in `localStorage` under `agent-governance-admin:<adminId>` and the active admin id under `agent-governance-active-admin`. Clearing sessions is handled by the Sign out action in the UI.
- Deleting an agent: the DELETE API removes approvals, findings, runs, audit events, and the behavior profile before deleting the agent row. Ownership is enforced—only the admin who owns the agent may delete it.

Debugging tips
--------------

- If agent creation returns a validation error, ensure the JSON body contains the `profile` object (name + allowed lists + thresholds).
- For authorization failures, inspect the request `Authorization` header in your browser devtools Network tab to ensure the `access_token` is present.
- Backend logs: when running with `uvicorn`, errors and traceback appear in the terminal. The backend also logs agent deletion attempts and failures.

CI
--

CI workflows validate backend tests and frontend builds in `.github/workflows/`.

If you want, I can also add a short CONTRIBUTING.md with a checklist for PRs and local pre-commit hooks.
