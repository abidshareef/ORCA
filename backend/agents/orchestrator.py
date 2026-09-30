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
        # Risk Score R = Σ(w_i * c_i * y_i) / Σ(w_i * c_i)
        # For prototype, weights w_i are equal
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

        # 4. Interaction Reasoning (XAI)
        # Example: High Temp + Low DO -> Synergy
        interactions = []
        temp_val = state.get("temperature", 0)
        do_val = state.get("dissolved_oxygen", 100)
        
        if temp_val > 29 and do_val < 4.5:
            interactions.append({
                "pair": ["Temperature", "Dissolved Oxygen"],
                "effect": "Synergistic Stress",
                "description": "High temperature reduces oxygen solubility, compounding physiological stress on marine organisms."
            })

        # 5. Explanation Generation
        top_findings = sorted(findings, key=lambda x: x.prediction, reverse=True)
        explanation = f"The system detected a {risk_level} risk level (Score: {risk_score:.2f}). "
        if top_findings:
            explanation += f"The primary driver is {top_findings[0].finding} detected by the {top_findings[0].agent}."
        
        if interactions:
            explanation += " Synergistic effects between temperature and dissolved oxygen further elevate the risk."

        # 6. Recommendation
        recommendation = "Continue routine monitoring."
        if risk_level == "CRITICAL":
            recommendation = "IMMEDIATE ACTION REQUIRED: Deploy field teams for in-situ validation and notify environmental authorities."
        elif risk_level == "HIGH":
            recommendation = "PRIORITY INVESTIGATION: Increase sensor sampling frequency and check for local pollution sources."
        elif risk_level == "MODERATE":
            recommendation = "INCREASED VIGILANCE: Monitor trends over the next 72 hours for potential escalation."

        # 7. Ecosystem Health Index (EHI)
        # EHI = 1 - RiskScore (simplified)
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
