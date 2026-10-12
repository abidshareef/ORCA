# ORCA Event Dashboard

This is a standalone Vite/React frontend for the ORCA API. It is intentionally separate from the legacy `frontend` Git submodule pointer.

## Local development

From this directory:

```bash
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the backend origin if the API is not running at `http://localhost:8000`.

## Vercel

Import the repository and set **Root Directory** to `frontend-app`. Set this environment variable:

- `VITE_API_BASE_URL`: the public origin of the deployed FastAPI service, without a trailing slash.

The dashboard uses controlled demo scenarios. It labels those measurements as illustrative and does not present them as live ocean observations.
