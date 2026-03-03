"""
Unit tests for Agent Handoff Logic.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

import sys
sys.path.insert(0, '.')

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.agent_handoff import (
    AgentHandoffConfig,
    AgentHandoff,
    HandoffResult,
    HandoffState,
    AgentHandoffOrchestrator,
    AgentStateSnapshot
)


class TestAgentStateSnapshot:
    """Test AgentStateSnapshot dataclass."""

    def test_create_snapshot(self):
        """Create agent state snapshot."""
        snapshot = AgentStateSnapshot(
            agent_id="scenespeak",
            agent_type="llm",
            state_data={"context": "test context"},
            metadata={"version": "1.0"}
        )

        assert snapshot.agent_id == "scenespeak"
        assert snapshot.agent_type == "llm"
        assert snapshot.state_data == {"context": "test context"}

    def test_snapshot_serialization(self):
        """Test snapshot to dict conversion."""
        snapshot = AgentStateSnapshot(
            agent_id="sentiment",
            agent_type="ml",
            state_data={"scores": [0.5, 0.3, 0.8]},
            metadata={"model": "sentiment-v1"}
        )

        data_dict = snapshot.to_dict()

        assert data_dict["agent_id"] == "sentiment"
        assert data_dict["agent_type"] == "ml"
        assert "state_data" in data_dict
        assert "serialized_at" in data_dict

    def test_snapshot_deserialization(self):
        """Test dict to snapshot conversion."""
        data_dict = {
            "agent_id": "captioning",
            "agent_type": "translation",
            "state_data": {"last_caption": "Hello world"},
            "metadata": {},
            "serialized_at": "2026-03-04T05:00:00Z"
        }

        snapshot = AgentStateSnapshot.from_dict(data_dict)

        assert snapshot.agent_id == "captioning"
        assert snapshot.state_data == {"last_caption": "Hello world"}

    def test_roundtrip_serialization(self):
        """Test roundtrip serialization."""
        original = AgentStateSnapshot(
            agent_id="lighting",
            agent_type="controller",
            state_data={"intensity": 0.8},
            metadata={"mode": "auto"}
        )

        # Serialize
        data_dict = original.to_dict()

        # Deserialize
        restored = AgentStateSnapshot.from_dict(data_dict)

        assert restored.agent_id == original.agent_id
        assert restored.agent_type == original.agent_type
        assert restored.state_data == original.state_data
        assert restored.metadata == original.metadata


class TestHandoffResult:
    """Test HandoffResult dataclass."""

    def test_success_result(self):
        """Create successful handoff result."""
        result = HandoffResult(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            success=True,
            transferred_bytes=1024
        )

        assert result.success is True
        assert result.transferred_bytes == 1024
        assert result.error is None

    def test_failure_result(self):
        """Create failed handoff result."""
        result = HandoffResult(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            success=False,
            error="Agent not responding"
        )

        assert result.success is False
        assert result.error == "Agent not responding"
        assert result.transferred_bytes == 0


class TestAgentHandoff:
    """Test AgentHandoff class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return AgentHandoffConfig(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            timeout_seconds=5.0,
            retry_attempts=3
        )

    @pytest.fixture
    def source_scene(self):
        """Create source scene manager."""
        config = SceneConfig(
            scene_id="scene-001",
            name="Scene 1",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)
        manager.initialize()
        manager.activate()
        # Mock agent state
        manager._state_data["agent_states"] = {
            "scenespeak": {"context": "active conversation"}
        }
        return manager

    @pytest.fixture
    def target_scene(self):
        """Create target scene manager."""
        config = SceneConfig(
            scene_id="scene-002",
            name="Scene 2",
            scene_type="dialogue",
            version="1.0.0"
        )
        manager = SceneManager(config)
        manager.initialize()
        return manager

    def test_create_handoff(self, config, source_scene, target_scene):
        """Create agent handoff."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        assert handoff.handoff_id is not None
        assert handoff.agent_id == "scenespeak"
        assert handoff.state == HandoffState.PENDING

    def test_capture_snapshot(self, config, source_scene, target_scene):
        """Capture agent state snapshot."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        snapshot = handoff._capture_snapshot()

        assert snapshot.agent_id == "scenespeak"
        assert "context" in snapshot.state_data

    def test_validate_snapshot_success(self, config, source_scene, target_scene):
        """Validate snapshot successfully."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        snapshot = AgentStateSnapshot(
            agent_id="scenespeak",
            agent_type="llm",
            state_data={"context": "test"},
            metadata={}
        )

        result = handoff._validate_snapshot(snapshot)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_snapshot_missing_data(self, config, source_scene, target_scene):
        """Validate snapshot with missing required data."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        snapshot = AgentStateSnapshot(
            agent_id="scenespeak",
            agent_type="llm",
            state_data={},  # Missing required context
            metadata={}
        )

        result = handoff._validate_snapshot(snapshot)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_execute_handoff_success(self, config, source_scene, target_scene):
        """Execute successful handoff."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        result = handoff.execute()

        assert result.success is True
        assert result.agent_id == "scenespeak"
        assert handoff.state == HandoffState.COMPLETE

    def test_execute_handoff_with_retry(self, config, source_scene, target_scene):
        """Execute handoff with retry on failure."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        # Mock _transfer_state to fail first attempt
        transfer_call_count = [0]

        def mock_transfer(snapshot):
            transfer_call_count[0] += 1
            if transfer_call_count[0] < 2:
                raise Exception("Transfer failed")
            return True

        handoff._transfer_state = mock_transfer
        handoff._max_retries = 3

        result = handoff.execute()

        assert result.success is True
        assert transfer_call_count[0] == 2  # Succeeded on retry

    def test_execute_handoff_max_retries(self, config, source_scene, target_scene):
        """Execute handoff that exceeds max retries."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        # Mock _transfer_state to always fail
        def mock_transfer(snapshot):
            raise Exception("Always fails")

        handoff._transfer_state = mock_transfer
        handoff._max_retries = 3

        result = handoff.execute()

        assert result.success is False
        assert "max retries" in result.error.lower()

    def test_cancel_handoff(self, config, source_scene, target_scene):
        """Cancel pending handoff."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        handoff.cancel("Cancelled by operator")

        assert handoff.state == HandoffState.CANCELLED

    def test_get_handoff_status(self, config, source_scene, target_scene):
        """Get handoff status."""
        handoff = AgentHandoff(config, source_scene, target_scene)

        status = handoff.get_status()

        assert status["handoff_id"] == handoff.handoff_id
        assert status["agent_id"] == "scenespeak"
        assert status["state"] == "pending"


class TestAgentHandoffOrchestrator:
    """Test AgentHandoffOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator."""
        return AgentHandoffOrchestrator()

    @pytest.fixture
    def scene_manager_factory(self):
        """Create scene managers."""
        def create_manager(scene_id, with_agent_state=True):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()
            # Set up agent state for tests
            if with_agent_state:
                manager._state_data["agent_states"] = {
                    "scenespeak": {"context": "active conversation"},
                    "sentiment": {"context": "sentiment analysis active", "scores": [0.5, 0.3, 0.8]}
                }
            return manager
        return create_manager

    def test_orchestrator_init(self, orchestrator):
        """Initialize orchestrator."""
        assert len(orchestrator._handoffs) == 0
        assert len(orchestrator._active_handoffs) == 0

    def test_create_handoff(self, orchestrator, scene_manager_factory):
        """Create and execute handoff."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        handoff_id = orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        assert handoff_id is not None
        assert handoff_id.startswith("hho-")

    def test_execute_concurrent_handoffs(self, orchestrator, scene_manager_factory):
        """Execute multiple handoffs concurrently."""
        source1 = scene_manager_factory("scene-001")
        target1 = scene_manager_factory("scene-002")

        source2 = scene_manager_factory("scene-003")
        target2 = scene_manager_factory("scene-004")

        # Create handoffs
        orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source1,
            target_scene=target1
        )

        orchestrator.create_handoff(
            agent_id="sentiment",
            source_scene_id="scene-003",
            target_scene_id="scene-004",
            source_scene=source2,
            target_scene=target2
        )

        # Execute all
        results = orchestrator.execute_all()

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_get_handoff_status(self, orchestrator, scene_manager_factory):
        """Get handoff status."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        handoff_id = orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        status = orchestrator.get_handoff_status(handoff_id)

        assert status["handoff_id"] == handoff_id
        assert status["agent_id"] == "scenespeak"
        assert status["state"] == "pending"

    def test_cancel_handoff(self, orchestrator, scene_manager_factory):
        """Cancel a handoff."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        handoff_id = orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        cancelled = orchestrator.cancel_handoff(handoff_id, "Test cancellation")

        assert cancelled is True

    def test_cleanup_completed_handoffs(self, orchestrator, scene_manager_factory):
        """Cleanup old completed handoffs."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        # Execute to complete
        orchestrator.execute_all()

        # Cleanup
        cleaned = orchestrator.cleanup_completed_handoffs(max_age_seconds=0)

        assert cleaned >= 1

    def test_get_handoff_history(self, orchestrator, scene_manager_factory):
        """Get handoff history."""
        source = scene_manager_factory("scene-001")
        target = scene_manager_factory("scene-002")

        orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        orchestrator.execute_all()

        history = orchestrator.get_handoff_history()

        assert len(history) == 1
        assert history[0]["agent_id"] == "scenespeak"
