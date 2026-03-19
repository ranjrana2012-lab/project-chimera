# services/nemoclaw-orchestrator/tests/unit/test_state_machine.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from state.machine import ShowStateMachine, ShowState


class TestShowState:
    def test_state_values_are_strings(self):
        """ShowState enum values should be strings for JSON serialization"""
        assert ShowState.IDLE.value == "IDLE"
        assert ShowState.PRELUDE.value == "PRELUDE"
        assert ShowState.ACTIVE.value == "ACTIVE"
        assert ShowState.POSTLUDE.value == "POSTLUDE"
        assert ShowState.CLEANUP.value == "CLEANUP"


class TestShowStateMachine:
    def test_initial_state_is_idle(self):
        """StateMachine should start in IDLE state"""
        machine = ShowStateMachine(show_id="test-show-1")
        assert machine.current_state == ShowState.IDLE

    def test_machine_creates_timestamps(self):
        """StateMachine should create timestamps on initialization"""
        machine = ShowStateMachine(show_id="test-show-1")
        assert machine.created_at is not None
        assert machine.updated_at is not None
        assert isinstance(machine.created_at, datetime)
        assert isinstance(machine.updated_at, datetime)

    def test_start_transitions_to_prelude(self):
        """start() should transition from IDLE to PRELUDE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()
        assert machine.current_state == ShowState.PRELUDE

    def test_start_from_non_idle_raises_error(self):
        """start() should only work from IDLE state"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()  # Now in PRELUDE
        with pytest.raises(ValueError, match="Cannot start show from PRELUDE, must be IDLE"):
            machine.start()

    def test_end_transitions_to_cleanup_then_idle(self):
        """end() should transition from ACTIVE to CLEANUP then IDLE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()  # IDLE -> PRELUDE
        machine.transition_to(ShowState.ACTIVE)  # PRELUDE -> ACTIVE
        machine.end()  # ACTIVE -> CLEANUP -> IDLE
        assert machine.current_state == ShowState.IDLE

    def test_end_from_prelude_goes_to_cleanup(self):
        """end() from PRELUDE should go to CLEANUP then IDLE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()  # Now in PRELUDE
        machine.end()
        assert machine.current_state == ShowState.IDLE

    def test_valid_transitions_from_idle(self):
        """From IDLE, can only go to PRELUDE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.transition_to(ShowState.PRELUDE)
        assert machine.current_state == ShowState.PRELUDE

    def test_invalid_transition_raises_value_error(self):
        """Invalid transitions should raise ValueError"""
        machine = ShowStateMachine(show_id="test-show-1")
        with pytest.raises(ValueError, match="Cannot transition from IDLE to ACTIVE"):
            machine.transition_to(ShowState.ACTIVE)

    def test_transition_from_prelude_to_active(self):
        """From PRELUDE, can transition to ACTIVE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()  # Now in PRELUDE
        machine.transition_to(ShowState.ACTIVE)
        assert machine.current_state == ShowState.ACTIVE

    def test_transition_from_prelude_to_cleanup(self):
        """From PRELUDE, can transition to CLEANUP"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()  # Now in PRELUDE
        machine.transition_to(ShowState.CLEANUP)
        assert machine.current_state == ShowState.CLEANUP

    def test_transition_from_active_to_postlude(self):
        """From ACTIVE, can transition to POSTLUDE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.transition_to(ShowState.PRELUDE)
        machine.transition_to(ShowState.ACTIVE)
        machine.transition_to(ShowState.POSTLUDE)
        assert machine.current_state == ShowState.POSTLUDE

    def test_transition_from_active_to_cleanup(self):
        """From ACTIVE, can transition to CLEANUP"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.transition_to(ShowState.PRELUDE)
        machine.transition_to(ShowState.ACTIVE)
        machine.transition_to(ShowState.CLEANUP)
        assert machine.current_state == ShowState.CLEANUP

    def test_transition_from_postlude_to_cleanup(self):
        """From POSTLUDE, can transition to CLEANUP"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.transition_to(ShowState.PRELUDE)
        machine.transition_to(ShowState.ACTIVE)
        machine.transition_to(ShowState.POSTLUDE)
        machine.transition_to(ShowState.CLEANUP)
        assert machine.current_state == ShowState.CLEANUP

    def test_transition_from_cleanup_to_idle(self):
        """From CLEANUP, can transition to IDLE"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.transition_to(ShowState.PRELUDE)
        machine.transition_to(ShowState.ACTIVE)
        machine.transition_to(ShowState.POSTLUDE)
        machine.transition_to(ShowState.CLEANUP)
        machine.transition_to(ShowState.IDLE)
        assert machine.current_state == ShowState.IDLE

    def test_to_dict_serialization(self):
        """to_dict() should return serializable representation"""
        machine = ShowStateMachine(show_id="test-show-1")
        state_dict = machine.to_dict()
        assert state_dict["show_id"] == "test-show-1"
        assert state_dict["state"] == "IDLE"
        assert "created_at" in state_dict
        assert "updated_at" in state_dict

    def test_to_dict_after_transition(self):
        """to_dict() should reflect current state after transitions"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()
        state_dict = machine.to_dict()
        assert state_dict["state"] == "PRELUDE"


class TestShowStateMachineWithStore:
    @pytest.mark.asyncio
    async def test_state_persists_to_store_on_transition(self):
        """State should persist to RedisStateStore when available"""
        mock_store = Mock()
        mock_store.save_state = AsyncMock()

        machine = ShowStateMachine(show_id="test-show-1", state_store=mock_store)
        machine.start()

        # Give the async task a moment to be created
        await asyncio.sleep(0.01)

        mock_store.save_state.assert_called_once()
        call_args = mock_store.save_state.call_args
        assert call_args[0][0] == "test-show-1"
        assert call_args[0][1]["state"] == "PRELUDE"

    def test_state_does_not_persist_without_store(self):
        """Should work without a store (in-memory only)"""
        machine = ShowStateMachine(show_id="test-show-1")
        machine.start()
        assert machine.current_state == ShowState.PRELUDE

    @pytest.mark.asyncio
    async def test_multiple_transitions_persist_each_time(self):
        """Each transition should persist state"""
        mock_store = Mock()
        mock_store.save_state = AsyncMock()

        machine = ShowStateMachine(show_id="test-show-1", state_store=mock_store)
        machine.start()
        await asyncio.sleep(0.01)
        machine.transition_to(ShowState.ACTIVE)
        await asyncio.sleep(0.01)
        machine.transition_to(ShowState.POSTLUDE)
        await asyncio.sleep(0.01)

        assert mock_store.save_state.call_count == 3


class TestRedisStateStore:
    @pytest.mark.asyncio
    async def test_save_state_stores_data(self):
        """save_state should store state data in Redis"""
        mock_redis = Mock()
        mock_redis.setex = AsyncMock()

        from state.store import RedisStateStore
        store = RedisStateStore(redis_client=mock_redis)
        await store.save_state("test-show", {"state": "ACTIVE", "show_id": "test-show"})

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "test-show" in call_args[0][0]
        assert call_args[0][1] == 3600  # Default TTL

    @pytest.mark.asyncio
    async def test_get_state_retrieves_data(self):
        """get_state should retrieve and decode state data"""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=b'{"state": "ACTIVE", "show_id": "test-show"}')

        from state.store import RedisStateStore
        store = RedisStateStore(redis_client=mock_redis)
        state = await store.get_state("test-show")

        assert state["state"] == "ACTIVE"
        assert state["show_id"] == "test-show"

    @pytest.mark.asyncio
    async def test_get_state_returns_none_for_missing_key(self):
        """get_state should return None if key doesn't exist"""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)

        from state.store import RedisStateStore
        store = RedisStateStore(redis_client=mock_redis)
        state = await store.get_state("nonexistent-show")

        assert state is None

    @pytest.mark.asyncio
    async def test_delete_state_removes_key(self):
        """delete_state should remove the state key from Redis"""
        mock_redis = Mock()
        mock_redis.delete = AsyncMock(return_value=1)

        from state.store import RedisStateStore
        store = RedisStateStore(redis_client=mock_redis)
        result = await store.delete_state("test-show")

        mock_redis.delete.assert_called_once()
        assert result == 1

    @pytest.mark.asyncio
    async def test_connect_creates_redis_connection(self):
        """connect should create Redis connection"""
        from state.store import RedisStateStore

        async def mock_from_url(*args, **kwargs):
            mock_redis = Mock()
            mock_redis.close = AsyncMock()
            return mock_redis

        with patch('redis.asyncio.from_url', side_effect=mock_from_url) as mock_from_url_patch:
            store = RedisStateStore(url="redis://localhost")
            await store.connect()

            mock_from_url_patch.assert_called_once_with("redis://localhost", decode_responses=True)
            assert store._redis is not None

    @pytest.mark.asyncio
    async def test_disconnect_closes_connection(self):
        """disconnect should close Redis connection"""
        mock_redis = Mock()
        mock_redis.close = AsyncMock()

        from state.store import RedisStateStore
        store = RedisStateStore(redis_client=mock_redis)
        await store.disconnect()

        mock_redis.close.assert_called_once()
