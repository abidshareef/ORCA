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
    assert "scenario-based prototype" in payload["notice"]


def test_pfz_query_discloses_missing_live_provider():
    response = client.post(
        "/api/query",
        json={"query": "Find a potential fishing zone today"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["plan"]["intent"] == "potential_fishing_zone"
    assert payload["analysis"] is not None
    assert "not implemented yet" in payload["notice"]


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
