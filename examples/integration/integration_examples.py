#!/usr/bin/env python3
"""
Project Chimera - Phase 2 Service Integration Examples

This module demonstrates how to integrate Phase 2 hardware services
(DMX Controller, Audio Controller, BSL Avatar Service) with the
Chimera Core orchestrator for adaptive live theatre experiences.

Usage:
    python integration_examples.py --example basic_show
    python integration_examples.py --example adaptive_scene
    python integration_examples.py --example emergency_procedures
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import requests
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

class ServiceConfig:
    """Configuration for Phase 2 service endpoints."""

    DMX_CONTROLLER = "http://localhost:8001"
    AUDIO_CONTROLLER = "http://localhost:8002"
    BSL_AVATAR_SERVICE = "http://localhost:8003"
    CHIMERA_CORE = "http://localhost:8000"

    # Timeouts
    REQUEST_TIMEOUT = 10
    HEALTH_CHECK_TIMEOUT = 5


# =============================================================================
# Data Models
# =============================================================================

class SentimentLevel(Enum):
    """Audience sentiment levels."""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class ShowState:
    """Current state of the show."""
    sentiment_level: SentimentLevel = SentimentLevel.NEUTRAL
    current_scene: str = "intro"
    audience_engagement: float = 0.5
    last_update: datetime = field(default_factory=datetime.now)

    def should_adapt(self) -> bool:
        """Determine if adaptation is needed based on state."""
        return self.sentiment_level != SentimentLevel.NEUTRAL


@dataclass
class LightingCue:
    """Lighting cue configuration."""
    scene_name: str
    fixture_values: Dict[str, Dict[int, int]]
    transition_time_ms: int
    intensity_modifier: float = 1.0


@dataclass
class AudioCue:
    """Audio cue configuration."""
    track_id: str
    volume_db: float
    fade_time_ms: int = 1000
    play_mode: str = "play"  # play, stop, pause


@dataclass
class BSLCue:
    """BSL avatar cue configuration."""
    text: str
    render_options: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Service Clients
# =============================================================================

class DMXClient:
    """Client for DMX Controller service."""

    def __init__(self, base_url: str = ServiceConfig.DMX_CONTROLLER):
        self.base_url = base_url
        self.timeout = ServiceConfig.REQUEST_TIMEOUT

    def health_check(self) -> bool:
        """Check if DMX service is healthy."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def create_scene(self, cue: LightingCue) -> bool:
        """Create a lighting scene."""
        try:
            # Apply intensity modifier
            modified_values = {}
            for fixture_id, channels in cue.fixture_values.items():
                modified_values[fixture_id] = {
                    ch: int(val * cue.intensity_modifier)
                    for ch, val in channels.items()
                }

            response = requests.post(
                f"{self.base_url}/api/scenes",
                json={
                    "name": cue.scene_name,
                    "fixture_values": modified_values,
                    "transition_time_ms": cue.transition_time_ms
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"DMX Error: {e}")
            return False

    def activate_scene(self, scene_name: str) -> bool:
        """Activate a lighting scene."""
        try:
            response = requests.post(
                f"{self.base_url}/api/scenes/{scene_name}/activate",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"DMX Error: {e}")
            return False

    def emergency_stop(self) -> bool:
        """Activate emergency stop (blackout)."""
        try:
            response = requests.post(
                f"{self.base_url}/api/emergency_stop",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"DMX Emergency Error: {e}")
            return False

    def reset_emergency(self) -> bool:
        """Reset from emergency stop state."""
        try:
            response = requests.post(
                f"{self.base_url}/api/reset_emergency",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"DMX Reset Error: {e}")
            return False


class AudioClient:
    """Client for Audio Controller service."""

    def __init__(self, base_url: str = ServiceConfig.AUDIO_CONTROLLER):
        self.base_url = base_url
        self.timeout = ServiceConfig.REQUEST_TIMEOUT

    def health_check(self) -> bool:
        """Check if Audio service is healthy."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def set_volume(self, volume_db: float) -> bool:
        """Set master volume."""
        try:
            response = requests.post(
                f"{self.base_url}/api/volume/master",
                json={"volume_db": volume_db},
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Audio Error: {e}")
            return False

    def play_track(self, track_id: str, volume_db: Optional[float] = None) -> bool:
        """Play a track."""
        try:
            if volume_db is not None:
                # Set volume first
                self.set_track_volume(track_id, volume_db)

            response = requests.post(
                f"{self.base_url}/api/tracks/{track_id}/play",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Audio Error: {e}")
            return False

    def set_track_volume(self, track_id: str, volume_db: float) -> bool:
        """Set track volume."""
        try:
            response = requests.post(
                f"{self.base_url}/api/tracks/{track_id}/volume",
                json={"volume_db": volume_db},
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Audio Error: {e}")
            return False

    def emergency_mute(self) -> bool:
        """Activate emergency mute."""
        try:
            response = requests.post(
                f"{self.base_url}/api/emergency_mute",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Audio Emergency Error: {e}")
            return False

    def reset_emergency(self) -> bool:
        """Reset from emergency mute state."""
        try:
            response = requests.post(
                f"{self.base_url}/api/reset_emergency",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Audio Reset Error: {e}")
            return False


class BSLClient:
    """Client for BSL Avatar Service."""

    def __init__(self, base_url: str = ServiceConfig.BSL_AVATAR_SERVICE):
        self.base_url = base_url
        self.timeout = ServiceConfig.REQUEST_TIMEOUT

    def health_check(self) -> bool:
        """Check if BSL service is healthy."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=ServiceConfig.HEALTH_CHECK_TIMEOUT
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def translate(self, text: str) -> Optional[Dict[str, Any]]:
        """Translate text to BSL gestures."""
        try:
            response = requests.post(
                f"{self.base_url}/api/translate",
                json={"text": text},
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"BSL Error: {e}")
            return None

    def render_avatar(self, text: str, options: Optional[Dict] = None) -> bool:
        """Render avatar animation."""
        try:
            payload = {"text": text}
            if options:
                payload["render_options"] = options

            response = requests.post(
                f"{self.base_url}/api/render",
                json=payload,
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"BSL Render Error: {e}")
            return False


# =============================================================================
# Integration Orchestrator
# =============================================================================

class ShowOrchestrator:
    """
    Main orchestrator for integrating Phase 2 services with Chimera Core.

    This class demonstrates how to coordinate DMX lighting, audio, and BSL
    avatar services based on audience sentiment and show state.
    """

    def __init__(self):
        self.dmx = DMXClient()
        self.audio = AudioClient()
        self.bsl = BSLClient()
        self.state = ShowState()
        self.running = False

    def check_all_services(self) -> Dict[str, bool]:
        """Health check for all services."""
        return {
            "dmx": self.dmx.health_check(),
            "audio": self.audio.health_check(),
            "bsl": self.bsl.health_check(),
        }

    def start_show(self):
        """Initialize the show."""
        print("🎭 Starting Project Chimera Show...")

        # Check service health
        health = self.check_all_services()
        unhealthy = [s for s, h in health.items() if not h]

        if unhealthy:
            print(f"⚠️  Warning: Unhealthy services: {unhealthy}")
            print("   Continuing anyway (demo mode)...")
        else:
            print("✅ All services healthy")

        self.running = True

    def stop_show(self):
        """Stop the show gracefully."""
        print("🛑 Stopping show...")
        self.running = False

    def update_sentiment(self, sentiment: float):
        """Update audience sentiment level."""
        # Convert float sentiment to SentimentLevel
        if sentiment < -0.75:
            self.state.sentiment_level = SentimentLevel.VERY_NEGATIVE
        elif sentiment < -0.25:
            self.state.sentiment_level = SentimentLevel.NEGATIVE
        elif sentiment < 0.25:
            self.state.sentiment_level = SentimentLevel.NEUTRAL
        elif sentiment < 0.75:
            self.state.sentiment_level = SentimentLevel.POSITIVE
        else:
            self.state.sentiment_level = SentimentLevel.VERY_POSITIVE

        self.state.last_update = datetime.now()
        print(f"📊 Sentiment updated: {self.state.sentiment_level.name}")

    def execute_adaptive_scene(self):
        """Execute scene based on current sentiment."""
        if not self.running:
            return

        sentiment = self.state.sentiment_level

        # Define scenes for different sentiment levels
        scenes = {
            SentimentLevel.VERY_NEGATIVE: LightingCue(
                "somber_scene",
                {
                    "mh_1": {1: 100, 4: 50, 5: 0, 6: 100},  # Dim, blue
                    "mh_2": {1: 80, 4: 30, 5: 0, 6: 80}
                },
                3000,
                intensity_modifier=0.5
            ),
            SentimentLevel.NEGATIVE: LightingCue(
                "tense_scene",
                {
                    "mh_1": {1: 150, 4: 200, 5: 0, 6: 50},  # Dim, red
                    "mh_2": {1: 120, 4: 150, 5: 0, 6: 30}
                },
                2000,
                intensity_modifier=0.7
            ),
            SentimentLevel.NEUTRAL: LightingCue(
                "neutral_scene",
                {
                    "mh_1": {1: 200, 4: 255, 5: 200, 6: 150},  # Warm white
                    "mh_2": {1: 180, 4: 255, 5: 180, 6: 120}
                },
                2000,
                intensity_modifier=1.0
            ),
            SentimentLevel.POSITIVE: LightingCue(
                "bright_scene",
                {
                    "mh_1": {1: 230, 4: 255, 5: 255, 6: 200},  # Bright, warm
                    "mh_2": {1: 200, 4: 255, 5: 255, 6: 180}
                },
                1500,
                intensity_modifier=1.2
            ),
            SentimentLevel.VERY_POSITIVE: LightingCue(
                "celebration_scene",
                {
                    "mh_1": {1: 255, 4: 255, 5: 200, 6: 100},  # Full bright, celebration
                    "mh_2": {1: 255, 4: 255, 5: 180, 6: 80}
                },
                1000,
                intensity_modifier=1.5
            ),
        }

        # Get appropriate scene
        scene = scenes.get(sentiment, scenes[SentimentLevel.NEUTRAL])

        # Create and activate scene
        print(f"🎨 Activating scene: {scene.scene_name}")
        if self.dmx.create_scene(scene):
            self.dmx.activate_scene(scene.scene_name)
            self.state.current_scene = scene.scene_name

    def execute_adaptive_audio(self):
        """Execute audio based on current sentiment."""
        if not self.running:
            return

        sentiment = self.state.sentiment_level

        # Define audio responses
        if sentiment == SentimentLevel.VERY_NEGATIVE:
            # Lower volume, somber music
            self.audio.set_volume(-24)
            self.audio.play_track("somber_bgm")
        elif sentiment == SentimentLevel.NEGATIVE:
            # Moderate volume, tense music
            self.audio.set_volume(-18)
            self.audio.play_track("tense_bgm")
        elif sentiment == SentimentLevel.NEUTRAL:
            # Normal volume, neutral music
            self.audio.set_volume(-12)
            self.audio.play_track("neutral_bgm")
        elif sentiment == SentimentLevel.POSITIVE:
            # Higher volume, upbeat music
            self.audio.set_volume(-9)
            self.audio.play_track("upbeat_bgm")
        else:  # VERY_POSITIVE
            # Full volume, celebration music
            self.audio.set_volume(-6)
            self.audio.play_track("celebration_bgm")

    def execute_bsl_translation(self, text: str):
        """Execute BSL translation for accessibility."""
        if not self.running:
            return

        print(f"🤟 Translating to BSL: {text}")
        result = self.bsl.translate(text)

        if result:
            gestures = result["translation"]["gestures"]
            hit_rate = result["translation"]["library_hit_rate"]
            print(f"   Used {len(gestures)} gestures (hit rate: {hit_rate:.1%})")

            # Render avatar
            self.bsl.render_avatar(text)

    def emergency_shutdown_all(self):
        """Emergency shutdown of all services."""
        print("🚨 EMERGENCY SHUTDOWN")

        # Emergency stop all services
        self.dmx.emergency_stop()
        self.audio.emergency_mute()

        print("✅ All services stopped safely")

    def reset_all_emergencies(self):
        """Reset all services from emergency states."""
        print("🔄 Resetting emergency states...")

        self.dmx.reset_emergency()
        self.audio.reset_emergency()

        print("✅ All services reset")


# =============================================================================
# Example Scenes
# =============================================================================

class ExampleScenes:
    """Pre-configured example scenes demonstrating integration."""

    @staticmethod
    def basic_welcome(orchestrator: ShowOrchestrator):
        """Basic welcome scene with all services."""
        print("\n=== Scene: Basic Welcome ===\n")

        # Set welcoming lighting
        welcome_scene = LightingCue(
            "welcome",
            {
                "mh_1": {1: 200, 4: 255, 5: 200, 6: 100},
                "mh_2": {1: 180, 4: 255, 5: 180, 6: 80}
            },
            3000
        )
        orchestrator.dmx.create_scene(welcome_scene)
        orchestrator.dmx.activate_scene("welcome")

        # Start background music
        orchestrator.audio.set_volume(-12)
        orchestrator.audio.play_track("welcome_bgm")

        # Display welcome message in BSL
        orchestrator.execute_bsl_translation("Welcome to Project Chimera")

        time.sleep(2)

    @staticmethod
    def adaptive_response(orchestrator: ShowOrchestrator, sentiment: float):
        """Demonstrate adaptive response to sentiment."""
        print(f"\n=== Adaptive Response (sentiment: {sentiment}) ===\n")

        # Update sentiment
        orchestrator.update_sentiment(sentiment)

        # Execute adaptive lighting and audio
        orchestrator.execute_adaptive_scene()
        orchestrator.execute_adaptive_audio()

        # Generate contextual dialogue
        if sentiment < -0.5:
            message = "We understand this may be difficult"
        elif sentiment < 0:
            message = "Thank you for your patience"
        elif sentiment < 0.5:
            message = "We're glad you're here with us"
        else:
            message = "Your wonderful energy makes this show special"

        # Translate to BSL
        orchestrator.execute_bsl_translation(message)

        time.sleep(3)

    @staticmethod
    def coordinated_scene_change(
        orchestrator: ShowOrchestrator,
        scene_name: str,
        audio_track: str,
        bsl_message: str
    ):
        """Coordinated scene change across all services."""
        print(f"\n=== Coordinated Scene: {scene_name} ===\n")

        # Create scene-specific lighting
        scenes = {
            "dramatic": LightingCue(
                "dramatic",
                {
                    "mh_1": {1: 150, 4: 255, 5: 50, 6: 50},
                    "mh_2": {1: 120, 4: 255, 5: 30, 6: 30}
                },
                2000
            ),
            "joyful": LightingCue(
                "joyful",
                {
                    "mh_1": {1: 240, 4: 255, 5: 255, 6: 150},
                    "mh_2": {1: 220, 4: 255, 5: 255, 6: 130}
                },
                1500
            ),
        }

        scene = scenes.get(scene_name, scenes["dramatic"])

        # Execute changes in parallel
        print("Executing coordinated changes...")
        orchestrator.dmx.create_scene(scene)
        orchestrator.dmx.activate_scene(scene.scene_name)
        orchestrator.audio.play_track(audio_track)
        orchestrator.execute_bsl_translation(bsl_message)

        print(f"✅ Scene '{scene_name}' activated")

    @staticmethod
    def emergency_drill(orchestrator: ShowOrchestrator):
        """Emergency response drill."""
        print("\n=== Emergency Drill ===\n")

        print("Simulating emergency situation...")

        # Activate emergency procedures
        orchestrator.emergency_shutdown_all()

        print("Waiting 3 seconds...")
        time.sleep(3)

        print("Resetting from emergency...")
        orchestrator.reset_all_emergencies()

        print("✅ Emergency drill complete")


# =============================================================================
# Main Examples
# =============================================================================

def example_basic_show():
    """Example 1: Basic show with all services."""
    print("\n" + "="*60)
    print("Example 1: Basic Show Integration")
    print("="*60 + "\n")

    orchestrator = ShowOrchestrator()
    orchestrator.start_show()

    try:
        # Welcome scene
        ExampleScenes.basic_welcome(orchestrator)

        # Adaptive responses
        print("\nDemonstrating adaptive responses:")
        sentiments = [-0.8, -0.3, 0.0, 0.5, 0.9]

        for sentiment in sentiments:
            ExampleScenes.adaptive_response(orchestrator, sentiment)
            time.sleep(1)

    finally:
        orchestrator.stop_show()


def example_adaptive_theatre():
    """Example 2: Adaptive theatre scenario."""
    print("\n" + "="*60)
    print("Example 2: Adaptive Theatre Scenario")
    print("="*60 + "\n")

    orchestrator = ShowOrchestrator()
    orchestrator.start_show()

    try:
        # Simulate show progression
        print("Act 1: Opening (neutral sentiment)")
        orchestrator.update_sentiment(0.0)
        orchestrator.execute_adaptive_scene()
        orchestrator.execute_adaptive_audio()
        orchestrator.execute_bsl_translation("Welcome to our performance")
        time.sleep(3)

        print("\nAct 2: Tension builds (negative sentiment)")
        orchestrator.update_sentiment(-0.6)
        orchestrator.execute_adaptive_scene()
        orchestrator.execute_adaptive_audio()
        orchestrator.execute_bsl_translation("The story takes a dramatic turn")
        time.sleep(3)

        print("\nAct 3: Resolution (positive sentiment)")
        orchestrator.update_sentiment(0.8)
        orchestrator.execute_adaptive_scene()
        orchestrator.execute_adaptive_audio()
        orchestrator.execute_bsl_translation("Together we find hope")
        time.sleep(3)

        print("\nFinale: Celebration (very positive)")
        orchestrator.update_sentiment(1.0)
        orchestrator.execute_adaptive_scene()
        orchestrator.execute_adaptive_audio()
        orchestrator.execute_bsl_translation("Thank you for joining us")
        time.sleep(3)

    finally:
        orchestrator.stop_show()


def example_coordinated_scenes():
    """Example 3: Coordinated scene changes."""
    print("\n" + "="*60)
    print("Example 3: Coordinated Scene Changes")
    print("="*60 + "\n")

    orchestrator = ShowOrchestrator()
    orchestrator.start_show()

    try:
        # Scene 1: Dramatic moment
        ExampleScenes.coordinated_scene_change(
            orchestrator,
            "dramatic",
            "dramatic_bgm",
            "The tension rises"
        )
        time.sleep(4)

        # Scene 2: Joyful resolution
        ExampleScenes.coordinated_scene_change(
            orchestrator,
            "joyful",
            "upbeat_bgm",
            "But hope remains"
        )
        time.sleep(4)

    finally:
        orchestrator.stop_show()


def example_emergency_procedures():
    """Example 4: Emergency procedures."""
    print("\n" + "="*60)
    print("Example 4: Emergency Procedures")
    print("="*60 + "\n")

    orchestrator = ShowOrchestrator()
    orchestrator.start_show()

    try:
        # Normal operation first
        print("Normal operation...")
        welcome_scene = LightingCue(
            "normal",
            {"mh_1": {1: 200, 4: 255, 5: 200, 6: 100}},
            1000
        )
        orchestrator.dmx.create_scene(welcome_scene)
        orchestrator.dmx.activate_scene("normal")
        orchestrator.audio.play_track("normal_bgm")
        time.sleep(2)

        # Emergency drill
        ExampleScenes.emergency_drill(orchestrator)

    finally:
        orchestrator.stop_show()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Project Chimera Phase 2 Integration Examples"
    )
    parser.add_argument(
        "--example",
        choices=["basic", "adaptive", "scenes", "emergency"],
        required=True,
        help="Example to run"
    )

    args = parser.parse_args()

    examples = {
        "basic": example_basic_show,
        "adaptive": example_adaptive_theatre,
        "scenes": example_coordinated_scenes,
        "emergency": example_emergency_procedures,
    }

    example_func = examples[args.example]
    example_func()


if __name__ == "__main__":
    main()
