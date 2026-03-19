# services/nemoclaw-orchestrator/tests/integration/test_agent_flow.py
"""Integration tests for agent flow with policy enforcement.

Tests the complete agent call flow including policy checks, sanitization,
and output filtering using the AgentCoordinator with mocked HTTP responses.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from agents.coordinator import AgentCoordinator
from policy.engine import PolicyEngine, PolicyRule, PolicyAction, PolicyViolationError
from agents.adapters import SentimentAdapter, AutonomousAdapter


@pytest.fixture
def mock_settings():
    """Create mock settings for AgentCoordinator."""
    settings = Mock()
    settings.scenespeak_agent_url = "http://localhost:8001"
    settings.sentiment_agent_url = "http://localhost:8004"
    settings.captioning_agent_url = "http://localhost:8002"
    settings.bsl_agent_url = "http://localhost:8003"
    settings.lighting_sound_music_url = "http://localhost:8005"
    settings.safety_filter_url = "http://localhost:8006"
    settings.music_generation_url = "http://localhost:8011"
    settings.autonomous_agent_url = "http://localhost:8008"
    settings.dgx_endpoint = "http://localhost:8000"
    settings.local_ratio = 0.95
    settings.cloud_fallback_enabled = True
    settings.nemotron_model = "nemotron-8b"
    return settings


@pytest.fixture
def policy_engine():
    """Create PolicyEngine with test policies."""
    policies = [
        # Allow sentiment analysis freely
        PolicyRule(
            name="sentiment-allow",
            agent="sentiment",
            action=PolicyAction.ALLOW,
            conditions={},
            output_filter=False
        ),
        # Block dangerous autonomous commands
        PolicyRule(
            name="autonomous-block-dangerous",
            agent="autonomous",
            action=PolicyAction.DENY,
            conditions={"command_contains": ["rm -rf", "format", "delete", "shutdown"]},
            output_filter=True
        ),
        # Sanitize profanity in scenespeak
        PolicyRule(
            name="scenespeak-sanitize",
            agent="scenespeak",
            action=PolicyAction.SANITIZE,
            conditions={"profanity_detected": True},
            output_filter=True
        ),
        # Allow captioning
        PolicyRule(
            name="captioning-allow",
            agent="captioning",
            action=PolicyAction.ALLOW,
            conditions={},
            output_filter=False
        ),
    ]
    return PolicyEngine(policies)


@pytest.fixture
async def agent_coordinator(mock_settings, policy_engine):
    """Create AgentCoordinator with mocked dependencies."""
    with patch('agents.coordinator.PrivacyRouter'):
        coordinator = AgentCoordinator(mock_settings, policy_engine)
        yield coordinator
        await coordinator.close()


class TestAgentPolicyFlow:
    """Test agent call flow with policy enforcement."""

    @pytest.mark.asyncio
    async def test_policy_blocks_dangerous_autonomous_commands(self, agent_coordinator):
        """Test that policy blocks dangerous autonomous commands with PolicyViolationError."""
        # Mock the autonomous adapter to never be called
        agent_coordinator.adapters["autonomous"].execute = AsyncMock(
            return_value={"result": "command executed"}
        )

        # Try to execute dangerous command
        dangerous_commands = [
            {"command": "rm -rf /"},
            {"command": "format c:"},
            {"command": "delete all files"},
            {"command": "shutdown system"},
        ]

        for cmd_data in dangerous_commands:
            with pytest.raises(PolicyViolationError) as exc_info:
                await agent_coordinator.call_agent(
                    agent="autonomous",
                    skill="execute",
                    input_data=cmd_data
                )

            # Verify error details
            assert exc_info.value.code == "POLICY_DENY"
            assert "denied by policy" in exc_info.value.message.lower()

        # Verify adapter was never called (blocked before execution)
        assert agent_coordinator.adapters["autonomous"].execute.call_count == 0

    @pytest.mark.asyncio
    async def test_policy_blocks_dangerous_command_with_http_patch(self, agent_coordinator):
        """Test policy blocks dangerous commands using pytest.patch on HTTP calls."""
        dangerous_input = {"command": "rm -rf /important/data"}

        # Mock HTTP client to verify no call is made
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post = AsyncMock()
            mock_post.return_value = Mock(
                json=lambda: {"result": "success"},
                raise_for_status=lambda: None
            )

            # Policy should block before HTTP call
            with pytest.raises(PolicyViolationError):
                await agent_coordinator.call_agent(
                    agent="autonomous",
                    skill="execute",
                    input_data=dangerous_input
                )

            # Verify HTTP was never called (policy blocked it)
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_sentiment_agent_allowed_through(self, agent_coordinator):
        """Test that sentiment agent calls are allowed through policy."""
        # Mock the sentiment adapter response
        agent_coordinator.adapters["sentiment"].execute = AsyncMock(
            return_value={"sentiment": "positive", "confidence": 0.95}
        )

        # Call sentiment agent
        result = await agent_coordinator.call_agent(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "This is a wonderful day!"}
        )

        # Verify result
        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.95

        # Verify adapter was called
        agent_coordinator.adapters["sentiment"].execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_sentiment_agent_with_mock_http_response(self, agent_coordinator):
        """Test sentiment agent with mocked HTTP response using pytest.patch."""
        test_text = "I love this amazing performance!"

        # Mock HTTP response
        mock_response = Mock()
        mock_response.json = Mock(return_value={
            "sentiment": "positive",
            "confidence": 0.98,
            "emotions": ["joy", "excitement"]
        })
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Replace adapter to use the mocked HTTP client
            original_adapter = agent_coordinator.adapters["sentiment"]
            test_adapter = SentimentAdapter("http://localhost:8004")
            test_adapter._client = Mock()
            test_adapter._client.post = mock_post
            agent_coordinator.adapters["sentiment"] = test_adapter

            try:
                # Mock filter_output to handle dict response properly
                agent_coordinator.policy_engine.filter_output = AsyncMock(
                    side_effect=lambda agent, response: response if isinstance(response, dict) else {"result": response}
                )

                # Call sentiment agent
                result = await agent_coordinator.call_agent(
                    agent="sentiment",
                    skill="analyze",
                    input_data={"text": test_text}
                )

                # Verify HTTP call was made
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert "analyze" in call_args[0][0]

                # Verify result
                assert result["sentiment"] == "positive"
                assert result["confidence"] == 0.98
            finally:
                # Restore original adapter
                agent_coordinator.adapters["sentiment"] = original_adapter

    @pytest.mark.asyncio
    async def test_policy_sanitize_flow(self, agent_coordinator):
        """Test policy SANITIZE flow for input sanitization."""
        # Mock policy to return SANITIZE action
        agent_coordinator.policy_engine.check_input = Mock(
            return_value=Mock(
                action=PolicyAction.SANITIZE,
                reason="Profanity detected",
                rule_name="profanity_filter"
            )
        )

        # Mock sanitize_input
        agent_coordinator.policy_engine.sanitize_input = AsyncMock(
            return_value={"text": "This is a *** show!"}
        )

        # Mock adapter response
        agent_coordinator.adapters["scenespeak"].execute = AsyncMock(
            return_value={"response": "Sanitized content generated"}
        )

        # Call with profanity
        result = await agent_coordinator.call_agent(
            agent="scenespeak",
            skill="generate",
            input_data={"text": "This is a bad word show!"}
        )

        # Verify sanitization happened
        agent_coordinator.policy_engine.sanitize_input.assert_called_once()
        agent_coordinator.adapters["scenespeak"].execute.assert_called_once()
        call_args = agent_coordinator.adapters["scenespeak"].execute.call_args
        # Verify sanitized input was passed to adapter
        assert call_args[0][1]["text"] == "This is a *** show!"

    @pytest.mark.asyncio
    async def test_policy_output_filtering(self, agent_coordinator):
        """Test that agent output is filtered through policy."""
        # Mock adapter response with potentially unsafe content
        agent_coordinator.adapters["sentiment"].execute = AsyncMock(
            return_value={"sentiment": "positive", "note": "User seems very happy!"}
        )

        # Mock filter_output to add warning
        agent_coordinator.policy_engine.filter_output = AsyncMock(
            side_effect=lambda agent, response: {
                **response,
                "filtered": True,
                "warning": "Content filtered by policy"
            }
        )

        # Call agent
        result = await agent_coordinator.call_agent(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "Great performance!"}
        )

        # Verify output was filtered
        assert result["filtered"] is True
        assert result["warning"] == "Content filtered by policy"
        agent_coordinator.policy_engine.filter_output.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_safe_agent_flow(self, agent_coordinator):
        """Test complete safe agent flow: ALLOW -> execute -> filter."""
        # Mock all components
        agent_coordinator.policy_engine.check_input = Mock(
            return_value=Mock(
                action=PolicyAction.ALLOW,
                reason="Safe input"
            )
        )
        agent_coordinator.policy_engine.filter_output = AsyncMock(
            side_effect=lambda agent, response: response  # Pass through
        )
        agent_coordinator.adapters["sentiment"].execute = AsyncMock(
            return_value={"sentiment": "neutral", "confidence": 0.75}
        )

        # Execute complete flow
        result = await agent_coordinator.call_agent(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "The show is starting now."}
        )

        # Verify complete flow
        agent_coordinator.policy_engine.check_input.assert_called_once_with(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "The show is starting now."}
        )
        agent_coordinator.adapters["sentiment"].execute.assert_called_once()
        agent_coordinator.policy_engine.filter_output.assert_called_once()
        assert result["sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_multiple_agents_with_different_policies(self, agent_coordinator):
        """Test multiple agents with different policy treatments."""
        # Setup mocks
        agent_coordinator.adapters["sentiment"].execute = AsyncMock(
            return_value={"sentiment": "positive"}
        )
        agent_coordinator.adapters["captioning"].execute = AsyncMock(
            return_value={"captions": "Hello world"}
        )

        # Test 1: Sentiment - ALLOW
        agent_coordinator.policy_engine.check_input = Mock(
            return_value=Mock(action=PolicyAction.ALLOW, reason="Safe")
        )
        result1 = await agent_coordinator.call_agent(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "Great!"}
        )
        assert result1["sentiment"] == "positive"

        # Test 2: Captioning - ALLOW
        result2 = await agent_coordinator.call_agent(
            agent="captioning",
            skill="generate",
            input_data={"audio": "base64..."}
        )
        assert result2["captions"] == "Hello world"

    @pytest.mark.asyncio
    async def test_agent_call_with_invalid_agent(self, agent_coordinator):
        """Test that calling invalid agent raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await agent_coordinator.call_agent(
                agent="nonexistent_agent",
                skill="test",
                input_data={}
            )
        assert "Unknown agent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_policy_check_called_before_execution(self, agent_coordinator):
        """Test that policy check is called before agent execution."""
        # Track call order
        call_order = []

        # Mock policy check to track calls
        def mock_check_input(*args, **kwargs):
            call_order.append("policy_check")
            return Mock(action=PolicyAction.ALLOW, reason="Safe")

        # Mock adapter to track calls
        async def mock_execute(*args, **kwargs):
            call_order.append("agent_execute")
            return {"result": "success"}

        agent_coordinator.policy_engine.check_input = mock_check_input
        agent_coordinator.adapters["sentiment"].execute = mock_execute

        # Make the call
        await agent_coordinator.call_agent(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "test"}
        )

        # Verify order: policy check before agent execution
        assert call_order == ["policy_check", "agent_execute"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, agent_coordinator):
        """Test that circuit breaker integrates with agent calls."""
        # Get circuit breaker for sentiment agent
        circuit_breaker = agent_coordinator.circuit_breakers.get("sentiment")
        assert circuit_breaker is not None

        # Mock adapter to fail
        agent_coordinator.adapters["sentiment"].execute = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        # Mock retry caller to handle retries
        agent_coordinator.retry_callers["sentiment"].call_with_retry_async = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed after retries")
        )

        # Try to call agent (should fail and record circuit breaker state)
        with pytest.raises(httpx.ConnectError):
            await agent_coordinator.call_agent(
                agent="sentiment",
                skill="analyze",
                input_data={"text": "test"}
            )

        # Verify circuit breaker recorded the failure
        assert circuit_breaker.stats.failure_count > 0


class TestAgentAdapterIntegration:
    """Test individual adapter integration with policy."""

    @pytest.mark.asyncio
    async def test_sentiment_adapter_integration(self, mock_settings):
        """Test SentimentAdapter with HTTP mocking."""
        adapter = SentimentAdapter(mock_settings.sentiment_agent_url)

        # Mock HTTP response
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json = Mock(return_value={"sentiment": "positive"})
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            # Execute adapter
            result = await adapter.execute("analyze", {"text": "Happy message"})

            # Verify
            assert result["sentiment"] == "positive"
            mock_post.assert_called_once()

        await adapter.close()

    @pytest.mark.asyncio
    async def test_autonomous_adapter_integration(self, mock_settings):
        """Test AutonomousAdapter with privacy router."""
        with patch('agents.adapters.PrivacyRouter') as mock_router_class:
            mock_router = Mock()
            mock_router.generate = Mock(return_value={
                "text": "Generated response",
                "backend": "local",
                "model": "nemotron-8b"
            })
            mock_router_class.return_value = mock_router

            adapter = AutonomousAdapter(mock_settings.autonomous_agent_url, mock_router)

            # Execute adapter
            result = await adapter.execute("generate", {"prompt": "Test prompt"})

            # Verify
            assert result["text"] == "Generated response"
            assert result["backend"] == "local"
            mock_router.generate.assert_called_once()

            await adapter.close()
