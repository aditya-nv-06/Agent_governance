# Testing

Backend tests

Run the Python test suite from the repository root:

```bash
# ensure backend venv and deps installed
make install-backend
source backend/.venv/bin/activate
pytest -q
```

Frontend tests / manual checks

- The repo contains UI components; there are no automated frontend tests by default. Use the manual checklist in [Developer run & UI test](DEVELOPER_RUN_TEST_UI.md) to exercise the UI.

Integration

- Start services (`./run-all.sh`) and use browser devtools to inspect network calls and backend logs.
