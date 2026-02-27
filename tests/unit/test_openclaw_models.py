"""Unit tests for OpenClaw Orchestrator data models."""
import pytest
from services.openclaw_orchestrator.src.models.skill import Skill, SkillHealth
from services.openclaw_orchestrator.src.models.request import OrchestrationRequest, SkillRequest
from services.openclaw_orchestrator.src.models.response import (
    OrchestrationResponse,
    SkillResponse,
    Status,
)


class TestSkill:
    """Test Skill model."""

    def test_skill_creation(self):
        """Test creating a basic skill."""
        skill = Skill(
            name="test-skill",
            version="1.0.0",
            endpoint="http://localhost:8001",
        )
        assert skill.name == "test-skill"
        assert skill.version == "1.0.0"
        assert skill.endpoint == "http://localhost:8001"
        assert skill.timeout == 5000
        assert skill.gpu_required is False
        assert skill.description is None
        assert skill.metadata == {}

    def test_skill_with_all_fields(self):
        """Test creating a skill with all fields."""
        skill = Skill(
            name="gpu-skill",
            version="2.0.0",
            endpoint="http://localhost:8002",
            timeout=10000,
            gpu_required=True,
            description="A GPU-intensive skill",
            metadata={"author": "test", "tags": ["gpu", "ml"]},
        )
        assert skill.name == "gpu-skill"
        assert skill.timeout == 10000
        assert skill.gpu_required is True
        assert skill.description == "A GPU-intensive skill"
        assert skill.metadata == {"author": "test", "tags": ["gpu", "ml"]}

    def test_skill_timeout_validation(self):
        """Test skill timeout validation."""
        # Test minimum boundary
        skill_min = Skill(
            name="test", version="1.0.0", endpoint="http://localhost", timeout=100
        )
        assert skill_min.timeout == 100

        # Test maximum boundary
        skill_max = Skill(
            name="test", version="1.0.0", endpoint="http://localhost", timeout=60000
        )
        assert skill_max.timeout == 60000

        # Test below minimum
        with pytest.raises(ValueError):
            Skill(name="test", version="1.0.0", endpoint="http://localhost", timeout=50)

        # Test above maximum
        with pytest.raises(ValueError):
            Skill(name="test", version="1.0.0", endpoint="http://localhost", timeout=70000)


class TestSkillHealth:
    """Test SkillHealth model."""

    def test_healthy_skill(self):
        """Test a healthy skill status."""
        health = SkillHealth(
            name="test-skill", healthy=True, last_check="2024-02-27T10:00:00Z"
        )
        assert health.name == "test-skill"
        assert health.healthy is True
        assert health.last_check == "2024-02-27T10:00:00Z"
        assert health.error_message is None

    def test_unhealthy_skill(self):
        """Test an unhealthy skill status."""
        health = SkillHealth(
            name="failing-skill",
            healthy=False,
            last_check="2024-02-27T10:00:00Z",
            error_message="Connection refused",
        )
        assert health.name == "failing-skill"
        assert health.healthy is False
        assert health.error_message == "Connection refused"


class TestOrchestrationRequest:
    """Test OrchestrationRequest model."""

    def test_valid_request(self):
        """Test creating a valid orchestration request."""
        request = OrchestrationRequest(
            skills=["scenespeak"], input_data={"context": "test"}
        )
        assert len(request.skills) == 1
        assert request.skills[0] == "scenespeak"
        assert request.input_data == {"context": "test"}
        assert request.priority == 100
        assert request.timeout == 30
        assert request.gpu_required is False
        assert request.request_id is None

    def test_request_with_all_fields(self):
        """Test request with all optional fields."""
        request = OrchestrationRequest(
            skills=["skill1", "skill2"],
            input_data={"key": "value"},
            priority=500,
            timeout=60,
            gpu_required=True,
            request_id="req-123",
        )
        assert len(request.skills) == 2
        assert request.priority == 500
        assert request.timeout == 60
        assert request.gpu_required is True
        assert request.request_id == "req-123"

    def test_priority_validation(self):
        """Test priority field validation."""
        # Test minimum boundary
        req_min = OrchestrationRequest(
            skills=["test"], input_data={}, priority=1
        )
        assert req_min.priority == 1

        # Test maximum boundary
        req_max = OrchestrationRequest(
            skills=["test"], input_data={}, priority=1000
        )
        assert req_max.priority == 1000

        # Test below minimum
        with pytest.raises(ValueError):
            OrchestrationRequest(skills=["test"], input_data={}, priority=0)

        # Test above maximum
        with pytest.raises(ValueError):
            OrchestrationRequest(skills=["test"], input_data={}, priority=2000)

    def test_timeout_validation(self):
        """Test timeout field validation."""
        # Test minimum boundary
        req_min = OrchestrationRequest(
            skills=["test"], input_data={}, timeout=1
        )
        assert req_min.timeout == 1

        # Test maximum boundary
        req_max = OrchestrationRequest(
            skills=["test"], input_data={}, timeout=300
        )
        assert req_max.timeout == 300

        # Test below minimum
        with pytest.raises(ValueError):
            OrchestrationRequest(skills=["test"], input_data={}, timeout=0)

        # Test above maximum
        with pytest.raises(ValueError):
            OrchestrationRequest(skills=["test"], input_data={}, timeout=500)


class TestSkillRequest:
    """Test SkillRequest model."""

    def test_skill_request_creation(self):
        """Test creating a skill request."""
        request = SkillRequest(
            skill="test-skill", input_data={"prompt": "Hello"}
        )
        assert request.skill == "test-skill"
        assert request.input_data == {"prompt": "Hello"}
        assert request.timeout == 5000

    def test_skill_request_custom_timeout(self):
        """Test skill request with custom timeout."""
        request = SkillRequest(
            skill="test-skill", input_data={}, timeout=10000
        )
        assert request.timeout == 10000


class TestStatus:
    """Test Status enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert Status.SUCCESS == "success"
        assert Status.ERROR == "error"
        assert Status.TIMEOUT == "timeout"


class TestOrchestrationResponse:
    """Test OrchestrationResponse model."""

    def test_successful_response(self):
        """Test creating a successful orchestration response."""
        response = OrchestrationResponse(
            request_id="req-123",
            status=Status.SUCCESS,
            results={"output": "test result"},
            execution_time_ms=150.5,
            gpu_used=False,
        )
        assert response.request_id == "req-123"
        assert response.status == Status.SUCCESS
        assert response.results == {"output": "test result"}
        assert response.execution_time_ms == 150.5
        assert response.gpu_used is False
        assert response.errors is None

    def test_error_response(self):
        """Test creating an error response."""
        response = OrchestrationResponse(
            request_id="req-456",
            status=Status.ERROR,
            results={},
            execution_time_ms=50.0,
            gpu_used=True,
            errors={"skill1": "Timeout exceeded"},
        )
        assert response.status == Status.ERROR
        assert response.errors == {"skill1": "Timeout exceeded"}
        assert response.gpu_used is True


class TestSkillResponse:
    """Test SkillResponse model."""

    def test_successful_skill_response(self):
        """Test creating a successful skill response."""
        response = SkillResponse(
            skill="test-skill",
            status=Status.SUCCESS,
            output={"result": "success"},
            execution_time_ms=100.0,
        )
        assert response.skill == "test-skill"
        assert response.status == Status.SUCCESS
        assert response.output == {"result": "success"}
        assert response.execution_time_ms == 100.0
        assert response.error is None

    def test_error_skill_response(self):
        """Test creating an error skill response."""
        response = SkillResponse(
            skill="failing-skill",
            status=Status.ERROR,
            output={},
            execution_time_ms=25.0,
            error="Division by zero",
        )
        assert response.skill == "failing-skill"
        assert response.status == Status.ERROR
        assert response.error == "Division by zero"

    def test_timeout_skill_response(self):
        """Test creating a timeout skill response."""
        response = SkillResponse(
            skill="slow-skill",
            status=Status.TIMEOUT,
            output={},
            execution_time_ms=5000.0,
            error="Request timed out after 5000ms",
        )
        assert response.status == Status.TIMEOUT
        assert response.execution_time_ms == 5000.0
