# Run

Quick start (recommended):

```bash
# install deps and start all dev services
make install
./run-all.sh
```

Services (default ports)
- Frontend: http://localhost:5173
- Primary Backend: http://localhost:8000
- Customer Service Backend: http://localhost:8001

Manual start (component-by-component)

- Primary backend: `backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000`
- Customer service: `cd customer-service-backend && ./run.py`
- Frontend: `cd frontend && npm run dev`

Logs and status

- `make status` — show PIDs and tail logs
- `make stop` — stop services started by the Makefile

For a focused manual UI test, see [Developer run & UI test](DEVELOPER_RUN_TEST_UI.md).
