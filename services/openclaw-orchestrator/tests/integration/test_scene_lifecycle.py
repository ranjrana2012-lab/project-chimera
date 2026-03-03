"""
Integration tests for Scene Lifecycle and Transitions.

Tests end-to-end flows for scene transitions, agent handoff,
audience context preservation, and undo/redo.
"""

import pytest
import time
import asyncio
from datetime import datetime, timezone, timedelta

import sys
sys.path.insert(0, '.')

from core.scene_manager import SceneManager, SceneConfig, SceneState
from transitions.time_triggers import TimeTriggerScheduler, TimeTriggerType, TimeTriggerConfig
from transitions.event_triggers import EventTriggerScheduler, EventType, EventTriggerConfig
from transitions.transition_effects import TransitionType, TransitionEffectConfig, TransitionEffectExecutor
from transitions.agent_handoff import AgentHandoffConfig, AgentHandoffOrchestrator
from transitions.audience_context import AudienceContext, AudienceContextManager, ContextMergeStrategy
from transitions.undo_redo import UndoRedoManager


class TestEndToEndTransitions:
    """Test complete transition workflows."""

    @pytest.fixture
    def scene_factory(self):
        """Create scene managers."""
        def create(scene_id, scene_type="dialogue"):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type=scene_type,
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            return manager
        return create

    def test_simple_scene_transition(self, scene_factory):
        """Test basic scene transition."""
        scene1 = scene_factory("scene-001")
        scene2 = scene_factory("scene-002")

        # Activate first scene
        scene1.activate()
        assert scene1.state == SceneState.ACTIVE

        # Transition to second scene
        scene1.complete("Transition to scene-002")
        scene2.activate()

        assert scene1.state == SceneState.COMPLETED
        assert scene2.state == SceneState.ACTIVE

    def test_multi_scene_orchestration(self, scene_factory):
        """Test multiple active scenes."""
        from core.multi_scene import MultiSceneOrchestrator

        orchestrator = MultiSceneOrchestrator(max_scenes=3)

        scene1 = scene_factory("scene-001")
        scene2 = scene_factory("scene-002")
        scene3 = scene_factory("scene-003")

        # Activate scenes first before adding
        scene1.activate()
        scene2.activate()
        scene3.activate()

        # Add scenes with different priorities
        orchestrator.add_scene(scene1, priority=50)
        orchestrator.add_scene(scene2, priority=75)  # Higher priority
        orchestrator.add_scene(scene3, priority=25)  # Lower priority

        assert orchestrator.active_scene_count == 3

        # Get ordered scenes by priority
        ordered = orchestrator.get_scenes_by_priority()
        assert ordered[0].scene_id == "scene-002"  # Highest priority


class TestTransitionTriggers:
    """Test transition trigger integration."""

    @pytest.fixture
    def scene_factory(self):
        """Create scene managers."""
        def create(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()
            return manager
        return create

    def test_time_based_transition(self, scene_factory):
        """Test scheduled time trigger integration."""
        from transitions.time_triggers import TransitionType as TimeTransitionType, TimeTrigger

        scheduler = TimeTriggerScheduler()
        scene1 = scene_factory("scene-001")
        scene2 = scene_factory("scene-002")

        # Create trigger for future time
        trigger_time = datetime.now(timezone.utc) + timedelta(seconds=10)

        config = TimeTriggerConfig(
            trigger_id="tt-scheduled",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TimeTransitionType.CUT,
            scheduled_time=trigger_time
        )

        trigger = TimeTrigger(config)
        scheduler.add_trigger(trigger)

        # Verify trigger is registered
        registered = scheduler.get_trigger("tt-scheduled")
        assert registered is not None
        assert registered.trigger_id == "tt-scheduled"

        # Check ready triggers - none should be ready yet
        ready = scheduler.get_ready_triggers()
        assert len(ready) == 0  # Should not be ready yet

    def test_event_based_transition(self, scene_factory):
        """Test event-based trigger integration."""
        from transitions.event_triggers import EventCondition, EventTrigger

        scheduler = EventTriggerScheduler()
        scene1 = scene_factory("scene-001")
        scene2 = scene_factory("scene-002")

        condition = EventCondition(
            topic="audience.events",
            event_type=EventType.AUDIENCE_THRESHOLD.value,
            metadata_filter={"metric": "engagement"}
        )

        config = EventTriggerConfig(
            trigger_id="et-threshold",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            event_condition=condition
        )

        trigger = EventTrigger(config)
        scheduler.add_trigger(trigger)

        # Verify trigger is registered
        registered = scheduler.get_trigger("et-threshold")
        assert registered is not None
        assert registered.trigger_id == "et-threshold"

        # Process event
        scheduler.process_event(
            "audience.events",
            {"metric": "engagement", "value": 150}
        )

        # Trigger should still be registered (event processed)
        assert scheduler.get_trigger("et-threshold") is not None


class TestAgentHandoffIntegration:
    """Test agent handoff in transition context."""

    @pytest.fixture
    def scene_factory(self):
        """Create scene managers with agent states."""
        def create(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            manager.activate()

            # Set up agent state
            manager._state_data["agent_states"] = {
                "scenespeak": {"context": f"Active in {scene_id}"},
                "sentiment": {"scores": [0.5, 0.6]}
            }

            return manager
        return create

    def test_agent_handoff_during_transition(self, scene_factory):
        """Test agent handoff when transitioning scenes."""
        source = scene_factory("scene-001")
        target = scene_factory("scene-002")

        orchestrator = AgentHandoffOrchestrator()

        # Create handoff for scenespeak agent
        handoff_id = orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        # Execute handoff
        results = orchestrator.execute_all()

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].agent_id == "scenespeak"

        # Verify state transferred
        target_state = target._state_data["agent_states"].get("scenespeak")
        assert target_state is not None
        assert "scene-001" in target_state.get("context", "")

    def test_concurrent_agent_handoffs(self, scene_factory):
        """Test multiple agent handoffs during transition."""
        source = scene_factory("scene-001")
        target = scene_factory("scene-002")

        # Add context for sentiment agent
        source._state_data["agent_states"]["sentiment"] = {
            "context": "sentiment analysis active",
            "scores": [0.5, 0.6]
        }

        orchestrator = AgentHandoffOrchestrator()

        # Handoff multiple agents
        orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        orchestrator.create_handoff(
            agent_id="sentiment",
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            source_scene=source,
            target_scene=target
        )

        # Execute all
        results = orchestrator.execute_all()

        assert len(results) == 2
        assert all(r.success for r in results)


class TestAudienceContextIntegration:
    """Test audience context preservation in transitions."""

    @pytest.fixture
    def context_manager(self):
        """Create audience context manager."""
        return AudienceContextManager()

    def test_context_preservation_across_transitions(self, context_manager):
        """Test context preserved through multiple transitions."""
        # Create initial context
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "theme": "light"},
            sentiment_history=[0.5, 0.6],
            interaction_count=10
        )

        context_manager.register_context("scene-001", context)

        # Capture context before transition
        snapshot_id = context_manager.capture_context("scene-001")

        # Simulate transition - modify context in new scene
        new_context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "theme": "dark"},  # Theme changed
            sentiment_history=[0.5, 0.6, 0.7],  # New sentiment
            interaction_count=15  # More interactions
        )

        context_manager.register_context("scene-002", new_context)

        # Update sentiment
        context_manager.update_sentiment("aud-001", 0.8)

        # Restore original context
        restored = context_manager.restore_context(snapshot_id, "scene-003")

        assert restored is not None
        assert "aud-001" in restored
        assert restored["aud-001"].preferences["theme"] == "light"

    def test_context_merge_on_scene_return(self, context_manager):
        """Test context merge when returning to previous scene."""
        # Original context
        context1 = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "volume": "medium"},
            sentiment_history=[0.5],
            interaction_count=5
        )

        context_manager.register_context("scene-001", context1)

        # Modified context in scene-002
        context2 = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en", "captions": True},  # New preference
            sentiment_history=[0.5, 0.6],
            interaction_count=10
        )

        context_manager.register_context("scene-002", context2)

        # Merge when returning
        result = context_manager.merge_contexts(
            [context1, context2],
            strategy=ContextMergeStrategy.MERGE
        )

        assert result.success is True
        merged = result.merged_context
        assert merged.preferences["language"] == "en"
        assert merged.preferences["volume"] == "medium"
        assert merged.preferences["captions"] is True


class TestTransitionEffectsIntegration:
    """Test transition effects with scenes."""

    @pytest.fixture
    def scene_factory(self):
        """Create scene managers."""
        def create(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            return manager
        return create

    def test_cut_transition_effect(self, scene_factory):
        """Test CUT transition effect."""
        executor = TransitionEffectExecutor()
        source = scene_factory("scene-001")
        target = scene_factory("scene-002")

        source.activate()

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.CUT,
            duration_seconds=0.1
        )

        effect_id = executor.execute_transition(config, source, target)

        # CUT is immediate
        effect = executor.get_effect(effect_id)
        assert effect.state.value == "complete"

    def test_fade_transition_effect(self, scene_factory):
        """Test FADE transition effect."""
        executor = TransitionEffectExecutor()
        source = scene_factory("scene-001")
        target = scene_factory("scene-002")

        config = TransitionEffectConfig(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE,
            duration_seconds=1.0
        )

        effect_id = executor.execute_transition(config, source, target)

        effect = executor.get_effect(effect_id)
        assert effect.state.value == "running"

        # Wait for completion
        time.sleep(1.5)

        effect = executor.get_effect(effect_id)
        assert effect.state.value == "complete"


class TestUndoRedoIntegration:
    """Test undo/redo with full transition workflow."""

    @pytest.fixture
    def scene_factory(self):
        """Create scene managers."""
        def create(scene_id):
            config = SceneConfig(
                scene_id=scene_id,
                name=f"Scene {scene_id}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            return manager
        return create

    def test_undo_transition_workflow(self, scene_factory):
        """Test complete undo workflow."""
        manager = UndoRedoManager()
        scene1 = scene_factory("scene-001")
        scene2 = scene_factory("scene-002")

        # Initial state: scene1 active
        scene1.activate()

        # Record transition
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        # Perform transition (pause scene1 instead of completing)
        scene1.pause()
        scene2.activate()

        assert scene2.state == SceneState.ACTIVE

        # Undo transition
        result = manager.undo(scene2, scene1)

        assert result.success is True
        assert result.action == "undo"

    def test_redo_transition_workflow(self, scene_factory):
        """Test complete redo workflow."""
        manager = UndoRedoManager()
        scene1 = scene_factory("scene-001")
        scene2 = scene_factory("scene-002")

        # Initial state
        scene1.activate()

        # Record and perform transition
        manager.record_transition(
            source_scene_id="scene-001",
            target_scene_id="scene-002",
            transition_type=TransitionType.FADE
        )

        scene1.pause()
        scene2.activate()

        # Undo
        undo_result = manager.undo(scene2, scene1)
        assert undo_result.success is True

        # Redo - scene2 is now completed, so we'll test the redo mechanics
        # In a real scenario, you'd create a new scene instance
        # For this test, we verify redo is available and processes correctly
        assert manager.can_redo() is True

        # Create new scene instances for redo (simulating fresh scene)
        new_scene1 = scene_factory("scene-001")
        new_scene2 = scene_factory("scene-002")
        new_scene1.activate()

        result = manager.redo(new_scene1, new_scene2)

        assert result.success is True
        assert result.action == "redo"

    def test_multiple_undo_redo(self, scene_factory):
        """Test multiple undo/redo operations."""
        manager = UndoRedoManager()
        scenes = [scene_factory(f"scene-{i:03d}") for i in range(4)]

        # Initial state
        scenes[0].activate()

        # Perform transitions (pause instead of complete)
        for i in range(3):
            manager.record_transition(
                source_scene_id=f"scene-{i:03d}",
                target_scene_id=f"scene-{i+1:03d}",
                transition_type=TransitionType.CUT
            )

            scenes[i].pause()
            scenes[i+1].activate()

        # Should be on scene-003
        assert scenes[3].state == SceneState.ACTIVE

        # Test undo capability
        assert manager.can_undo() is True
        assert manager.get_history_count() == 3

        # Undo once
        undo_result1 = manager.undo(scenes[3], scenes[2])
        assert undo_result1.success is True

        # Test manager state after undo
        assert manager.get_redo_count() == 1

        # Undo again
        undo_result2 = manager.undo(scenes[2], scenes[1])
        assert undo_result2.success is True

        # Verify manager state
        assert manager.get_redo_count() == 2
        assert manager.get_history_count() == 1


class TestCompleteWorkflow:
    """Test complete transition workflow with all components."""

    @pytest.fixture
    def setup_full_workflow(self):
        """Set up complete workflow components."""
        from core.multi_scene import MultiSceneOrchestrator

        # Create components
        multi_orchestrator = MultiSceneOrchestrator(max_scenes=3)
        agent_orchestrator = AgentHandoffOrchestrator()
        context_manager = AudienceContextManager()
        effect_executor = TransitionEffectExecutor()
        undo_manager = UndoRedoManager()

        # Create scenes
        scenes = {}
        for i in range(3):
            config = SceneConfig(
                scene_id=f"scene-{i:03d}",
                name=f"Scene {i}",
                scene_type="dialogue",
                version="1.0.0"
            )
            manager = SceneManager(config)
            manager.initialize()
            scenes[f"scene-{i:03d}"] = manager

        # Set up agent states
        scenes["scene-000"]._state_data["agent_states"] = {
            "scenespeak": {"context": "Welcome"},
            "sentiment": {"scores": [0.5]}
        }

        # Set up audience context
        context = AudienceContext(
            audience_id="aud-001",
            preferences={"language": "en"},
            sentiment_history=[0.5],
            interaction_count=0
        )
        context_manager.register_context("scene-000", context)

        return {
            "multi_orchestrator": multi_orchestrator,
            "agent_orchestrator": agent_orchestrator,
            "context_manager": context_manager,
            "effect_executor": effect_executor,
            "undo_manager": undo_manager,
            "scenes": scenes
        }

    def test_complete_transition_flow(self, setup_full_workflow):
        """Test end-to-end transition with all components."""
        components = setup_full_workflow
        scenes = components["scenes"]
        agent_orchestrator = components["agent_orchestrator"]
        context_manager = components["context_manager"]
        effect_executor = components["effect_executor"]
        undo_manager = components["undo_manager"]

        # Initial state
        scenes["scene-000"].activate()
        scenes["scene-001"].activate()

        assert scenes["scene-000"].state == SceneState.ACTIVE
        assert scenes["scene-001"].state == SceneState.ACTIVE

        # 1. Record transition in undo manager
        undo_manager.record_transition(
            source_scene_id="scene-000",
            target_scene_id="scene-001",
            transition_type=TransitionType.FADE
        )

        # 2. Capture audience context
        snapshot_id = context_manager.capture_context("scene-000")

        # 3. Execute transition effect
        effect_config = TransitionEffectConfig(
            source_scene_id="scene-000",
            target_scene_id="scene-001",
            transition_type=TransitionType.CUT,
            duration_seconds=0.1
        )
        effect_executor.execute_transition(effect_config, scenes["scene-000"], scenes["scene-001"])

        # 4. Handoff agents
        agent_orchestrator.create_handoff(
            agent_id="scenespeak",
            source_scene_id="scene-000",
            target_scene_id="scene-001",
            source_scene=scenes["scene-000"],
            target_scene=scenes["scene-001"]
        )
        agent_results = agent_orchestrator.execute_all()

        # Verify components
        assert agent_results[0].success is True
        assert context_manager.get_snapshot(snapshot_id) is not None
        assert undo_manager.can_undo() is True

        # 5. Update audience in new scene
        context_manager.update_sentiment("aud-001", 0.7)
        context_manager.increment_interactions("aud-001", 5)

        # Verify context updated
        updated_context = context_manager.get_context("aud-001")
        assert updated_context.sentiment_history[-1] == 0.7
        assert updated_context.interaction_count == 5

        # 6. Test undo capability (verify state, don't execute)
        assert undo_manager.can_undo() is True
        assert undo_manager.get_history_count() == 1

        # 7. Test context restoration
        restored = context_manager.restore_context(snapshot_id, "scene-002")
        assert restored is not None
        assert "aud-001" in restored

        # 8. Verify complete workflow integration
        # All components are working together
        assert agent_results[0].success is True
        assert context_manager.get_context("aud-001") is not None
        assert undo_manager.get_history_count() > 0
