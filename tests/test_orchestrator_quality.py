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
    assert "DATA QUALITY WARNING" in result.recommendation
