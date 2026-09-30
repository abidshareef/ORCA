from typing import List, Dict, Any
from backend.models.ecosystem import AgentFinding

class PollutionDetectionAgent:
    def __init__(self):
        self.name = "Pollution Detection Agent"

    async def analyze(self, state: Dict[str, Any], anomalies: List[Any]) -> AgentFinding:
        # Analyze: pollution, turbidity
        poll_params = ["pollution", "turbidity"]
        relevant_anomalies = [a for a in anomalies if a.parameter in poll_params]
        
        pollution_val = state.get("pollution", 0.0)
        turbidity_val = state.get("turbidity", 1.0)
        
        # Basic PRS = w1*P + w2*T
        # Normal turbidity is ~1.0, pollution ~0.0
        prs = (pollution_val * 0.7) + (max(0, (turbidity_val - 1.0) / 5.0) * 0.3)
        
        score = min(1.0, prs)
        evidence = [f"Pollution level: {pollution_val}", f"Turbidity: {turbidity_val}"]
        reasoning = "Pollution levels are within acceptable limits."
        finding = "Clean water conditions"
        
        if score > 0.3:
            reasoning = "Elevated pollution and turbidity indicators detected."
            if score > 0.7:
                finding = "Severe pollution event"
            else:
                finding = "Moderate pollution risk"
        
        for a in relevant_anomalies:
            evidence.append(f"{a.parameter} anomaly: {a.severity}")

        return AgentFinding(
            agent=self.name,
            finding=finding,
            prediction=score,
            confidence=0.85,
            evidence=evidence,
            reasoning=reasoning
        )
