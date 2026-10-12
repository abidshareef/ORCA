import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import backend.services.marine_provider as provider


def test_marine_provider_rejects_invalid_coordinates():
    with pytest.raises(ValueError):
        asyncio.run(provider.get_marine_conditions(95, 0))


def test_marine_provider_normalizes_hourly_response(monkeypatch):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    next_hour = (now + timedelta(hours=1)).isoformat()
    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {"hourly": {"time": [next_hour], "wave_height": [1.7], "wave_period": [7.5], "wave_direction": [210]}}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(provider.httpx, "AsyncClient", FakeClient)
    result = asyncio.run(provider.get_marine_conditions(15.5, 70.5))
    assert result["wave_height_m"] == 1.7
    assert result["wave_period_s"] == 7.5
    assert result["display_band"] == "caution"
    assert result["source"] == "Open-Meteo Marine API"
    assert "not an official maritime warning" in result["limitations"][0].lower()
