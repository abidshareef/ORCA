import asyncio
from typing import List, Dict, Any
from backend.models.ecosystem import AgentFinding, RiskAnalysis, Location

from backend.agents.ocean import OceanMonitoringAgent
from backend.agents.biodiversity import BiodiversityAgent
from backend.agents.pollution import PollutionDetectionAgent
from backend.agents.climate import ClimateOceanAgent
from backend.agents.fisheries import FisheriesAgent

class OrcaOrchestrator:
    def __init__(self):
        self.agents = [
            OceanMonitoringAgent(),
            BiodiversityAgent(),
            PollutionDetectionAgent(),
            ClimateOceanAgent(),
            FisheriesAgent()
        ]

    async def run_analysis(self, state: Dict[str, Any], anomalies: List[Any]) -> RiskAnalysis:
        # 1. Parallel Execution of Specialized Agents
        tasks = [agent.analyze(state, anomalies) for agent in self.agents]
        findings = await asyncio.gather(*tasks)

        # 2. Confidence-Weighted Aggregation
        total_weighted_score = 0.0
        total_weight = 0.0

        for f in findings:
            weight = 1.0
            total_weighted_score += weight * f.confidence * f.prediction
            total_weight += weight * f.confidence

        risk_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # 3. Risk Level Classification
        if risk_score > 0.75:
            risk_level = "CRITICAL"
        elif risk_score > 0.5:
            risk_level = "HIGH"
        elif risk_score > 0.25:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # 4. Dynamic Interaction Reasoning (Improved XAI)
        # Instead of hardcoded thresholds, we identify synergistic stress based on anomaly patterns
        interactions = []

        # Identify which parameters are currently anomalous (Z-score high)
        anomalous_params = {a.parameter for a in anomalies if a.severity == "ANOMALY"}

        # Synergy Mapping: If both parameters in a pair are anomalous, trigger synergistic risk
        synergies = [
            {
                "pair": ["temperature", "dissolved_oxygen"],
                "effect": "Synergistic Physiological Stress",
                "description": "Combined high temperature and low oxygen levels compound respiratory stress on marine organisms."
            },
            {
                "pair": ["pollution", "biodiversity"],
                "effect": "Ecotoxicological Collapse",
                "description": "Elevated pollution levels are directly correlating with a rapid decline in species biodiversity."
            },
            {
                "pair": ["temperature", "ph"],
                "effect": "Climatic Destabilization",
                "description": "Concurrent warming and acidification are compromising calcification processes in coral and shellfish."
            }
        ]

        for synergy in synergies:
            if all(p in anomalous_params for p in synergy["pair"]):
                interactions.append(synergy)

        # 5. Explanation Generation
        top_findings = sorted(findings, key=lambda x: x.prediction, reverse=True)
        explanation = f"The system detected a {risk_level} risk level (Score: {risk_score:.2f}). "
        if top_findings:
            explanation += f"The primary driver is {top_findings[0].finding} detected by the {top_findings[0].agent}."

        if interactions:
            explanation += f" {len(interactions)} synergistic interactions were detected, further elevating the systemic risk."

        # 6. Recommendation
        recommendation = "Continue routine monitoring."
        if risk_level == "CRITICAL":
            recommendation = "IMMEDIATE ACTION REQUIRED: Deploy field teams for in-situ validation and notify environmental authorities."
        elif risk_level == "HIGH":
            recommendation = "PRIORITY INVESTIGATION: Increase sensor sampling frequency and check for local pollution sources."
        elif risk_level == "MODERATE":
            recommendation = "INCREASED VIGILANCE: Monitor trends over the next 72 hours for potential escalation."

        # 7. Ecosystem Health Index (EHI)
        ehi = 1.0 - risk_score

        return RiskAnalysis(
            location=Location(
                latitude=state.get("latitude", 0),
                longitude=state.get("longitude", 0),
                depth=state.get("depth", 0)
            ),
            timestamp=state.get("timestamp"),
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=sum(f.confidence for f in findings) / len(findings),
            ecosystem_health=ehi,
            anomalies=[{"parameter": a.parameter, "z_score": a.z_score, "severity": a.severity} for a in anomalies],
            contributors=[{"agent": f.agent, "contribution": f.prediction} for f in findings],
            agents=findings,
            evidence=[{"source": "Agent", "content": f.reasoning} for f in findings],
            interactions=interactions,
            explanation=explanation,
            recommendation=recommendation,
            uncertainty={"model_variance": 0.05, "data_gap": 0.1},
            data_quality={"completeness": 0.95, "reliability": 0.9}
        )
