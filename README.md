# AI Agent Governance Platform

A full-stack governance layer for LLM-powered agents. The app enforces who may call which tools, which data sources and actions are permitted, and how many LLM calls are allowed before usage crosses warning or critical thresholds.

## Why this project exists

Large language models can propose tool calls, but they should not be allowed to decide policy on their own. This project adds a policy boundary that blocks unauthorized actions, logs every decision, and requires human approval for higher-risk steps.

## Key product rules

- An agent cannot be created without a behavior profile.
- Each agent is scoped to the authenticated admin user.
- Approval is required for blocked or sensitive actions.
- Every allowed, denied, and approved action is written to audit records.
- Delete-agent support is available for admins who own the agent.

## Architecture

![Runtime architecture](docs/architecture.png)

### Components

- Backend: FastAPI + SQLAlchemy + PostgreSQL/SQLite test support
- Frontend: React + Vite + Tailwind CSS
- Governance engine: policy checks for tools, data sources, actions, thresholds, and approvals
- Data model: admin users, agents, behavior profiles, runs, findings, approvals, audit events

## Behavior profile model

Each agent must include a behavior profile at creation time. The profile includes:

- name
- allowed tools
- allowed data sources
- allowed actions
- max LLM calls
- warning threshold
- critical threshold

The demo seed configuration creates a customer support agent whose approved behavior is intentionally narrower than the full tool registry.

## Demo flow

1. Create an admin account or log in.
2. Create an agent and attach a profile in the same step.
3. Run a prompt that triggers an allowed tool.
4. Run a prompt that attempts a disallowed tool.
5. Review the generated finding and approval workflow.
6. Approve or reject the request from the dashboard.

## Project structure

```text
backend/
  app/
    agent/            LLM decision support and execution helpers
    governance/       Policy evaluation, enforcement, and findings
    routes/           API layer for auth, agents, profiles, runs, findings, approvals, audit
    models.py         SQLAlchemy schema
    schemas.py        Validation models for API payloads
  tests/              Automated checks for auth, governance, and approvals
  seed.py             Local demo-data seeding
frontend/
  src/                React dashboard and API client
  package.json        frontend dependencies and scripts
docs/
  architecture.png   runtime diagram
.github/workflows/    CI automation for backend and frontend
```

## Local startup

### 1) Backend configuration

Create `backend/.env` with values like:

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/agent_governance
OPENAI_API_KEY=your-key-if-using-live-llm-decisions
AUTH_SECRET=change-this-secret
```

For tests, the app supports SQLite via environment variables when `ALLOW_SQLITE_FOR_TESTS=true`.

### 2) Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Seed demo data

```bash
cd backend
source .venv/bin/activate
python seed.py
```

This ensures the demo admin `adityanv4@gmail.com` is created and seeded with the sample agent configuration.

### 4) Run the API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 5) Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api` to the backend automatically when running through Vite.

## API overview

Key routes:

- `POST /auth/register`
- `POST /auth/login`
- `GET /agents`
- `POST /agents`
- `DELETE /agents/{agent_id}`
- `GET /profiles`
- `POST /profiles`
- `POST /runs`
- `GET /findings`
- `GET /approvals`
- `POST /approvals/{approval_id}/decision`
- `POST /approvals/{approval_id}/execute`
- `GET /audit`

The Swagger UI is available at `/docs` in the FastAPI app.

## Tests

Run the local backend tests with:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The suite covers:

- auth registration and login
- agent creation validation
- governance blocking for unauthorized and unknown tools
- warning and critical threshold behavior
- approval restrictions and approved execution rules

## GitHub workflow automation

The repository includes CI checks for both application layers:

- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`

These workflows run on push and pull request and validate that the backend tests still pass and the frontend still builds successfully.

## Troubleshooting

### Agent creation fails

The API now rejects requests with no behavior profile payload. Ensure the request includes a `profile` object when creating an agent.

### Session shows the wrong user data

The frontend stores session data under a user-specific key so that a second login does not overwrite the first one in the browser.

### Delete agent button does nothing

The backend route deletes related findings, runs, approvals, behavior profiles, audit events, and the agent record itself. If the endpoint still fails, confirm the authenticated admin owns the agent and the backend is running.

## Future improvements

- Add Alembic migrations for schema evolution
- Add stricter role-based authorization for approvers and admins
- Add deployment automation for staging and production
- Add end-to-end browser tests for the dashboard flow
