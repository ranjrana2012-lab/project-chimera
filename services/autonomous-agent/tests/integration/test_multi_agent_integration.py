"""Integration tests for multi-agent orchestration with OpenClaw.

Tests the integration between autonomous-agent and OpenClaw orchestrator,
demonstrating VMAO-style multi-agent task execution.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Test both directions of integration
from gsd_orchestrator import GSDOrchestrator, Requirements, Plan, Task, Results, Result
from openclaw_client import OpenClawClient, AgentCallResult
from vmao_verifier import VMAOVerifier, VerificationStatus, QualityMetrics


@pytest.fixture
def temp_state_dir():
    """Create temporary state directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_openclaw_response():
    """Mock OpenClaw orchestrator response."""
    return {
        "result": {
            "dialogue": "Hello, this is a test dialogue.",
            "scene": "scene1",
            "characters": ["Alice", "Bob"]
        },
        "skill_used": "generate_dialogue",
        "execution_time": 1.5,
        "metadata": {}
    }


@pytest.mark.asyncio
class TestOpenClawClient:
    """Test OpenClaw client functionality."""

    async def test_get_available_skills(self, temp_state_dir):
        """Test discovering available skills from OpenClaw."""
        client = OpenClawClient()

        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "skills": [
                {
                    "name": "generate_dialogue",
                    "description": "Generate contextual dialogue",
                    "endpoint": "/v1/generate",
                    "method": "POST"
                },
                {
                    "name": "captioning",
                    "description": "Speech-to-text transcription",
                    "endpoint": "/v1/transcribe",
                    "method": "POST"
                }
            ],
            "total": 2,
            "enabled": 2
        }

        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            skills = await client.get_available_skills()

            assert len(skills) == 2
            assert skills[0].name == "generate_dialogue"
            assert skills[1].name == "captioning"
            mock_get.assert_called_once()

    async def test_call_agent(self, mock_openclaw_response):
        """Test calling another agent through OpenClaw."""
        client = OpenClawClient()

        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = mock_openclaw_response
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await client.call_agent(
                skill="generate_dialogue",
                input_data={
                    "scene": "test_scene",
                    "context": "test context"
                }
            )

            assert result.success is True
            assert result.skill_used == "generate_dialogue"
            assert "dialogue" in result.result
            mock_post.assert_called_once()

    async def test_call_agent_parallel(self):
        """Test parallel agent calls for dependency-aware execution."""
        client = OpenClawClient()

        # Mock responses for parallel calls
        async def mock_post(*args, **kwargs):
            mock_response = Mock()
            skill = kwargs.get("json", {}).get("skill", "unknown")

            if skill == "generate_dialogue":
                mock_response.json.return_value = {
                    "result": {"dialogue": "Test dialogue"},
                    "skill_used": skill,
                    "execution_time": 1.0
                }
            elif skill == "captioning":
                mock_response.json.return_value = {
                    "result": {"transcript": "Test transcript"},
                    "skill_used": skill,
                    "execution_time": 1.5
                }
            else:
                mock_response.json.return_value = {
                    "result": {},
                    "skill_used": skill,
                    "execution_time": 0.5
                }

            mock_response.raise_for_status = Mock()
            return mock_response

        with patch("httpx.AsyncClient.post", side_effect=mock_post):
            results = await client.call_agent_parallel([
                ("generate_dialogue", {"scene": "test"}),
                ("captioning", {"audio": "test.mp3"})
            ])

            assert len(results) == 2
            assert all(isinstance(r, AgentCallResult) for r in results)
            assert results[0].skill_used == "generate_dialogue"
            assert results[1].skill_used == "captioning"

    async def test_check_health(self):
        """Test OpenClaw health check."""
        client = OpenClawClient()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            is_healthy = await client.check_health()
            assert is_healthy is True


@pytest.mark.asyncio
class TestVMAOVerifier:
    """Test VMAO verifier functionality."""

    async def test_verify_plan_success(self, temp_state_dir):
        """Test plan verification with good plan."""
        verifier = VMAOVerifier()

        requirements = Requirements(
            goal="Create a REST API",
            constraints=["Use Python", "Follow PEP8"],
            acceptance_criteria=["API responds to GET requests"]
        )

        plan = Plan(
            tasks=[
                Task(
                    id="1",
                    description="Implement REST API with Python",
                    dependencies=[]
                ),
                Task(
                    id="2",
                    description="Add PEP8 linting",
                    dependencies=["1"]
                )
            ]
        )

        result = await verifier.verify_plan(plan, requirements)

        assert result.status in [VerificationStatus.PASSED, VerificationStatus.NEEDS_REPLAN]
        assert result.confidence >= 0.6
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)

    async def test_verify_plan_failure(self, temp_state_dir):
        """Test plan verification with poor plan."""
        verifier = VMAOVerifier()

        requirements = Requirements(
            goal="Create a REST API",
            constraints=["Use Python"],
            acceptance_criteria=["API responds"]
        )

        # Empty plan should fail
        plan = Plan(tasks=[])

        result = await verifier.verify_plan(plan, requirements)

        assert result.status == VerificationStatus.FAILED
        assert result.confidence == 0.0
        assert len(result.issues) > 0

    async def test_verify_execution_result_success(self, temp_state_dir):
        """Test execution result verification with good result."""
        verifier = VMAOVerifier()

        requirements = Requirements(
            goal="Generate dialogue",
            constraints=["Max 100 words"],
            acceptance_criteria=["Dialogue makes sense"]
        )

        plan = Plan(
            tasks=[
                Task(id="1", description="Generate dialogue")
            ]
        )

        result = Result(
            task_id="1",
            success=True,
            output="This is a test dialogue that meets all requirements.",
            duration_seconds=1.0
        )

        verification = await verifier.verify_execution_result(result, requirements, plan)

        assert verification.status == VerificationStatus.PASSED
        assert verification.confidence > 0.7

    async def test_verify_execution_result_failure(self, temp_state_dir):
        """Test execution result verification with failed result."""
        verifier = VMAOVerifier()

        requirements = Requirements(goal="Generate dialogue")

        plan = Plan(tasks=[Task(id="1", description="Generate dialogue")])

        result = Result(
            task_id="1",
            success=False,
            error="Generation failed",
            duration_seconds=0.5
        )

        verification = await verifier.verify_execution_result(result, requirements, plan)

        assert verification.status == VerificationStatus.FAILED
        assert verification.confidence == 0.0
        assert len(verification.issues) > 0

    async def test_should_replan(self, temp_state_dir):
        """Test replanning decision logic."""
        verifier = VMAOVerifier()

        # Create verification result that needs replan
        from vmao_verifier import VerificationResult

        needs_replan_result = VerificationResult(
            status=VerificationStatus.NEEDS_REPLAN,
            confidence=0.6,
            issues=["Minor issues"],
            suggestions=["Fix these"],
            metrics={}
        )

        should_replan = await verifier.should_replan(needs_replan_result)
        assert should_replan is True

        # Passed result should not trigger replan
        passed_result = VerificationResult(
            status=VerificationStatus.PASSED,
            confidence=0.9,
            issues=[],
            suggestions=[],
            metrics={}
        )

        should_replan = await verifier.should_replan(passed_result)
        assert should_replan is False


@pytest.mark.asyncio
class TestGSDOrchestratorWithVerification:
    """Test GSD orchestrator with VMAO verification."""

    async def test_verify_phase(self, temp_state_dir):
        """Test the verify phase of GSD orchestrator."""
        orchestrator = GSDOrchestrator()

        requirements = Requirements(
            goal="Execute multi-agent task",
            constraints=["Use available agents"],
            acceptance_criteria=["All tasks complete"]
        )

        plan = Plan(
            tasks=[
                Task(id="1", description="Call dialogue agent"),
                Task(id="2", description="Call captioning agent")
            ]
        )

        results = Results(
            results=[
                Result(
                    task_id="1",
                    success=True,
                    output="Dialogue generated",
                    duration_seconds=1.0
                ),
                Result(
                    task_id="2",
                    success=True,
                    output="Caption created",
                    duration_seconds=1.5
                )
            ],
            total_tasks=2,
            successful_tasks=2,
            failed_tasks=0
        )

        verification_report = await orchestrator.verify_phase(results, requirements, plan)

        assert "total_tasks" in verification_report
        assert verification_report["total_tasks"] == 2
        assert verification_report["successful_tasks"] == 2
        assert "overall_status" in verification_report
        assert isinstance(verification_report["task_verifications"], list)

    async def test_execute_with_verification(self, temp_state_dir):
        """Test full execute-with-verification cycle."""
        orchestrator = GSDOrchestrator()

        requirements = Requirements(
            goal="Execute multi-agent task",
            constraints=["Use available agents"]
        )

        plan = Plan(
            tasks=[
                Task(id="1", description="Test task")
            ]
        )

        results, verification = await orchestrator.execute_with_verification(plan, requirements)

        assert isinstance(results, Results)
        assert isinstance(verification, dict)
        assert "overall_status" in verification


@pytest.mark.asyncio
class TestEndToEndMultiAgentFlow:
    """Test end-to-end multi-agent workflow."""

    async def test_autonomous_agent_calls_openclaw(self, temp_state_dir):
        """Test autonomous agent calling other agents via OpenClaw."""
        # Setup
        orchestrator = GSDOrchestrator()
        openclaw_client = OpenClawClient()
        verifier = VMAOVerifier()

        # Phase 1: Discuss
        user_request = "Generate dialogue and create captions for a scene"
        requirements = orchestrator.discuss_phase(user_request)

        assert requirements.goal == user_request

        # Phase 2: Plan
        plan = orchestrator.plan_phase(requirements)

        assert len(plan.tasks) > 0

        # Phase 3: Verify plan
        plan_verification = await verifier.verify_plan(plan, requirements)

        assert plan_verification.status in [VerificationStatus.PASSED, VerificationStatus.NEEDS_REPLAN]

        # Mock OpenClaw calls
        async def mock_post(*args, **kwargs):
            mock_response = Mock()
            mock_response.json.return_value = {
                "result": {"output": "Mocked result"},
                "skill_used": "test_skill",
                "execution_time": 1.0
            }
            mock_response.raise_for_status = Mock()
            return mock_response

        with patch("httpx.AsyncClient.post", side_effect=mock_post):
            # Simulate calling agents through OpenClaw
            agent_calls = [
                ("generate_dialogue", {"scene": "test"}),
                ("captioning", {"audio": "test.mp3"})
            ]

            agent_results = await openclaw_client.call_agent_parallel(agent_calls)

            assert len(agent_results) == 2
            assert all(isinstance(r, AgentCallResult) for r in agent_results)

        # Phase 4: Execute with verification
        results, verification = await orchestrator.execute_with_verification(plan, requirements)

        assert results.total_tasks == len(plan.tasks)
        assert "overall_status" in verification

    async def test_vmao_plan_execute_verify_replan_cycle(self, temp_state_dir):
        """Test full VMAO Plan-Execute-Verify-Replan cycle."""
        orchestrator = GSDOrchestrator()
        verifier = VMAOVerifier()

        # Initial request
        user_request = "Create a multi-agent show experience"
        requirements = Requirements(
            goal=user_request,
            constraints=["Use dialogue and captioning"],
            acceptance_criteria=["Both agents succeed"]
        )

        # Plan
        plan = Plan(
            tasks=[
                Task(id="1", description="Call dialogue agent"),
                Task(id="2", description="Call captioning agent")
            ]
        )

        # Verify plan
        plan_verification = await verifier.verify_plan(plan, requirements)

        # If plan needs improvement, show suggestions
        if await verifier.should_replan(plan_verification):
            suggestions = await verifier.generate_replan_suggestions(plan_verification)
            assert isinstance(suggestions, list)

        # Execute
        results = Results(
            results=[
                Result(
                    task_id="1",
                    success=True,
                    output="Dialogue complete",
                    duration_seconds=1.0
                ),
                Result(
                    task_id="2",
                    success=False,
                    error="Captioning failed",
                    duration_seconds=0.5
                )
            ],
            total_tasks=2,
            successful_tasks=1,
            failed_tasks=1
        )

        # Verify execution
        execution_verification = await orchestrator.verify_phase(results, requirements, plan)

        # Check if replanning is needed
        assert execution_verification["overall_status"] in ["passed", "needs_replan", "failed"]

        if execution_verification["overall_status"] == "needs_replan":
            assert len(execution_verification["suggestions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
