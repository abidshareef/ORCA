from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_is_live():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_works_in_demo_mode():
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_scenarios_are_loaded_from_json():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenario_ids = {item["id"] for item in response.json()["scenarios"]}
    assert scenario_ids == {
        "normal_ocean",
        "marine_heatwave",
        "pollution_event",
        "combined_crisis",
    }


def test_each_demo_scenario_runs_through_all_agents():
    for scenario_id in (
        "normal_ocean",
        "marine_heatwave",
        "pollution_event",
        "combined_crisis",
    ):
        response = client.post("/api/analyze", json={"scenario_id": scenario_id})
        assert response.status_code == 200, response.text
        payload = response.json()
        assert 0 <= payload["risk_score"] <= 1
        assert payload["risk_level"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
        assert len(payload["agents"]) == 5
        assert payload["data_source"].startswith("demo scenario JSON")


def test_unknown_scenario_returns_404():
    response = client.post("/api/analyze", json={"scenario_id": "does_not_exist"})
    assert response.status_code == 404


def test_natural_language_query_routes_to_relevant_agent():
    response = client.post(
        "/api/query",
        json={"query": "Check pollution levels", "scenario_id": "pollution_event"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan"]["intent"] == "ecosystem_assessment"
    assert payload["plan"]["selected_agents"] == ["Pollution Detection Agent"]
    assert len(payload["analysis"]["agents"]) == 1
    assert "prototype" in payload["notice"].lower()


def test_pfz_query_discloses_missing_live_provider():
    response = client.post(
        "/api/query",
        json={"query": "Find a potential fishing zone today"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan"]["intent"] == "potential_fishing_zone"
    assert payload["analysis"] is None
    assert payload["plan"]["selected_agents"] == ["Fisheries Agent", "Ocean Monitoring Agent"]
    assert "live pfz discovery is not available" in payload["notice"].lower()


def test_marine_conditions_query_requires_coordinates():
    response = client.post(
        "/api/query",
        json={"query": "Are the waves safe for a small boat today?"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan"]["intent"] == "marine_conditions"
    assert payload["marine_conditions"] is None
    assert "latitude and longitude" in payload["notice"]


def test_query_rejects_invalid_coordinates():
    response = client.post(
        "/api/query",
        json={"query": "Wave forecast", "latitude": 95, "longitude": 0},
    )
    assert response.status_code == 422


def test_analysis_reports_actual_data_completeness():
    response = client.post("/api/analyze", json={"scenario_id": "normal_ocean"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_quality"]["completeness"] == 1.0
    assert payload["uncertainty"]["data_gap"] == 0.0


def test_marine_conditions_endpoint_returns_controlled_503(monkeypatch):
    import backend.main as main

    async def unavailable(*args, **kwargs):
        raise main.MarineProviderError("Marine forecast provider is temporarily unavailable")

    monkeypatch.setattr(main, "get_marine_conditions", unavailable)
    response = client.get("/api/marine/conditions?latitude=15.5&longitude=70.5")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_marine_query_returns_live_source_metadata(monkeypatch):
    import backend.main as main

    async def fake_conditions(latitude, longitude):
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "forecast_time_utc": "2026-10-12T18:00:00+00:00",
            "fetched_at_utc": "2026-10-12T18:01:00+00:00",
            "wave_height_m": 1.2,
            "wave_period_s": None,
            "wave_direction_deg": 180.0,
            "missing_optional_fields": ["wave_period_s"],
            "display_band": "no_high_wave_flag_from_this_threshold_only",
            "source": "Open-Meteo Marine API",
            "source_url": "https://marine-api.open-meteo.com/v1/marine",
            "data_type": "forecast",
            "limitations": ["Not an official maritime warning."],
        }

    monkeypatch.setattr(main, "get_marine_conditions", fake_conditions)
    response = client.post(
        "/api/query",
        json={"query": "Show the wave forecast", "latitude": 15.5, "longitude": 70.5},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["marine_conditions"]["source"] == "Open-Meteo Marine API"
    assert payload["marine_conditions"]["missing_optional_fields"] == ["wave_period_s"]
    assert "not an official maritime warning" in payload["marine_conditions"]["limitations"][0].lower()


def test_unrecognized_query_returns_no_analysis():
    response = client.post(
        "/api/query",
        json={"query": "What is the capital of India?"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan"]["intent"] == "unsupported_query"
    assert payload["plan"]["selected_agents"] == []
    assert payload["analysis"] is None
    assert "no agents were run" in payload["notice"].lower()


def test_pfz_rank_endpoint_ranks_supplied_observations_and_preserves_provenance():
    from datetime import datetime, timezone

    response = client.post(
        "/api/pfz/rank",
        json={
            "candidates": [
                {
                    "id": "candidate-a",
                    "latitude": 15.5,
                    "longitude": 70.5,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "chlorophyll_mg_m3": 0.5,
                    "sea_surface_temperature_c": 27.0,
                    "dissolved_oxygen_mg_l": 6.0,
                    "source": "test observation source",
                    "source_url": "https://example.org/observations",
                },
                {
                    "id": "candidate-b",
                    "latitude": 16.0,
                    "longitude": 71.0,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "chlorophyll_mg_m3": 0.01,
                    "sea_surface_temperature_c": 20.0,
                    "dissolved_oxygen_mg_l": 2.0,
                    "source": "test observation source",
                },
            ]
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ranking_method"] == "transparent_weighted_heuristic_v1"
    assert payload["ranked_candidates"][0]["id"] == "candidate-a"
    assert payload["ranked_candidates"][0]["rank"] == 1
    assert payload["ranked_candidates"][0]["source_url"] == "https://example.org/observations"
    assert any("not a validated Potential Fishing Zone forecast" in item for item in payload["limitations"])


def test_pfz_rank_endpoint_rejects_missing_observation_fields():
    response = client.post(
        "/api/pfz/rank",
        json={"candidates": [{"id": "incomplete", "latitude": 15.5, "longitude": 70.5}]},
    )
    assert response.status_code == 422


def test_pfz_rank_endpoint_excludes_stale_observations():
    from datetime import datetime, timedelta, timezone

    response = client.post(
        "/api/pfz/rank",
        json={
            "candidates": [
                {
                    "id": "stale",
                    "latitude": 15.5,
                    "longitude": 70.5,
                    "observed_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                    "chlorophyll_mg_m3": 0.5,
                    "sea_surface_temperature_c": 27.0,
                    "dissolved_oxygen_mg_l": 6.0,
                    "source": "test observation source",
                }
            ]
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ranked_candidates"] == []
    assert payload["excluded_candidates"][0]["id"] == "stale"
