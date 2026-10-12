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
