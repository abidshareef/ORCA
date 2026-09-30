from typing import List, Dict, Any
from backend.models.ecosystem import AgentFinding

class OceanMonitoringAgent:
    def __init__(self):
        self.name = "Ocean Monitoring Agent"

    async def analyze(self, state: Dict[str, Any], anomalies: List[Any]) -> AgentFinding:
        # Analyze physical parameters: temp, salinity, DO, ph, turbidity
        physical_params = ["temperature", "salinity", "dissolved_oxygen", "ph", "turbidity"]
        relevant_anomalies = [a for a in anomalies if a.parameter in physical_params]
        
        score = 0.0
        evidence = []
        reasoning = "Physical parameters are within normal ranges."
        finding = "Stable physical conditions"
        
        if relevant_anomalies:
            # Simplified logic: high Z-score sum leads to higher prediction
            z_sum = sum(abs(a.z_score) for a in relevant_anomalies)
            score = min(1.0, z_sum / 10.0)
            
            findings_list = [f"{a.parameter}: {a.severity} (Z={a.z_score:.2f})" for a in relevant_anomalies]
            evidence = findings_list
            reasoning = f"Detected anomalies in: {', '.join([a.parameter for a in relevant_anomalies])}."
            
            if score > 0.7:
                finding = "Critical physical anomaly"
            elif score > 0.3:
                finding = "Moderate physical instability"
            else:
                finding = "Minor physical fluctuations"

        return AgentFinding(
            agent=self.name,
            finding=finding,
            prediction=score,
            confidence=0.9, # High confidence in sensor data
            evidence=evidence,
            reasoning=reasoning
        )
