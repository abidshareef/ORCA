from typing import List, Dict, Any
from backend.models.ecosystem import AgentFinding

class ClimateOceanAgent:
    def __init__(self):
        self.name = "Climate & Oceanographic Agent"

    async def analyze(self, state: Dict[str, Any], anomalies: List[Any]) -> AgentFinding:
        # Analyze: temperature, ph, current
        climate_params = ["temperature", "ph", "current"]
        relevant_anomalies = [a for a in anomalies if a.parameter in climate_params]
        
        temp_val = state.get("temperature", 26.0)
        ph_val = state.get("ph", 8.1)
        
        # Heuristic for Marine Heatwave (MHW)
        # Assume baseline 26.0, MHW > 28.5
        mhw_score = 0.0
        if temp_val > 28.5:
            mhw_score = (temp_val - 28.5) / 2.0 # Simple linear scale
        
        # Ocean Acidification (pH decline)
        acid_score = 0.0
        if ph_val < 8.0:
            acid_score = (8.0 - ph_val) / 0.5
            
        score = min(1.0, (mhw_score * 0.7) + (acid_score * 0.3))
        
        evidence = [f"Temp: {temp_val}C", f"pH: {ph_val}"]
        reasoning = "Climate indicators are stable."
        finding = "Normal climatic conditions"
        
        if score > 0.3:
            if mhw_score > 0.5:
                finding = "Potential Marine Heatwave"
                reasoning = "Sustained high temperatures indicate a heatwave event."
            elif acid_score > 0.5:
                finding = "Ocean Acidification Signal"
                reasoning = "pH levels are dropping, suggesting acidification."
            else:
                finding = "Climate variability detected"
                reasoning = "Moderate climate anomalies observed."

        for a in relevant_anomalies:
            evidence.append(f"{a.parameter} anomaly: {a.severity}")

        return AgentFinding(
            agent=self.name,
            finding=finding,
            prediction=score,
            confidence=0.8,
            evidence=evidence,
            reasoning=reasoning
        )
