import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from backend.models.ecosystem import EcosystemState, RiskAnalysis, Anomaly
from backend.ml.anomaly import AnomalyDetector
from backend.agents.orchestrator import OrcaOrchestrator
from backend.database.db_manager import db

app = FastAPI(title="ORCA Backend")

app = FastAPI(title="ORCA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
detector = AnomalyDetector()
orchestrator = OrcaOrchestrator()

# Mock Baselines (In production, these come from DB)
BASELINES = {
    "temperature": {"mean": 26.0, "std": 0.8},
    "salinity": {"mean": 35.0, "std": 0.2},
    "dissolved_oxygen": {"mean": 6.0, "std": 0.5},
    "ph": {"mean": 8.1, "std": 0.1},
    "chlorophyll": {"mean": 0.4, "std": 0.1},
    "turbidity": {"mean": 1.0, "std": 0.3},
    "pollution": {"mean": 0.05, "std": 0.05},
    "biodiversity": {"mean": 0.8, "std": 0.1},
    "fisheries": {"mean": 0.8, "std": 0.1},
    "current": {"mean": 0.5, "std": 0.2},
}

class AnalysisRequest(BaseModel):
    scenario_id: str = "normal_ocean"

@app.get("/api/health")
async def health():
    return {"status": "healthy", "system": "ORCA Ecosystem Intelligence"}

@app.post("/api/analyze", response_model=RiskAnalysis)
async def analyze_ecosystem(request: AnalysisRequest):
    # 1. Load scenario data from DB
    try:
        query = """
            SELECT l.latitude, l.longitude, l.depth, o.*
            FROM locations l
            JOIN ecosystem_observations o ON l.id = o.location_id
            WHERE l.name = %s
            ORDER BY o.timestamp DESC LIMIT 1
        """
        scenario_map = {
            "normal_ocean": "Normal Ocean State",
            "marine_heatwave": "Marine Heatwave",
            "pollution_event": "Pollution Event",
            "combined_crisis": "Combined Ecosystem Crisis"
        }
        name = scenario_map.get(request.scenario_id, request.scenario_id)

        result = db.fetch_one(query, (name,))
        if not result:
            raise HTTPException(status_code=404, detail="Scenario not found in database")

        state_dict = {
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "depth": result["depth"],
            "temperature": result["temperature"],
            "salinity": result["salinity"],
            "dissolved_oxygen": result["dissolved_oxygen"],
            "ph": result["ph"],
            "chlorophyll": result["chlorophyll"],
            "turbidity": result["turbidity"],
            "pollution": result["pollution"],
            "biodiversity": result["biodiversity"],
            "fisheries": result["fisheries"],
            "current": result["current"],
            "timestamp": result["timestamp"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 2. Run Anomaly Detection
    numeric_state = {k: v for k, v in state_dict.items() if isinstance(v, (int, float))}
    anomalies = detector.calculate_z_scores(numeric_state)

    # 3. Orchestrate Agent Analysis
    result = await orchestrator.run_analysis(state_dict, anomalies)

    return result

@app.get("/api/scenarios")
async def get_scenarios():
    with open("data/demo/scenarios.json", "r") as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
