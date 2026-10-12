import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agents.orchestrator import OrcaOrchestrator
from backend.database.db_manager import db
from backend.ml.anomaly import AnomalyDetector
from backend.models.ecosystem import RiskAnalysis
from backend.services.query_planner import plan_query
from backend.services.marine_provider import get_marine_conditions, MarineProviderError

logger = logging.getLogger("orca")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

BASE_DIR = Path(__file__).resolve().parents[1]
SCENARIOS_PATH = BASE_DIR / "data" / "demo" / "scenarios.json"
DATA_MODE = os.getenv("ORCA_DATA_MODE", "demo").strip().lower()

app = FastAPI(
    title="ORCA Marine Ecosystem Intelligence API",
    version="1.0.0",
    description="Explainable, multi-agent marine ecosystem decision support.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

detector = AnomalyDetector()
orchestrator = OrcaOrchestrator()


class AnalysisRequest(BaseModel):
    scenario_id: str = Field(default="normal_ocean", min_length=1, max_length=100)


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    scenario_id: str = Field(default="normal_ocean", min_length=1, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


def load_scenarios() -> Dict[str, Dict[str, Any]]:
    """Load the checked-in, reproducible demo scenarios."""
    if not SCENARIOS_PATH.is_file():
        raise RuntimeError(f"Demo scenario file is missing: {SCENARIOS_PATH}")
    with SCENARIOS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    scenarios = payload.get("scenarios", [])
    indexed = {
        item["id"]: item
        for item in scenarios
        if isinstance(item, dict) and item.get("id") and item.get("locations")
    }
    if not indexed:
        raise RuntimeError("No valid demo scenarios were found.")
    return indexed


def scenario_state_from_json(scenario: Dict[str, Any]) -> Dict[str, Any]:
    location = scenario["locations"][0]
    state = dict(location.get("state", {}))
    state.update(
        {
            "latitude": float(location["latitude"]),
            "longitude": float(location["longitude"]),
            "depth": float(location.get("depth", 0.0)),
            "timestamp": datetime.now(timezone.utc),
        }
    )
    return state


def scenario_state_from_database(scenario_id: str) -> Dict[str, Any]:
    scenarios = load_scenarios()
    scenario = scenarios.get(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Unknown scenario_id.")

    query = """
        SELECT
            ST_Y(l.geom) AS latitude,
            ST_X(l.geom) AS longitude,
            COALESCE(l.depth, 0) AS depth,
            o.temperature, o.salinity, o.dissolved_oxygen, o.ph,
            o.chlorophyll, o.turbidity, o.pollution, o.biodiversity,
            o.fisheries, o.current, o.timestamp
        FROM locations AS l
        JOIN ecosystem_observations AS o ON l.id = o.location_id
        WHERE l.name = %s
        ORDER BY o.timestamp DESC
        LIMIT 1
    """
    result = db.fetch_one(query, (scenario["name"],))
    if not result:
        raise HTTPException(
            status_code=404,
            detail=(
                "Scenario data was not found in PostgreSQL. "
                "Initialize the schema and seed scenarios, or set ORCA_DATA_MODE=demo."
            ),
        )
    result = dict(result)
    result["timestamp"] = result.get("timestamp") or datetime.now(timezone.utc)
    return result


@app.get("/")
async def root():
    return {
        "service": "ORCA",
        "description": "Marine Ecosystem Reasoning with Collaborative Agents",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
async def health():
    """Liveness check: confirms that the API process is responding."""
    return {"status": "ok", "service": "ORCA", "data_mode": DATA_MODE}


@app.get("/api/ready")
async def ready():
    """Readiness check for the configured data path."""
    if DATA_MODE not in {"demo", "database"}:
        raise HTTPException(
            status_code=500,
            detail="ORCA_DATA_MODE must be either 'demo' or 'database'.",
        )
    try:
        if DATA_MODE == "demo":
            load_scenarios()
        else:
            db.fetch_one("SELECT 1 AS ready")
    except Exception:
        logger.exception("ORCA readiness check failed")
        raise HTTPException(status_code=503, detail="ORCA is not ready.")
    return {"status": "ready", "data_mode": DATA_MODE}


@app.get("/api/scenarios")
async def get_scenarios():
    try:
        scenarios = load_scenarios()
    except Exception:
        logger.exception("Unable to load scenarios")
        raise HTTPException(status_code=500, detail="Scenario data is unavailable.")
    return {
        "data_mode": DATA_MODE,
        "scenarios": [
            {
                "id": item["id"],
                "name": item["name"],
                "description": item.get("description", ""),
            }
            for item in scenarios.values()
        ],
    }


@app.post("/api/analyze", response_model=RiskAnalysis)
async def analyze_ecosystem(request: AnalysisRequest):
    if DATA_MODE not in {"demo", "database"}:
        raise HTTPException(
            status_code=500,
            detail="ORCA_DATA_MODE must be either 'demo' or 'database'.",
        )

    try:
        scenarios = load_scenarios()
        scenario = scenarios.get(request.scenario_id)
        if scenario is None:
            raise HTTPException(status_code=404, detail="Unknown scenario_id.")

        if DATA_MODE == "demo":
            state = scenario_state_from_json(scenario)
            data_source = "demo scenario JSON (simulated/reference data)"
        else:
            state = scenario_state_from_database(request.scenario_id)
            data_source = "PostgreSQL"

        numeric_state = {
            key: value
            for key, value in state.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        anomalies = detector.calculate_z_scores(numeric_state)
        analysis = await orchestrator.run_analysis(state, anomalies)
        analysis.data_source = data_source
        return analysis
    except HTTPException:
        raise
    except Exception:
        logger.exception("Analysis failed for scenario %s", request.scenario_id)
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Check the server logs for the underlying error.",
        )



@app.get("/api/marine/conditions")
async def marine_conditions(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Fetch live wave-forecast context; this is not a maritime safety clearance."""
    try:
        return await get_marine_conditions(latitude, longitude)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except MarineProviderError as exc:
        logger.warning("Marine forecast unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/api/query")
async def query_orca(request: QueryRequest):
    """Route a natural-language question to relevant ORCA capabilities.

    Keyword planning is deterministic and auditable. Ecosystem analysis still uses
    the selected demo/database scenario until live ecological providers are wired in.
    """
    try:
        plan = plan_query(request.query)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    response: Dict[str, Any] = {
        "query": request.query,
        "plan": plan.to_dict(),
        "analysis": None,
        "marine_conditions": None,
        "notice": None,
    }

    if plan.intent == "unsupported_query":
        response["notice"] = (
            "I could not route this question to an implemented ORCA capability. "
            "No agents were run and no scenario analysis was generated. Try a question "
            "about ocean conditions, water quality, fisheries/PFZ, biodiversity, climate, "
            "pollution, or a wave forecast."
        )
        return response

    if plan.intent == "marine_conditions":
        if request.latitude is None or request.longitude is None:
            response["notice"] = "Provide both latitude and longitude to retrieve a live wave forecast."
            return response
        try:
            response["marine_conditions"] = await get_marine_conditions(
                request.latitude, request.longitude
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except MarineProviderError as exc:
            logger.warning("Marine forecast unavailable: %s", exc)
            raise HTTPException(status_code=503, detail=str(exc))
        response["notice"] = (
            "Wave forecast context only; this is not an official maritime warning "
            "or a vessel-specific safety clearance."
        )
        return response

    scenarios = load_scenarios()
    scenario = scenarios.get(request.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Unknown scenario_id.")

    try:
        if DATA_MODE == "demo":
            state = scenario_state_from_json(scenario)
            data_source = "demo scenario JSON (simulated/reference data)"
        elif DATA_MODE == "database":
            state = scenario_state_from_database(request.scenario_id)
            data_source = "PostgreSQL"
        else:
            raise HTTPException(
                status_code=500,
                detail="ORCA_DATA_MODE must be either 'demo' or 'database'.",
            )

        numeric_state = {
            key: value
            for key, value in state.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        anomalies = detector.calculate_z_scores(numeric_state)
        analysis = await orchestrator.run_analysis(
            state, anomalies, selected_agent_names=plan.selected_agents
        )
        analysis.data_source = data_source
        response["analysis"] = analysis.model_dump(mode="json")
        response["notice"] = (
            "PFZ discovery is not live or validated yet; any analysis returned here "
            "is a scenario-based prototype assessment."
            if plan.intent == "potential_fishing_zone"
            else "Scenario-based prototype analysis; do not treat scores as validated scientific predictions."
        )
        return response
    except HTTPException:
        raise
    except Exception:
        logger.exception("Natural-language query analysis failed")
        raise HTTPException(
            status_code=500,
            detail="Query analysis failed. Check the server logs for the underlying error.",
        )
