# AI Agent Governance Platform

A full-stack governance layer for LLM-powered agents. The app enforces which tools, data sources, and actions are allowed, applies usage guardrails, records audit events, and provides a human-in-the-loop approval flow for high-risk operations.

Quick links
- [Development guide](docs/DEVELOPMENT_GUIDE.md)
- API docs (when running backend): `/docs`

Why this project
------------------
LLM-based agents can propose external actions. This project places a policy layer between the agent and external systems that:

- Blocks unauthorized actions
- Logs every decision and action to an audit trail
- Requires human approval for higher-risk actions
- Tracks usage and enforces warning/critical thresholds

What’s included
----------------
- Backend: FastAPI + SQLAlchemy (Postgres supported, SQLite for testing)
- Frontend: React + Vite + Tailwind CSS dashboard
- Governance: policy evaluation, findings, approvals, enforcement

Project layout
--------------
See the main application folders and responsibilities:

```
backend/            Python API, models, governance engine, tests
frontend/           React dashboard, API client
docs/               Diagrams and developer documentation
```

Quickstart (local)
-------------------
Prereqs: Python 3.11+, Node.js 18+, PostgreSQL (optional)

1) Backend: create virtualenv and install

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure environment

Create `backend/.env` with at least:

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/agent_governance
AUTH_SECRET=change-this-secret
# Optional when using a real LLM provider
OPENAI_API_KEY=your-key
```

For local development you may allow SQLite for tests by setting `ALLOW_SQLITE_FOR_TESTS=true`.

3) Seed demo data (optional)

```bash
source .venv/bin/activate
python seed.py
```

4) Run backend

```bash
uvicorn app.main:app --reload --port 8000
```

5) Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` to the backend in dev mode.

API overview & examples
------------------------
Key endpoints (authenticated):

- `POST /auth/register` — create an admin
- `POST /auth/login` — obtain `access_token` and `admin` info
- `GET /agents` — list agents owned by the admin
- `POST /agents` — create an agent (must include `profile`)
- `DELETE /agents/{agent_id}` — delete agent and related records
- `GET /profiles`, `POST /profiles` — manage behavior profiles

Example: create agent (profile required)

```bash
curl -i -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Agent",
    "description": "Helps customers",
    "profile": {
      "name": "Support profile",
      "allowed_tools": ["send_email"],
      "allowed_data_sources": ["crm"],
      "allowed_actions": ["read","send_email"],
      "max_llm_calls": 1000,
      "warning_threshold": 80,
      "critical_threshold": 90
    }
  }'
```

Troubleshooting
---------------

- Agent creation fails: the API enforces a behavior `profile` on create. Ensure the payload includes a `profile` object (see example above).
- Session shows wrong user: the frontend stores per-admin session data to avoid overwriting multiple admin sessions in the same browser. If you experience wrong sessions, clear stored sessions from the browser (see `Sign out` in the UI).
- Delete agent appears to do nothing: the backend deletes related findings, runs, approvals, behavior profiles, audit events, and the agent record. If it fails, ensure the authenticated admin owns the agent and check backend logs or the network response in the browser devtools for details.

Testing
-------

Run backend tests:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Run frontend build check:

```bash
cd frontend
npm run build
```

Contributing
------------
- See `docs/DEVELOPMENT_GUIDE.md` for local environment setup and tips for working on the codebase.

License & CI
------------
- CI workflows validate backend tests and frontend build in `.github/workflows/`.

