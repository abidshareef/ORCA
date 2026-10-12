# ORCA event runbook

## The intended end-to-end path

1. The dashboard loads the available scenario list from `GET /api/scenarios`.
2. A user selects a scenario and sends `POST /api/analyze` with its `scenario_id`.
3. The API loads the checked-in scenario JSON in the default `ORCA_DATA_MODE=demo` mode.
4. The anomaly detector compares numeric observations with the configured reference baselines.
5. The orchestrator runs the five specialized agents concurrently.
6. The orchestrator combines agent predictions using confidence-weighted aggregation and derives a risk category.
7. The API returns structured risk, anomaly, agent, evidence and recommendation fields.
8. The dashboard renders the risk summary, map marker, agent chart, evidence cards and data-source label.

## Important data boundary

The scenarios are controlled illustrative inputs, not live marine measurements. The UI and API label them as demo data. Do not describe the event build as a live monitoring system unless live provider integrations and data provenance have been implemented and verified.

## Local run

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:ORCA_DATA_MODE = "demo"
python -m uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend-app
npm install
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm run dev
```

Open the Vite URL printed in the terminal. API docs are at `http://localhost:8000/docs`.

## Deploy the API on Render

1. Create a new Web Service from this repository.
2. Use the `stabilization/event-ready` branch for review, or merge the branch to `main` before production deployment.
3. Runtime: Python; build command: `pip install -r requirements.txt`.
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
5. Health-check path: `/api/ready`.
6. Set `ORCA_DATA_MODE=demo` and `CORS_ORIGINS` to the exact deployed frontend origin.
7. Confirm `/api/health`, `/api/ready`, `/api/scenarios` and all four POST analysis requests.

A PostgreSQL database is not required for the default demo deployment.

## Deploy the dashboard on Vercel

1. Import this repository into Vercel.
2. Set **Root Directory** to `frontend-app`.
3. Framework preset: Vite; build command: `npm run build`; output directory: `dist`.
4. Set `VITE_API_BASE_URL` to the public Render API origin, without a trailing slash.
5. Redeploy after setting the variable.
6. Update Render's `CORS_ORIGINS` with the exact Vercel origin and redeploy the API.

## Database mode (optional; not needed for the event demo)

1. Start PostgreSQL/PostGIS with `docker compose up -d db`.
2. Set `DATABASE_URL` to the matching database connection string.
3. Apply `backend/database/schema.sql` to a fresh database.
4. Run `python scripts/seed_demo.py` from the repository root.
5. Set `ORCA_DATA_MODE=database` and restart the API.
6. Verify all four scenarios before relying on this mode.

The schema uses JSONB for embeddings so it works with the supplied PostGIS image. This does not provide vector similarity search; configure pgvector separately if that feature is required.

## Event smoke-test checklist

- [ ] API readiness responds with HTTP 200.
- [ ] Scenario selector loads.
- [ ] Each of the four scenarios returns HTTP 200 and five agent findings.
- [ ] The risk level, evidence and recommendation change according to the selected scenario.
- [ ] Map, chart and evidence cards render on desktop and mobile.
- [ ] The data-source disclaimer remains visible.
- [ ] The demo works in a fresh browser session.
- [ ] A local browser tab with the deployed API docs is ready as a fallback.
