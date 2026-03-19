# services/nemoclaw-orchestrator/tests/integration/test_show_lifecycle.py
"""Integration tests for complete show lifecycle.

Tests the complete show lifecycle from IDLE through PRELUDE, ACTIVE, POSTLUDE,
CLEANUP, and back to IDLE, integrating ShowStateMachine, RedisStateStore,
PolicyEngine, and AgentCoordinator.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from state.machine import ShowStateMachine, ShowState
from state.store import RedisStateStore
from policy.engine import PolicyEngine, PolicyRule, PolicyAction
from agents.coordinator import AgentCoordinator


@pytest.fixture
async def mock_redis():
    """Create mock Redis client for testing."""
    redis_mock = Mock()
    redis_mock.setex = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture
def state_store(mock_redis):
    """Create RedisStateStore with mock Redis."""
    return RedisStateStore(redis_client=mock_redis)


@pytest.fixture
def policy_engine():
    """Create PolicyEngine with test policies."""
    policies = [
        PolicyRule(
            name="sentiment-allow",
            agent="sentiment",
            action=PolicyAction.ALLOW,
            conditions={},
            output_filter=False
        ),
        PolicyRule(
            name="autonomous-block-dangerous",
            agent="autonomous",
            action=PolicyAction.DENY,
            conditions={"command_contains": ["rm -rf", "format", "delete"]},
            output_filter=True
        ),
    ]
    return PolicyEngine(policies)


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
async def agent_coordinator(mock_settings, policy_engine):
    """Create AgentCoordinator with mocked dependencies."""
    with patch('agents.coordinator.PrivacyRouter'):
        coordinator = AgentCoordinator(mock_settings, policy_engine)
        yield coordinator
        await coordinator.close()


class TestShowLifecycleIntegration:
    """Test complete show lifecycle with all components integrated."""

    @pytest.mark.asyncio
    async def test_complete_show_lifecycle(self, state_store):
        """Test complete show lifecycle: IDLE -> PRELUDE -> ACTIVE -> POSTLUDE -> CLEANUP -> IDLE."""
        show_id = "test-show-complete-lifecycle"

        # Create state machine with state store
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Initial state should be IDLE
        assert machine.current_state == ShowState.IDLE
        assert machine.is_ended()
        assert not machine.is_running()
        assert not machine.is_paused()

        # Start the show: IDLE -> PRELUDE
        machine.start()
        await asyncio.sleep(0.01)  # Allow async persist to complete
        assert machine.current_state == ShowState.PRELUDE
        assert machine.is_paused()
        assert not machine.is_running()
        assert not machine.is_ended()

        # Transition to ACTIVE: PRELUDE -> ACTIVE
        machine.transition_to(ShowState.ACTIVE)
        await asyncio.sleep(0.01)
        assert machine.current_state == ShowState.ACTIVE
        assert machine.is_running()
        assert not machine.is_paused()
        assert not machine.is_ended()

        # Transition to POSTLUDE: ACTIVE -> POSTLUDE
        machine.transition_to(ShowState.POSTLUDE)
        await asyncio.sleep(0.01)
        assert machine.current_state == ShowState.POSTLUDE
        assert machine.is_paused()
        assert not machine.is_running()
        assert not machine.is_ended()

        # Transition to CLEANUP: POSTLUDE -> CLEANUP
        machine.transition_to(ShowState.CLEANUP)
        await asyncio.sleep(0.01)
        assert not machine.is_running()
        assert not machine.is_paused()

        # Transition to IDLE: CLEANUP -> IDLE
        machine.transition_to(ShowState.IDLE)
        await asyncio.sleep(0.01)
        assert machine.current_state == ShowState.IDLE
        assert machine.is_ended()
        assert not machine.is_running()
        assert not machine.is_paused()

    @pytest.mark.asyncio
    async def test_show_lifecycle_with_persistence(self, state_store, mock_redis):
        """Test that state persists correctly throughout lifecycle."""
        show_id = "test-show-persistence"

        # Create and start show
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)
        machine.start()
        await asyncio.sleep(0.01)

        # Verify state was saved
        mock_redis.setex.assert_called()
        call_args = mock_redis.setex.call_args
        # call_args[0] contains positional args: (key, ttl, value)
        # We need to get the value which is the third argument (index 2)
        saved_data = call_args[0][2]  # The value argument (JSON string)
        import json
        state_data = json.loads(saved_data)
        assert state_data["state"] == "PRELUDE"
        assert state_data["show_id"] == show_id

    @pytest.mark.asyncio
    async def test_show_lifecycle_invalid_transition(self, state_store):
        """Test that invalid transitions are blocked."""
        show_id = "test-show-invalid-transition"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Try to skip from IDLE to ACTIVE (should fail)
        with pytest.raises(ValueError, match="Cannot transition from IDLE to ACTIVE"):
            machine.transition_to(ShowState.ACTIVE)

        # Verify state didn't change
        assert machine.current_state == ShowState.IDLE

    @pytest.mark.asyncio
    async def test_show_lifecycle_recovery_from_store(self, mock_redis):
        """Test recovering state machine from Redis store."""
        show_id = "test-show-recovery"

        # Simulate existing state in Redis (as JSON string)
        import json
        existing_state = {
            "show_id": show_id,
            "state": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(existing_state))

        # Create store and retrieve state
        store = RedisStateStore(redis_client=mock_redis)
        retrieved_state = await store.get_state(show_id)

        # Recreate machine from retrieved state
        machine = ShowStateMachine.from_dict(retrieved_state)
        assert machine.current_state == ShowState.ACTIVE
        assert machine.show_id == show_id

    @pytest.mark.asyncio
    async def test_show_lifecycle_with_agent_coordinator(self, state_store, agent_coordinator):
        """Test show lifecycle integrated with agent coordinator."""
        show_id = "test-show-with-coordinator"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Start show
        machine.start()
        await asyncio.sleep(0.01)
        assert machine.current_state == ShowState.PRELUDE

        # Move to ACTIVE and simulate agent call
        machine.transition_to(ShowState.ACTIVE)
        await asyncio.sleep(0.01)
        assert machine.is_running()

        # Verify agent coordinator is available
        assert "sentiment" in agent_coordinator.list_agents()
        assert "autonomous" in agent_coordinator.list_agents()

    @pytest.mark.asyncio
    async def test_show_lifecycle_end_from_multiple_states(self, state_store):
        """Test end() method works from different active states."""
        test_cases = [
            (ShowState.PRELUDE, "from PRELUDE"),
            (ShowState.ACTIVE, "from ACTIVE"),
            (ShowState.POSTLUDE, "from POSTLUDE"),
        ]

        for start_state, description in test_cases:
            show_id = f"test-show-end-{start_state.value}"
            machine = ShowStateMachine(show_id=show_id, state_store=state_store)

            # Navigate to test state
            if start_state == ShowState.PRELUDE:
                machine.start()
            elif start_state == ShowState.ACTIVE:
                machine.start()
                machine.transition_to(ShowState.ACTIVE)
            elif start_state == ShowState.POSTLUDE:
                machine.start()
                machine.transition_to(ShowState.ACTIVE)
                machine.transition_to(ShowState.POSTLUDE)

            await asyncio.sleep(0.01)

            # End the show
            machine.end()
            await asyncio.sleep(0.01)

            # Verify back to IDLE
            assert machine.current_state == ShowState.IDLE, f"Failed {description}"

    @pytest.mark.asyncio
    async def test_show_lifecycle_end_from_idle_raises_error(self, state_store):
        """Test that end() raises error when called from IDLE."""
        show_id = "test-show-end-from-idle"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Should not be able to end from IDLE
        with pytest.raises(ValueError, match="Cannot end show from IDLE"):
            machine.end()

    @pytest.mark.asyncio
    async def test_show_lifecycle_end_from_cleanup_raises_error(self, state_store):
        """Test that end() raises error when called from CLEANUP."""
        show_id = "test-show-end-from-cleanup"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Navigate to CLEANUP
        machine.start()
        machine.transition_to(ShowState.ACTIVE)
        machine.transition_to(ShowState.CLEANUP)
        await asyncio.sleep(0.01)

        # Should not be able to end from CLEANUP
        with pytest.raises(ValueError, match="Cannot end show from CLEANUP"):
            machine.end()

    @pytest.mark.asyncio
    async def test_show_lifecycle_serialization_roundtrip(self, state_store):
        """Test that state machine serializes and deserializes correctly."""
        show_id = "test-show-serialization"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Transition through several states
        machine.start()
        machine.transition_to(ShowState.ACTIVE)
        machine.transition_to(ShowState.POSTLUDE)

        # Serialize
        state_dict = machine.to_dict()
        assert state_dict["show_id"] == show_id
        assert state_dict["state"] == "POSTLUDE"
        assert "created_at" in state_dict
        assert "updated_at" in state_dict

        # Deserialize
        restored_machine = ShowStateMachine.from_dict(state_dict)
        assert restored_machine.show_id == show_id
        assert restored_machine.current_state == ShowState.POSTLUDE
        assert isinstance(restored_machine.created_at, datetime)
        assert isinstance(restored_machine.updated_at, datetime)


class TestShowLifecycleWithPolicy:
    """Test show lifecycle with policy enforcement."""

    @pytest.mark.asyncio
    async def test_policy_enforcement_during_active_show(self, state_store, policy_engine):
        """Test that policy is enforced during ACTIVE show state."""
        show_id = "test-show-policy-enforcement"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        # Start show and move to ACTIVE
        machine.start()
        machine.transition_to(ShowState.ACTIVE)
        await asyncio.sleep(0.01)

        # Test policy check for dangerous command
        result = policy_engine.check_input(
            agent="autonomous",
            skill="execute",
            input_data={"command": "rm -rf /"}
        )
        assert result.action == PolicyAction.DENY
        assert "dangerous" in result.reason.lower()

        # Test policy check for safe operation
        result = policy_engine.check_input(
            agent="sentiment",
            skill="analyze",
            input_data={"text": "happy message"}
        )
        assert result.action == PolicyAction.ALLOW

    @pytest.mark.asyncio
    async def test_show_state_dict_format(self, state_store):
        """Test that get_state() returns properly formatted dictionary."""
        show_id = "test-show-state-dict"
        machine = ShowStateMachine(show_id=show_id, state_store=state_store)

        machine.start()
        state_dict = machine.get_state()

        # Verify structure
        assert isinstance(state_dict, dict)
        assert "show_id" in state_dict
        assert "state" in state_dict
        assert "created_at" in state_dict
        assert "updated_at" in state_dict
        assert state_dict["show_id"] == show_id
        assert state_dict["state"] == "PRELUDE"
