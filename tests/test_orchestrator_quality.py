import asyncio
from datetime import datetime, timezone

from backend.agents.orchestrator import OrcaOrchestrator


def test_incomplete_inputs_reduce_confidence_and_add_warning():
    result = asyncio.run(
        OrcaOrchestrator().run_analysis(
            {"latitude": 15.5, "longitude": 70.5, "timestamp": datetime.now(timezone.utc)},
            [],
        )
    )
    assert result.data_quality["completeness"] == 0.0
    assert result.confidence == 0.0
    assert result.uncertainty["data_gap"] == 1.0
    assert result.risk_level == "UNKNOWN"
    assert result.risk_score is None
    assert result.ecosystem_health is None
    assert result.agents == []
    assert "do not interpret this result as low risk" in result.recommendation.lower()


def test_agent_is_not_run_when_required_measurements_are_missing():
    result = asyncio.run(
        OrcaOrchestrator().run_analysis(
            {
                "pollution": 0.9,
                "timestamp": datetime.now(timezone.utc),
                "latitude": 15.5,
                "longitude": 70.5,
            },
            [],
            selected_agent_names=["Pollution Detection Agent"],
        )
    )
    assert result.risk_level == "UNKNOWN"
    assert result.risk_score is None
    assert result.agents == []
    assert result.data_quality["available_parameters"] == 1.0
    assert "required inputs" in result.explanation.lower()
