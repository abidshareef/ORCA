from typing import List, Dict, Any
from backend.models.ecosystem import AgentFinding

class BiodiversityAgent:
    def __init__(self):
        self.name = "Biodiversity Agent"

    async def analyze(self, state: Dict[str, Any], anomalies: List[Any]) -> AgentFinding:
        # Analyze: biodiversity, fisheries
        bio_params = ["biodiversity", "fisheries"]
        relevant_anomalies = [a for a in anomalies if a.parameter in bio_params]
        
        score = 0.0
        evidence = []
        reasoning = "Biodiversity indicators are stable."
        finding = "Stable biodiversity"
        
        # Use the state values directly for a basic heuristic
        # Normal bio is ~0.8, low is < 0.5
        bio_val = state.get("biodiversity", 0.8)
        fish_val = state.get("fisheries", 0.8)
        
        if bio_val < 0.6 or fish_val < 0.6:
            score = 1.0 - ((bio_val + fish_val) / 2)
            evidence = [f"Biodiversity index: {bio_val}", f"Fisheries index: {fish_val}"]
            reasoning = "Observed decline in biodiversity and fisheries suitability."
            
            if score > 0.4:
                finding = "Severe biodiversity stress"
            else:
                finding = "Moderate biodiversity decline"
        
        # Add anomaly context
        for a in relevant_anomalies:
            evidence.append(f"{a.parameter} anomaly: {a.severity}")

        return AgentFinding(
            agent=self.name,
            finding=finding,
            prediction=score,
            confidence=0.75, # Bio data often has more uncertainty
            evidence=evidence,
            reasoning=reasoning
        )
