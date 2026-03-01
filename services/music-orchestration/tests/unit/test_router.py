import pytest
from unittest.mock import Mock, AsyncMock

from music_orchestration.router import RequestRouter
from music_orchestration.schemas import MusicRequest, UseCase, UserContext, Role


@pytest.mark.asyncio
async def test_route_to_cache_hit():
    cache_mock = Mock()
    cache_mock.get = AsyncMock(return_value={"music_id": "cached-123"})

    router = RequestRouter(cache=cache_mock)
    request = MusicRequest(
        prompt="upbeat electronic",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )
    user = UserContext(
        service_name="test",
        role=Role.SOCIAL_MEDIA_USER,
        permissions=["music:generate"]
    )

    response = await router.route(request, user)

    assert response["was_cache_hit"] is True
    assert response["music_id"] == "cached-123"


@pytest.mark.asyncio
async def test_route_to_generation_on_cache_miss():
    cache_mock = Mock()
    cache_mock.get = AsyncMock(return_value=None)
    generation_mock = Mock()
    generation_mock.generate = AsyncMock(return_value={"music_id": "new-123"})

    router = RequestRouter(cache=cache_mock, generation_client=generation_mock)
    request = MusicRequest(
        prompt="new prompt",
        use_case=UseCase.MARKETING,
        duration_seconds=30
    )
    user = UserContext(
        service_name="test",
        role=Role.SOCIAL_MEDIA_USER,
        permissions=["music:generate"]
    )

    response = await router.route(request, user)

    assert response["was_cache_hit"] is False
    assert response["music_id"] == "new-123"
