"""Unit tests for OpenClaw Router."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from services.openclaw_orchestrator.src.core.router import Router
from services.openclaw_orchestrator.src.models.skill import Skill
from services.openclaw_orchestrator.src.models.request import OrchestrationRequest
from services.openclaw_orchestrator.src.models.response import Status


class TestRouter:
    """Test Router class."""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock skill registry."""
        registry = Mock()
        registry.get_skill = Mock()
        return registry

    @pytest.fixture
    def mock_gpu_scheduler(self):
        """Create a mock GPU scheduler."""
        scheduler = Mock()
        scheduler.allocate_gpu = AsyncMock(return_value=None)
        scheduler.release_gpu = AsyncMock()
        return scheduler

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis_mock = Mock()
        return redis_mock

    @pytest.fixture
    def sample_skill(self):
        """Create a sample skill."""
        return Skill(
            name="test-skill",
            version="1.0.0",
            endpoint="http://localhost:8001",
            timeout=5000,
        )

    @pytest.fixture
    def router(self, mock_registry, mock_gpu_scheduler, mock_redis):
        """Create a router instance."""
        return Router(
            registry=mock_registry,
            gpu_scheduler=mock_gpu_scheduler,
            redis_client=mock_redis,
        )

    def test_router_init(self, router, mock_registry, mock_gpu_scheduler, mock_redis):
        """Test router initialization."""
        assert router.registry is mock_registry
        assert router.gpu_scheduler is mock_gpu_scheduler
        assert router.redis is mock_redis
        assert router.session is None

    @pytest.mark.asyncio
    async def test_router_async_context_manager(self, mock_registry, mock_gpu_scheduler, mock_redis):
        """Test router async context manager."""
        async with Router(mock_registry, mock_gpu_scheduler, mock_redis) as router:
            assert router.session is not None

        # Session should be closed after exiting context
        # Note: We can't directly test if session is closed without more complex mocking

    @pytest.mark.asyncio
    async def test_orchestrate_single_skill_success(
        self, router, mock_registry, mock_gpu_scheduler, sample_skill
    ):
        """Test successful orchestration of a single skill."""
        mock_registry.get_skill.return_value = sample_skill

        request = OrchestrationRequest(
            skills=["test-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
        )

        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})

        mock_session_post = AsyncMock()
        mock_session_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session_post.__aexit__ = AsyncMock()

        router.session = Mock()
        router.session.post = Mock(return_value=mock_session_post)

        response = await router.orchestrate(request)

        assert response.status == Status.SUCCESS
        assert response.results == {"test-skill": {"result": "success"}}
        assert response.execution_time_ms > 0
        assert response.gpu_used is False
        assert response.errors is None

    @pytest.mark.asyncio
    async def test_orchestrate_with_gpu_allocation(
        self, router, mock_registry, mock_gpu_scheduler, sample_skill
    ):
        """Test orchestration with GPU allocation."""
        mock_registry.get_skill.return_value = sample_skill
        mock_gpu_scheduler.allocate_gpu.return_value = 0  # GPU ID 0

        request = OrchestrationRequest(
            skills=["test-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
            gpu_required=True,
        )

        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})

        mock_session_post = AsyncMock()
        mock_session_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session_post.__aexit__ = AsyncMock()

        router.session = Mock()
        router.session.post = Mock(return_value=mock_session_post)

        response = await router.orchestrate(request)

        assert response.status == Status.SUCCESS
        assert response.gpu_used is True
        mock_gpu_scheduler.allocate_gpu.assert_called_once_with(
            service="orchestrate",
            memory_mb=4000,
            timeout=30,
        )
        mock_gpu_scheduler.release_gpu.assert_called_once_with("orchestrate")

    @pytest.mark.asyncio
    async def test_orchestrate_skill_not_found(self, router, mock_registry, mock_gpu_scheduler):
        """Test orchestration when a skill is not found."""
        mock_registry.get_skill.return_value = None

        request = OrchestrationRequest(
            skills=["nonexistent-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
        )

        response = await router.orchestrate(request)

        assert response.status == Status.ERROR
        assert response.results == {}
        assert response.errors == {"nonexistent-skill": "Skill not found"}

    @pytest.mark.asyncio
    async def test_orchestrate_multiple_skills_mixed_results(
        self, router, mock_registry, mock_gpu_scheduler, sample_skill
    ):
        """Test orchestration with multiple skills where some fail."""
        # Set up mock to return skill for first, None for second
        def get_skill_side_effect(name):
            if name == "test-skill":
                return sample_skill
            return None

        mock_registry.get_skill.side_effect = get_skill_side_effect

        request = OrchestrationRequest(
            skills=["test-skill", "nonexistent-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
        )

        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})

        mock_session_post = AsyncMock()
        mock_session_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session_post.__aexit__ = AsyncMock()

        router.session = Mock()
        router.session.post = Mock(return_value=mock_session_post)

        response = await router.orchestrate(request)

        assert response.status == Status.ERROR
        assert "test-skill" in response.results
        assert response.errors == {"nonexistent-skill": "Skill not found"}

    @pytest.mark.asyncio
    async def test_orchestrate_with_custom_request_id(
        self, router, mock_registry, sample_skill
    ):
        """Test orchestration with a custom request ID."""
        mock_registry.get_skill.return_value = sample_skill

        request = OrchestrationRequest(
            skills=["test-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
            request_id="custom-req-123",
        )

        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})

        mock_session_post = AsyncMock()
        mock_session_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session_post.__aexit__ = AsyncMock()

        router.session = Mock()
        router.session.post = Mock(return_value=mock_session_post)

        response = await router.orchestrate(request)

        assert response.request_id == "custom-req-123"

    @pytest.mark.asyncio
    async def test_orchestrate_generates_request_id(
        self, router, mock_registry, sample_skill
    ):
        """Test orchestration generates a UUID when no request ID provided."""
        mock_registry.get_skill.return_value = sample_skill

        request = OrchestrationRequest(
            skills=["test-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
        )

        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})

        mock_session_post = AsyncMock()
        mock_session_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session_post.__aexit__ = AsyncMock()

        router.session = Mock()
        router.session.post = Mock(return_value=mock_session_post)

        response = await router.orchestrate(request)

        assert response.request_id is not None
        assert len(response.request_id) > 0

    @pytest.mark.asyncio
    async def test_invoke_skill_success(self, router, sample_skill):
        """Test successful skill invocation."""
        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"output": "test result"})

        mock_session_post = AsyncMock()
        mock_session_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session_post.__aexit__ = AsyncMock()

        router.session = Mock()
        router.session.post = Mock(return_value=mock_session_post)

        response = await router._invoke_skill(
            skill=sample_skill,
            input_data={"prompt": "test"},
            timeout=5000,
        )

        assert response.skill == "test-skill"
        assert response.status == Status.SUCCESS
        assert response.output == {"output": "test result"}
        assert response.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_invoke_skill_timeout(self, router, sample_skill):
        """Test skill invocation timeout."""
        # Mock timeout exception
        async def mock_post_timeout(*args, **kwargs):
            raise asyncio.TimeoutError()

        router.session = Mock()
        router.session.post = mock_post_timeout

        request = OrchestrationRequest(
            skills=["test-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
        )

        response = await router.orchestrate(request)

        assert response.status == Status.ERROR
        assert response.errors == {"test-skill": "Timeout"}

    @pytest.mark.asyncio
    async def test_invoke_skill_http_error(self, router, sample_skill):
        """Test skill invocation with HTTP error."""
        # Mock HTTP error
        async def mock_post_error(*args, **kwargs):
            raise Exception("Connection refused")

        router.session = Mock()
        router.session.post = mock_post_error

        request = OrchestrationRequest(
            skills=["test-skill"],
            input_data={"prompt": "test input"},
            timeout=30,
        )

        response = await router.orchestrate(request)

        assert response.status == Status.ERROR
        assert "test-skill" in response.errors
        assert "Connection refused" in response.errors["test-skill"]

    @pytest.mark.asyncio
    async def test_orchestrate_empty_skills(self, router):
        """Test orchestration with empty skills list."""
        request = OrchestrationRequest(
            skills=[],
            input_data={},
            timeout=30,
        )

        response = await router.orchestrate(request)

        assert response.status == Status.SUCCESS
        assert response.results == {}
        assert response.errors is None
