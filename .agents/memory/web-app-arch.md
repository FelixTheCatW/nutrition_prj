---
name: Web App architecture
description: How the FastAPI + Vue3 web layer is structured and started
---

## Stack
- FastAPI backend: `src/web/api.py`, runs via uvicorn on port **8080** (background in start_web.sh)
- Vue 3 + Vite frontend: `web/` directory, runs on port **5000** (foreground in start_web.sh)
- Vite proxies `/api/*` → `http://localhost:8080`
- Workflow "Web App": `bash start_web.sh`, waitForPort 5000, outputType webview

## Key files
- `src/web/api.py` — all 10 report endpoints + `/api/users`
- `web/src/App.vue` — main layout, keyboard nav (↑↓ Enter U 1-0)
- `web/src/components/ReportPanel.vue` — all 10 report visualizations (Chart.js via vue-chartjs)
- `web/src/components/UserModal.vue` — user picker modal (U key)
- `start_web.sh` — starts uvicorn in bg, then Vite in fg; trap kills uvicorn on exit

## DB init
`DBConfig.load_from_env()` reads PGDATABASE/PGHOST/PGPORT/PGUSER/PGPASSWORD env vars (Replit secrets).
FastAPI uses lifespan context for startup.

**Why two processes:** Vite provides HMR during development; proxy keeps API calls working without CORS issues.
