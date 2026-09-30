from typing import List, Dict, Any
from backend.models.ecosystem import AgentFinding

class FisheriesAgent:
    def __init__(self):
        self.name = "Fisheries Agent"

    async def analyze(self, state: Dict[str, Any], anomalies: List[Any]) -> AgentFinding:
        # Analyze: fisheries index, temperature, dissolved_oxygen
        # Habitat Suitability Index (HSI) simplified
        # HSI = w1*FishIndex + w2*TempScore + w3*DOScore
        
        fish_idx = state.get("fisheries", 0.8)
        temp = state.get("temperature", 26.0)
        do = state.get("dissolved_oxygen", 6.0)
        
        # Temp score: Ideal ~25-27, penalty if > 29 or < 22
        temp_score = 1.0 if 24 <= temp <= 28 else (1.0 - abs(temp - 26)/10)
        
        # DO score: Ideal > 5.0, penalty if < 4.0
        do_score = 1.0 if do > 5.0 else (do / 5.0)
        
        hsi = (fish_idx * 0.5) + (temp_score * 0.25) + (do_score * 0.25)
        
        # Prediction is 1 - HSI (higher risk/suitability loss)
        score = 1.0 - max(0, min(1.0, hsi))
        
        evidence = [f"Fisheries Index: {fish_idx}", f"Temp: {temp}C", f"DO: {do}mg/L"]
        reasoning = "Habitat suitability is high for target species."
        finding = "Optimal fisheries habitat"
        
        if score > 0.3:
            reasoning = "Environmental conditions are degrading habitat suitability."
            if score > 0.6:
                finding = "Critical habitat loss"
            else:
                finding = "Sub-optimal habitat"

        return AgentFinding(
            agent=self.name,
            finding=finding,
            prediction=score,
            confidence=0.7,
            evidence=evidence,
            reasoning=reasoning
        )
