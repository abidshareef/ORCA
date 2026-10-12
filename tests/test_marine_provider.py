import pytest

from backend.services.marine_provider import get_marine_conditions


@pytest.mark.asyncio
async def test_marine_provider_rejects_invalid_coordinates():
    with pytest.raises(ValueError):
        await get_marine_conditions(95, 0)
