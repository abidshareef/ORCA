from backend.services.query_planner import plan_query


def test_pollution_query_routes_to_pollution_agent():
    plan = plan_query("Is there a pollution event near the coast?")
    assert plan.intent == "ecosystem_assessment"
    assert "Pollution Detection Agent" in plan.selected_agents


def test_fishing_query_exposes_missing_live_pfz_capability():
    plan = plan_query("Find a potential fishing zone today")
    assert plan.intent == "potential_fishing_zone"
    assert "Fisheries Agent" in plan.selected_agents
    assert any("not implemented" in item for item in plan.limitations)


def test_wave_query_requires_location_and_discloses_safety_limitations():
    plan = plan_query("Are the waves safe for a small boat today?")
    assert plan.intent == "marine_conditions"
    assert plan.needs_location is True
    assert any("not official" in item for item in plan.limitations)


def test_empty_query_is_rejected():
    try:
        plan_query("   ")
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("empty query should fail")



def test_marine_conditions_plan_does_not_select_ecosystem_agents():
    plan = plan_query("Show the wave forecast")
    assert plan.intent == "marine_conditions"
    assert plan.selected_agents == []
    assert "Open-Meteo Marine API" in plan.required_data_sources[0]
