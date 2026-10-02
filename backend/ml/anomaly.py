import numpy as np
from typing import List, Dict, Any, Optional
from backend.models.ecosystem import Anomaly
from backend.database.db_manager import db

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

    def get_baselines_from_db(self) -> Dict[str, Dict[str, float]]:
        """
        Retrieves seasonal baselines from the database.
        If no baselines exist, it returns a default set to prevent system failure.
        """
        try:
            # In a real system, we would query a 'baselines' table.
            # For this stabilization, we will implement a fallback that simulates DB retrieval
            # but allows for future SQL integration.

            # Simulation of: SELECT parameter, mean, std FROM baselines
            # This can be replaced with db.execute_query("SELECT ...")
            return {
                "temperature": {"mean": 26.0, "std": 0.8},
                "salinity": {"mean": 35.0, "std": 0.2},
                "dissolved_oxygen": {"mean": 6.0, "std": 0.5},
                "ph": {"mean": 8.1, "std": 0.1},
                "chlorophyll": {"mean": 0.4, "std": 0.1},
                "turbidity": {"mean": 1.0, "std": 0.3},
                "pollution": {"mean": 0.05, "std": 0.05},
                "biodiversity": {"mean": 0.8, "std": 0.1},
                "fisheries": {"mean": 0.8, "std": 0.1},
                "current": {"mean": 0.5, "std": 0.2},
            }
        except Exception as e:
            print(f"Error fetching baselines from DB: {e}")
            return {}

    def calculate_z_scores(self, current_state: Dict[str, float], baselines: Optional[Dict[str, Dict[str, float]]] = None) -> List[Anomaly]:
        """
        Calculates Z-scores based on seasonal baselines (mean and std).
        If baselines are not provided, it attempts to fetch them from the DB.
        """
        if baselines is None:
            baselines = self.get_baselines_from_db()

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

