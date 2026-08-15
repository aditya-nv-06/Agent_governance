# Development Guide

This guide is meant for contributors working on the governance platform locally or in CI.

## Local prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ for local full-stack integration
- A browser for the React dashboard

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/` with values such as:

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/agent_governance
AUTH_SECRET=super-secret-value
OPENAI_API_KEY=your-key-if-live-decisions-are-enabled
ALLOW_SQLITE_FOR_TESTS=true
```

For tests, SQLite is allowed explicitly when the environment variable is set.

## Seed the demo data

```bash
cd backend
source .venv/bin/activate
python seed.py
```

This ensures the admin `adityanv4@gmail.com` is available with a demo agent and behavior profile.

## Run the API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Swagger UI is available at http://127.0.0.1:8000/docs.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The Vite app uses a proxy for `/api` requests to the FastAPI service.

## Validation commands

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

```bash
cd frontend
npm run build
```

## Required behavior rules

- Agents must include a profile at creation time.
- The profile is stored as a `BehaviorProfile` record linked to the agent.
- Agents are owner-scoped to the logged-in admin.
- Delete operations remove related findings, runs, audit records, profiles, and the agent itself.

## CI expectations

GitHub Actions runs backend tests and frontend build validation on pull requests and pushes.
