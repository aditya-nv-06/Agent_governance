# Contributing

Guidelines for contributing to this repository.

1. Fork the repository and create a feature branch.
2. Run linters and tests locally before submitting a PR:

```bash
# backend
make install-backend
source backend/.venv/bin/activate
pytest

# frontend
cd frontend && npm run lint
```

3. Keep changes focused and add tests where appropriate.
4. Write clear commit messages and a descriptive PR description.

Code style

- Python: follow existing project conventions (PEP8-ish). No automatic formatter enforced by repo.
- JS/React: follow existing patterns in `frontend/src/`.

Support

If you're unsure where to contribute, open an issue describing your idea.
