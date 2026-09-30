from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float
    depth: float

class EcosystemState(BaseModel):
    location: Location
    timestamp: datetime
    temperature: float
    salinity: float
    dissolved_oxygen: float
    ph: float
    chlorophyll: float
    turbidity: float
    pollution: float
    biodiversity: float
    fisheries: float
    current: float

class AgentFinding(BaseModel):
    agent: str
    finding: str
    prediction: float
    confidence: float
    evidence: List[str]
    reasoning: str

class RiskAnalysis(BaseModel):
    location: Location
    timestamp: datetime
    risk_score: float
    risk_level: str # LOW, MODERATE, HIGH, CRITICAL
    confidence: float
    ecosystem_health: float
    anomalies: List[Dict]
    contributors: List[Dict]
    agents: List[AgentFinding]
    evidence: List[Dict]
    interactions: List[Dict]
    explanation: str
    recommendation: str
    uncertainty: Dict
    data_quality: Dict

class Anomaly(BaseModel):
    parameter: str
    value: float
    z_score: float
    severity: str # NORMAL, WATCH, ANOMALY
