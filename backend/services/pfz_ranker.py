"""Transparent experimental ranking of supplied marine candidate observations.

This is a prototype decision-support heuristic, not an operational PFZ forecast.
It never fetches or invents observations; callers must provide values and provenance.
"""
from datetime import datetime, timezone
from math import isfinite, log10
from typing import Any


FRESHNESS_HOURS = 168


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def rank_candidates(candidates: list[dict[str, Any]], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    ranked = []
    excluded = []

    for candidate in candidates:
        name = candidate["id"]
        observed_at = candidate["observed_at"]
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age_hours = (now - observed_at.astimezone(timezone.utc)).total_seconds() / 3600
        if age_hours < -1:
            excluded.append({"id": name, "reason": "Observation timestamp is in the future."})
            continue
        if age_hours > FRESHNESS_HOURS:
            excluded.append({"id": name, "reason": "Observation is older than the 7-day prototype freshness window."})
            continue

        chlorophyll = float(candidate["chlorophyll_mg_m3"])
        temperature = float(candidate["sea_surface_temperature_c"])
        oxygen = float(candidate["dissolved_oxygen_mg_l"])
        values = (chlorophyll, temperature, oxygen)
        if not all(isfinite(value) for value in values) or chlorophyll <= 0 or oxygen < 0:
            excluded.append({"id": name, "reason": "Observation values are invalid."})
            continue

        # Broad heuristic bands are intentionally visible and must be scientifically calibrated
        # before any operational fisheries use.
        chlorophyll_score = _clamp(1.0 - abs(log10(chlorophyll / 0.5)) / 1.5)
        temperature_score = _clamp(1.0 - max(0.0, 24.0 - temperature, temperature - 29.0) / 8.0)
        oxygen_score = _clamp(oxygen / 6.0)
        score = 0.4 * chlorophyll_score + 0.3 * temperature_score + 0.3 * oxygen_score
        ranked.append({
            "id": name,
            "latitude": candidate["latitude"],
            "longitude": candidate["longitude"],
            "score": round(score, 4),
            "components": {
                "chlorophyll_suitability": round(chlorophyll_score, 4),
                "temperature_suitability": round(temperature_score, 4),
                "oxygen_suitability": round(oxygen_score, 4),
            },
            "observed_at": observed_at.astimezone(timezone.utc).isoformat(),
            "age_hours": round(max(0.0, age_hours), 2),
            "source": candidate["source"],
            "source_url": candidate.get("source_url"),
        })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return {
        "ranking_method": "transparent_weighted_heuristic_v1",
        "ranked_candidates": ranked,
        "excluded_candidates": excluded,
        "limitations": [
            "Experimental ranking only; not a validated Potential Fishing Zone forecast.",
            "Inputs are supplied by the caller and are not fetched or independently verified by ORCA.",
            "Weights and broad suitability bands are illustrative and require regional scientific calibration and independent validation.",
            "No catch, species, weather, maritime safety, or legal fishing recommendation is implied.",
        ],
    }
