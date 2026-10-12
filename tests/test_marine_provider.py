import asyncio
from datetime import datetime, timedelta, timezone

import pytest

import backend.services.marine_provider as provider


class FakeResponse:
    def __init__(self, payload, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


class FakeClient:
    response = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        return self.response


def fake_payload(wave_height=1.7, wave_period=7.5, wave_direction=210):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return {
        "hourly": {
            "time": [(now + timedelta(hours=1)).isoformat()],
            "wave_height": [wave_height],
            "wave_period": [wave_period],
            "wave_direction": [wave_direction],
        }
    }


def install_response(monkeypatch, payload):
    FakeClient.response = FakeResponse(payload)
    monkeypatch.setattr(provider.httpx, "AsyncClient", FakeClient)


def test_marine_provider_rejects_invalid_coordinates():
    with pytest.raises(ValueError):
        asyncio.run(provider.get_marine_conditions(95, 0))


def test_marine_provider_normalizes_hourly_response(monkeypatch):
    install_response(monkeypatch, fake_payload())
    result = asyncio.run(provider.get_marine_conditions(15.5, 70.5))
    assert result["wave_height_m"] == 1.7
    assert result["wave_period_s"] == 7.5
    assert result["display_band"] == "caution"
    assert result["source"] == "Open-Meteo Marine API"
    assert result["source_url"] == provider.MARINE_API_URL
    assert result["fetched_at_utc"]
    assert result["missing_optional_fields"] == []
    assert "not an official maritime warning" in result["limitations"][0].lower()


def test_marine_provider_handles_missing_optional_values(monkeypatch):
    install_response(monkeypatch, fake_payload(wave_period=None, wave_direction="bad"))
    result = asyncio.run(provider.get_marine_conditions(15.5, 70.5))
    assert result["wave_height_m"] == 1.7
    assert result["wave_period_s"] is None
    assert result["wave_direction_deg"] is None
    assert set(result["missing_optional_fields"]) == {"wave_period_s", "wave_direction_deg"}


@pytest.mark.parametrize("payload", [None, [], {}, {"hourly": {"time": []}}])
def test_marine_provider_rejects_malformed_payloads(monkeypatch, payload):
    install_response(monkeypatch, payload)
    with pytest.raises(provider.MarineProviderError):
        asyncio.run(provider.get_marine_conditions(15.5, 70.5))


@pytest.mark.parametrize("wave_height", [-1, None, "not-a-number"])
def test_marine_provider_rejects_invalid_wave_height(monkeypatch, wave_height):
    install_response(monkeypatch, fake_payload(wave_height=wave_height))
    with pytest.raises(provider.MarineProviderError):
        asyncio.run(provider.get_marine_conditions(15.5, 70.5))


def test_marine_provider_rejects_stale_timestamps(monkeypatch):
    stale = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    install_response(monkeypatch, {"hourly": {"time": [stale], "wave_height": [1.0]}})
    with pytest.raises(provider.MarineProviderError, match="timestamp close enough"):
        asyncio.run(provider.get_marine_conditions(15.5, 70.5))
