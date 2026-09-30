import numpy as np
from typing import List, Dict, Any
from backend.models.ecosystem import Anomaly

class AnomalyDetector:
    def __init__(self, thresholds: Dict[str, float] = None):
        # Default Z-score thresholds
        self.thresholds = thresholds or {
            "temperature": 2.0,
            "salinity": 2.0,
            "dissolved_oxygen": 2.0,
            "ph": 2.0,
            "chlorophyll": 2.0,
            "turbidity": 2.0,
            "pollution": 2.0,
            "biodiversity": 2.0,
            "fisheries": 2.0,
            "current": 2.0
        }

    def calculate_z_scores(self, current_state: Dict[str, float], baselines: Dict[str, Dict[str, float]]) -> List[Anomaly]:
        """
        Calculates Z-scores based on seasonal baselines (mean and std).
        baselines format: {"temperature": {"mean": 26.0, "std": 0.5}, ...}
        """
        anomalies = []
        for param, value in current_state.items():
            if param in baselines:
                mean = baselines[param]["mean"]
                std = baselines[param]["std"]
                
                # Avoid division by zero
                if std == 0:
                    z_score = 0 if value == mean else 10.0
                else:
                    z_score = (value - mean) / std
                
                severity = "NORMAL"
                abs_z = abs(z_score)
                if abs_z > self.thresholds.get(param, 2.0):
                    severity = "ANOMALY"
                elif abs_z > self.thresholds.get(param, 2.0) * 0.5:
                    severity = "WATCH"
                
                anomalies.append(Anomaly(
                    parameter=param,
                    value=value,
                    z_score=z_score,
                    severity=severity
                ))
        
        return anomalies

    def calculate_composite_score(self, anomalies: List[Anomaly]) -> float:
        """
        EAS = Σ w_i |Z_i| / Σ w_i
        For prototype, we use equal weights.
        """
        if not anomalies:
            return 0.0
        
        total_abs_z = sum(abs(a.z_score) for a in anomalies)
        return total_abs_z / len(anomalies)

