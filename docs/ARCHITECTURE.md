# Architecture

High-level components

- Frontend — Vite + React app in `frontend/`. Communicates with the primary backend APIs and optional customer-service backend.
- Primary Backend — FastAPI app in `backend/` exposing governance APIs and performing DB operations.
- Customer Service Backend — lightweight FastAPI app in `customer-service-backend/` used to simulate agent interactions.
- Database — Neon PostgreSQL (configured via `DATABASE_URL`)

Important notes

- CORS: The primary backend allows origins for local development (`http://localhost:5173`, `http://localhost:3000`) and the value of `FRONTEND_URL` in production.
- DB initialization: The primary backend runs initialization logic at startup (see `backend/app/startup.py`). Use `make db-init` to explicitly run initialization.

Repository layout (high-level)

- `frontend/` — UI
- `backend/` — main API and governance logic
- `customer-service-backend/` — auxiliary service used by demos and simulations
- `docs/` — developer documentation
