from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Location(BaseModel):
    latitude: float
    longitude: float
    depth: float = 0.0


class AgentFinding(BaseModel):
    agent: str
    finding: str
    prediction: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    reasoning: str


class RiskAnalysis(BaseModel):
    location: Location
    timestamp: datetime
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    confidence: float = Field(ge=0.0, le=1.0)
    ecosystem_health: float = Field(ge=0.0, le=1.0)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    contributors: List[Dict[str, Any]] = Field(default_factory=list)
    agents: List[AgentFinding] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str
    recommendation: str
    uncertainty: Dict[str, float] = Field(default_factory=dict)
    data_quality: Dict[str, float] = Field(default_factory=dict)
    data_source: str = "demo scenario JSON"


class Anomaly(BaseModel):
    parameter: str
    value: float
    z_score: float
    severity: str
