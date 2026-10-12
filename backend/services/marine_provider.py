"""Validated Open-Meteo Marine API adapter.

This adapter provides wave-forecast context only. It is not a source of ecological
observations, cyclone warnings, or official go/no-go maritime advice.
"""
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Dict

import httpx

MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
OPTIONAL_FIELDS = ("wave_period_s", "wave_direction_deg")


class MarineProviderError(RuntimeError):
    """Raised when upstream forecast data cannot be used safely."""


def _number_at(values: Any, index: int) -> float | None:
    if not isinstance(values, list) or index < 0 or index >= len(values):
        return None
    value = values[index]
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


async def get_marine_conditions(latitude: float, longitude: float) -> Dict[str, Any]:
    """Return a validated forecast hour close to now with provenance attached."""
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("latitude or longitude is outside its valid range")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "wave_height,wave_direction,wave_period",
        "forecast_days": 2,
        "timezone": "UTC",
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0)) as client:
            response = await client.get(MARINE_API_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise MarineProviderError("Marine forecast provider is temporarily unavailable") from exc

    if not isinstance(payload, dict):
        raise MarineProviderError("Marine forecast provider returned an invalid response")
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise MarineProviderError("Marine forecast provider returned no hourly forecast")

    times = hourly.get("time")
    if not isinstance(times, list) or not times:
        raise MarineProviderError("Marine forecast provider returned no hourly timestamps")

    now = datetime.now(timezone.utc)
    parsed_times = []
    for index, raw in enumerate(times):
        try:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            parsed_times.append((abs((parsed - now).total_seconds()), index, parsed))
        except (TypeError, ValueError):
            continue
    if not parsed_times:
        raise MarineProviderError("Marine forecast timestamps could not be parsed")

    distance_seconds, index, valid_time = min(parsed_times, key=lambda item: item[0])
    if distance_seconds > 3 * 60 * 60:
        raise MarineProviderError("Marine forecast has no timestamp close enough to the current time")

    wave_height = _number_at(hourly.get("wave_height"), index)
    wave_period = _number_at(hourly.get("wave_period"), index)
    wave_direction = _number_at(hourly.get("wave_direction"), index)
    if wave_height is None or wave_height < 0:
        raise MarineProviderError("Marine forecast did not include a valid wave-height value")
    if wave_period is not None and wave_period < 0:
        wave_period = None
    if wave_direction is not None and not 0 <= wave_direction <= 360:
        wave_direction = None

    if wave_height >= 2.5:
        band = "elevated_waves"
    elif wave_height >= 1.5:
        band = "caution"
    else:
        band = "no_high_wave_flag_from_this_threshold_only"

    optional_values = {
        "wave_period_s": wave_period,
        "wave_direction_deg": wave_direction,
    }
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "forecast_time_utc": valid_time.astimezone(timezone.utc).isoformat(),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "wave_height_m": wave_height,
        **optional_values,
        "missing_optional_fields": [key for key, value in optional_values.items() if value is None],
        "display_band": band,
        "source": "Open-Meteo Marine API",
        "source_url": MARINE_API_URL,
        "data_type": "forecast",
        "limitations": [
            "Not an official maritime warning or a vessel-specific safety clearance.",
            "Wind, currents, tides, visibility, vessel type, and local authority warnings are not assessed by this endpoint.",
            "Display bands are simple thresholds, not a validated maritime risk model.",
        ],
    }
