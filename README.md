# Agent Governance Platform — v1

A focused governance layer for autonomous agents. It defines approved behavior, observes each runtime request, checks its tool/data/action scope and usage limit, blocks deviations, supports controlled human approval, and records the full trail.

## Architecture

``` text
React dashboard ── /api proxy ──> FastAPI
                                     │
                                     ├── Behavior profile (tools, data, actions, thresholds)
                                     ├── Agent runner → policy evaluator → mock tool adapter
                                     └── PostgreSQL (runs, findings, approvals, audit events)
```

## Governance flow

```text
User request → decision layer creates ToolRequest → governance evaluation
                                                   ├─ allowed → execute → run completed → audit
                                                   └─ denied  → finding → agent blocked → approval → audit
                                                                                       ├─ approve → resume → execute original tool
                                                                                       └─ reject  → block confirmed
```

## Run locally

1. Configure `backend/.env` with `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/agent_governance`.
2. Start the API: `cd backend && ./.venv/bin/uvicorn app.main:app --reload`
3. Start the dashboard: `cd frontend && npm install && npm run dev`
4. Seed a demo agent and its profile once: `cd backend && ./.venv/bin/python seed.py`

Open `http://localhost:5173`. The Vite proxy forwards `/api` requests to FastAPI.

## Demo scenario

The seeded Customer Support Agent is permitted to use `faq_search` and `send_email`.

- Enter a FAQ request: the run completes and writes `AGENT_RUN_STARTED`, `TOOL_REQUESTED`, `TOOL_ALLOWED`, `TOOL_EXECUTION`, and `RUN_COMPLETED` audit events.
- Enter a request containing `customer` or `database`: the agent selects `customer_database`, which is unauthorized. v1 creates a high-severity finding, blocks the agent, creates an approval, and records `FINDING_CREATED`, `APPROVAL_REQUESTED`, and `AGENT_BLOCKED`.
- Approve the pending request in the dashboard to resume the agent, then select **Execute**. The API executes only the tool captured in the original finding and writes an `APPROVED_ACTION_EXECUTED` audit event. A pending or rejected approval receives `403` from this endpoint.
- Reject the request to keep the block confirmed.

## API surface

- `GET /agents`, `POST /agents`, `GET /profiles`, `POST /profiles`, `PUT /profiles/{id}`
- `POST /runs`, `GET /runs`
- `GET /findings`, `GET /approvals`, `POST /approvals/{id}/decision`, `POST /approvals/{id}/execute`, `GET /audit`

Interactive API documentation is available at `http://localhost:8000/docs`.

## Design notes and limitations

- The agent is deliberately small and deterministic; the important v1 behavior is the governance boundary, not an LLM implementation.
- Tool selection is monitored at the runtime gateway. Tool, data source, and action are enforced using tool metadata. A daily run count acts as the v1 LLM-call usage metric and writes a warning audit event at configured warning/critical thresholds; usage over the configured maximum is blocked.
- The startup migration is additive for the initial local PostgreSQL schema. A production version should replace it with Alembic migrations and authentication/role checks around profile and approval changes.
