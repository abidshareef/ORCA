import { BaseModel } from 'pydantic';
from typing import List, Dict, Any, Optional
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float
    depth: float

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
    anomalies: List[Dict[str, Any]]
    contributors: List[Dict[str, Any]]
    agents: List[AgentFinding]
    evidence: List[Dict[str, Any]]
    interactions: List[Dict[str, Any]]
    explanation: str
    recommendation: str
    uncertainty: Dict[str, float]
    data_quality: Dict[str, float]

class Anomaly(BaseModel):
    parameter: str
    value: float
    z_score: float
    severity: str # NORMAL, WATCH, ANOMALY
