# services/nemoclaw-orchestrator/tests/unit/test_agent_coordinator.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from agents.coordinator import AgentCoordinator, PolicyViolationError
from agents.adapters import (
    SceneSpeakAdapter,
    SentimentAdapter,
    CaptioningAdapter,
    BSLAdapter,
    LightingSoundMusicAdapter,
    SafetyFilterAdapter,
    MusicGenerationAdapter,
    AutonomousAdapter
)
from policy.engine import PolicyAction, PolicyRule
from llm.privacy_router import RouterConfig, PrivacyRouter


class TestPolicyViolationError:
    def test_policy_violation_error_creation(self):
        """Test PolicyViolationError can be created with message and code"""
        error = PolicyViolationError("Test violation", "TEST_CODE")
        assert error.message == "Test violation"
        assert error.code == "TEST_CODE"
        assert str(error) == "Test violation"

    def test_policy_violation_error_default_code(self):
        """Test PolicyViolationError default code"""
        error = PolicyViolationError("Test violation")
        assert error.code == "POLICY_VIOLATION"


class TestAgentCoordinator:
    @pytest.fixture
    def settings(self):
        """Create mock settings"""
        settings = Mock()
        settings.scenespeak_agent_url = "http://localhost:8001"
        settings.captioning_agent_url = "http://localhost:8002"
        settings.bsl_agent_url = "http://localhost:8003"
        settings.sentiment_agent_url = "http://localhost:8004"
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
    def mock_policy_engine(self):
        """Create mock policy engine"""
        engine = Mock()
        engine.check_input = Mock(return_value=Mock(
            action=PolicyAction.ALLOW,
            reason="No specific policy applies"
        ))
        engine.sanitize_input = AsyncMock(return_value={"text": "sanitized"})
        engine.filter_output = AsyncMock(return_value={"result": "filtered"})
        return engine

    @pytest.fixture
    def coordinator(self, settings, mock_policy_engine):
        """Create coordinator instance"""
        with patch('agents.coordinator.PrivacyRouter'):
            coord = AgentCoordinator(settings, mock_policy_engine)
            return coord

    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes with all adapters"""
        assert coordinator.adapters is not None
        assert len(coordinator.adapters) == 8
        assert "scenespeak" in coordinator.adapters
        assert "sentiment" in coordinator.adapters
        assert "captioning" in coordinator.adapters
        assert "bsl" in coordinator.adapters
        assert "lighting-sound-music" in coordinator.adapters
        assert "safety-filter" in coordinator.adapters
        assert "music-generation" in coordinator.adapters
        assert "autonomous" in coordinator.adapters

    def test_coordinator_policy_allow_flow(self, coordinator, mock_policy_engine):
        """Test policy ALLOW flow passes through"""
        mock_policy_engine.check_input.return_value = Mock(
            action=PolicyAction.ALLOW,
            reason="Safe input"
        )
        # Mock filter_output to return the same data (no filtering needed)
        mock_policy_engine.filter_output = AsyncMock(side_effect=lambda agent, response: response)

        # Mock the execute method properly for async
        original_execute = coordinator.adapters["sentiment"].execute
        coordinator.adapters["sentiment"].execute = AsyncMock(return_value={"sentiment": "positive"})

        result = coordinator.call_agent(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "happy message"}
        )

        assert result["sentiment"] == "positive"
        mock_policy_engine.check_input.assert_called_once()
        coordinator.adapters["sentiment"].execute.assert_called_once()

        # Restore original
        coordinator.adapters["sentiment"].execute = original_execute

    def test_coordinator_policy_deny_raises_error(self, coordinator, mock_policy_engine):
        """Test policy DENY raises PolicyViolationError"""
        mock_policy_engine.check_input.return_value = Mock(
            action=PolicyAction.DENY,
            reason="Dangerous command detected",
            rule_name="dangerous_commands"
        )

        with pytest.raises(PolicyViolationError) as exc_info:
            coordinator.call_agent(
                agent="autonomous",
                skill="execute",
                input_data={"command": "rm -rf /"}
            )

        assert "Dangerous command detected" in exc_info.value.message
        assert exc_info.value.code == "POLICY_DENY"

    def test_coordinator_policy_sanitize_flow(self, coordinator, mock_policy_engine):
        """Test policy SANITIZE flow sanitizes input"""
        mock_policy_engine.check_input.return_value = Mock(
            action=PolicyAction.SANITIZE,
            reason="Profanity detected",
            rule_name="profanity_filter"
        )
        mock_policy_engine.sanitize_input.return_value = {"text": "sanitized text"}

        # Mock the execute method properly for async
        original_execute = coordinator.adapters["scenespeak"].execute
        coordinator.adapters["scenespeak"].execute = AsyncMock(return_value={"response": "generated"})

        result = coordinator.call_agent(
            agent="scenespeak",
            skill="generate",
            input_data={"text": "bad words here"}
        )

        mock_policy_engine.sanitize_input.assert_called_once()
        coordinator.adapters["scenespeak"].execute.assert_called_once_with("generate", {"text": "sanitized text"})

        # Restore original
        coordinator.adapters["scenespeak"].execute = original_execute

    @pytest.mark.asyncio
    async def test_llm_agent_uses_privacy_router(self, coordinator):
        """Test LLM agents route through PrivacyRouter"""
        adapter = coordinator.adapters["scenespeak"]
        assert adapter.requires_llm is True
        assert isinstance(adapter, SceneSpeakAdapter)

    @pytest.mark.asyncio
    async def test_direct_http_agent_no_llm(self, coordinator):
        """Test direct HTTP agents don't use LLM"""
        adapter = coordinator.adapters["sentiment"]
        assert adapter.requires_llm is False
        assert isinstance(adapter, SentimentAdapter)

    def test_all_agent_types_correct(self, coordinator):
        """Test all 8 agents have correct types"""
        assert isinstance(coordinator.adapters["scenespeak"], SceneSpeakAdapter)
        assert isinstance(coordinator.adapters["sentiment"], SentimentAdapter)
        assert isinstance(coordinator.adapters["captioning"], CaptioningAdapter)
        assert isinstance(coordinator.adapters["bsl"], BSLAdapter)
        assert isinstance(coordinator.adapters["lighting-sound-music"], LightingSoundMusicAdapter)
        assert isinstance(coordinator.adapters["safety-filter"], SafetyFilterAdapter)
        assert isinstance(coordinator.adapters["music-generation"], MusicGenerationAdapter)
        assert isinstance(coordinator.adapters["autonomous"], AutonomousAdapter)

    def test_call_agent_with_invalid_agent(self, coordinator):
        """Test calling invalid agent raises error"""
        with pytest.raises(ValueError) as exc_info:
            coordinator.call_agent(
                agent="nonexistent",
                skill="test",
                input_data={}
            )
        assert "Unknown agent" in str(exc_info.value)


class TestAgentAdapters:
    """Test individual agent adapters"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for adapters"""
        settings = Mock()
        settings.scenespeak_agent_url = "http://localhost:8001"
        settings.sentiment_agent_url = "http://localhost:8004"
        settings.captioning_agent_url = "http://localhost:8002"
        settings.bsl_agent_url = "http://localhost:8003"
        settings.lighting_sound_music_url = "http://localhost:8005"
        settings.safety_filter_url = "http://localhost:8006"
        settings.music_generation_url = "http://localhost:8011"
        settings.autonomous_agent_url = "http://localhost:8008"
        return settings

    @pytest.mark.asyncio
    async def test_scenespeak_adapter_requires_llm(self, mock_settings):
        """Test SceneSpeakAdapter requires LLM"""
        with patch('agents.adapters.PrivacyRouter'):
            adapter = SceneSpeakAdapter(mock_settings.scenespeak_agent_url, Mock())
            assert adapter.requires_llm is True

    @pytest.mark.asyncio
    async def test_sentiment_adapter_direct_http(self, mock_settings):
        """Test SentimentAdapter uses direct HTTP"""
        adapter = SentimentAdapter(mock_settings.sentiment_agent_url)
        assert adapter.requires_llm is False

    @pytest.mark.asyncio
    async def test_captioning_adapter_direct_http(self, mock_settings):
        """Test CaptioningAdapter uses direct HTTP"""
        adapter = CaptioningAdapter(mock_settings.captioning_agent_url)
        assert adapter.requires_llm is False

    @pytest.mark.asyncio
    async def test_bsl_adapter_direct_http(self, mock_settings):
        """Test BSLAdapter uses direct HTTP"""
        adapter = BSLAdapter(mock_settings.bsl_agent_url)
        assert adapter.requires_llm is False

    @pytest.mark.asyncio
    async def test_lighting_sound_music_adapter_direct_http(self, mock_settings):
        """Test LightingSoundMusicAdapter uses direct HTTP"""
        adapter = LightingSoundMusicAdapter(mock_settings.lighting_sound_music_url)
        assert adapter.requires_llm is False

    @pytest.mark.asyncio
    async def test_safety_filter_adapter_direct_http(self, mock_settings):
        """Test SafetyFilterAdapter uses direct HTTP"""
        adapter = SafetyFilterAdapter(mock_settings.safety_filter_url)
        assert adapter.requires_llm is False

    @pytest.mark.asyncio
    async def test_music_generation_adapter_direct_http(self, mock_settings):
        """Test MusicGenerationAdapter uses direct HTTP"""
        adapter = MusicGenerationAdapter(mock_settings.music_generation_url)
        assert adapter.requires_llm is False

    @pytest.mark.asyncio
    async def test_autonomous_adapter_requires_llm(self, mock_settings):
        """Test AutonomousAdapter requires LLM"""
        with patch('agents.adapters.PrivacyRouter'):
            adapter = AutonomousAdapter(mock_settings.autonomous_agent_url, Mock())
            assert adapter.requires_llm is True
