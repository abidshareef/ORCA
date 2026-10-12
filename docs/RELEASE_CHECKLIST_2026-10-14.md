# ORCA Release Readiness — 14 October 2026

## Delivery rule

Do not describe ORCA as a live ecological forecasting platform. The current release is a marine-intelligence prototype with:
- scenario-based ecosystem assessment from checked-in JSON by default;
- five heuristic domain agents and an anomaly detector with illustrative baseline values;
- a live Open-Meteo marine wave-forecast adapter when coordinates are provided;
- query-intent routing and source/limitation disclosures.

It does **not** yet provide validated live satellite/ecological ingestion, operational PFZ discovery, official marine safety alerts, route planning, geofencing, or a scientifically calibrated ecosystem-risk model.

## Workstreams (small-team ownership model)

### 1. Frontend engineer
- Configure `VITE_API_BASE_URL` to the deployed API origin.
- Verify query form, scenario selector, loading states, API-offline state, API errors, map, charts, agent findings, and source/limitations copy.
- Confirm marine conditions require both coordinates and show source plus forecast timestamp.
- Never label scenario measurements as live observations.

### 2. Backend / data-pipeline engineer
- Keep `ORCA_DATA_MODE=demo` for the event unless PostgreSQL has been initialized and seeded with valid observations.
- Verify `/api/health`, `/api/ready`, `/api/scenarios`, `POST /api/analyze`, `POST /api/query`, and `GET /api/marine/conditions`.
- Preserve provider provenance, timestamp checks, coordinate validation, timeout handling, and clear 503 errors.
- Do not map wave forecasts into ecological fields such as pollution, oxygen, or biodiversity.

### 3. AI/ML engineer
- Validate that each agent receives only fields relevant to its domain.
- Keep confidence and risk scores clearly marked as prototype outputs; do not claim model validation without a held-out dataset and metrics.
- Test missing-data behavior, anomalies, multi-agent aggregation, and explanations.
- Future work: replace fixed baselines with source-backed seasonal baselines and evaluate on independent observations.

### 4. Integration / QA owner
- Run backend tests and frontend production build on every change.
- Test the API through the frontend, not only by calling agent functions directly.
- Test one success and one failure path for each external provider.
- Record actual deployment URLs and smoke-test them after deployment.

## Local verification

From repository root:

```bash
python -m pip install -r requirements.txt
python -m compileall -q backend scripts
ORCA_DATA_MODE=demo python -m pytest -q
```

From `frontend-app/`:

```bash
npm install
npm run build
```

On Windows PowerShell, set the mode with:

```powershell
$env:ORCA_DATA_MODE = "demo"
python -m pytest -q
```

## API smoke-test matrix

| Check | Expected result |
|---|---|
| `GET /api/health` | HTTP 200; service status `ok` |
| `GET /api/ready` in demo mode | HTTP 200; status `ready` |
| `GET /api/scenarios` | Four named demo scenarios |
| `POST /api/analyze` with each known scenario | HTTP 200; risk score in [0, 1]; five agent findings |
| `POST /api/analyze` with unknown scenario | HTTP 404 |
| `POST /api/query` with pollution query | Routes to Pollution Detection Agent; scenario prototype notice |
| `POST /api/query` with PFZ query | Explicitly says live PFZ discovery is unavailable |
| `POST /api/query` with marine-conditions query and no coordinates | Requests both coordinates; no fabricated forecast |
| `POST /api/query` with invalid coordinates | HTTP 422 |
| Marine provider malformed/stale/invalid response | Controlled provider error, not fabricated values |
| Frontend production build | Vite build succeeds |

The repository CI should be green before release. A green CI run proves automated checks passed; it does not prove the hosted services are deployed or that third-party APIs are reachable from the deployment.

## Render + Vercel release sequence

1. Deploy the repository's `render.yaml` as the `orca-api` service in Render.
2. Wait for Render's `/api/ready` health check to pass. Confirm `/api/health` and `/api/scenarios` from the public Render URL.
3. Deploy `frontend-app/` to Vercel with framework Vite, build command `npm run build`, output directory `dist`.
4. Set Vercel project environment variable `VITE_API_BASE_URL` to the exact public Render API URL (no trailing slash), then redeploy the frontend.
5. Open the public Vercel URL and run an ecosystem scenario plus a marine query using valid ocean coordinates.
6. Check browser console/network for CORS, failed requests, map tile, and rendering errors. Confirm the displayed source and limitations.
7. Record both URLs and the exact successful smoke-test results in the event handoff.

The Render configuration uses wildcard CORS for the public, unauthenticated demo so the first deployment is not blocked by a placeholder Vercel hostname. Restrict `CORS_ORIGINS` to the exact frontend origin before adding authenticated or user-specific functionality.

## Release acceptance gates

- [ ] CI backend tests pass.
- [ ] Frontend production build passes.
- [ ] Render readiness endpoint is green.
- [ ] Frontend can reach the deployed API.
- [ ] Scenario and marine-forecast flows both work end-to-end.
- [ ] Upstream timeout / unavailable forecast shows a controlled error.
- [ ] Demo values, live forecast values, timestamps, and limitations are visibly distinguished.
- [ ] No secrets are committed.
- [ ] Final presentation states current limitations accurately.
