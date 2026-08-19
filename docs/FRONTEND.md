# Frontend developer notes

Location: `frontend/` (Vite + React)

Run dev server

```bash
cd frontend
npm install
npm run dev
```

Build for production

```bash
cd frontend
npm run build
npm run preview
```

Port

- Dev: 5173 (Vite default)

Linting

- `npm run lint` (configured in `frontend/package.json`)

Notes

- The UI talks to the primary backend on `http://localhost:8000` by default. Ensure the backend is running when testing UI features.

## Examples & screenshots

Capture these important pages to document UI behaviour or include in PRs:

- Home / Dashboard: `http://localhost:5173/`
- Approvals: `http://localhost:5173/approvals`
- Audit / Events: `http://localhost:5173/audit`
- Customer Service / Simulate: `http://localhost:5173/simulate`

Headless screenshot commands (Linux / Chrome):

```bash
# modern Chrome (headless "new" mode)
google-chrome --headless=new --disable-gpu --screenshot=docs/images/frontend/dashboard.png --window-size=1280,800 http://localhost:5173/

# legacy headless
google-chrome --headless --disable-gpu --screenshot=docs/images/frontend/dashboard.png --window-size=1280,800 http://localhost:5173/
```

Using Playwright (recommended if already installed):

```bash
# install (if needed): npm i -D @playwright/test
npx playwright screenshot http://localhost:5173/ --output=docs/images/frontend/dashboard.png --width=1280 --height=800
```

Screenshot guidelines

- Store screenshots under `docs/images/frontend/` and use descriptive names (e.g. `approvals-list.png`).
- Prefer 1280×800 or 1920×1080 for readability.
- When adding screenshots to PRs, include the page URL and the steps to reproduce the captured state.

Short example UI flow to document in screenshots or GIFs

1. Open the app at `http://localhost:5173/` and confirm the dashboard shows summary widgets.
2. Navigate to `Approvals` and capture the list view.
3. Click an approval row to open details and capture the modal/detail view.
4. Go to `Simulate`, create a simulated run, and capture the run results and any linked Findings.
