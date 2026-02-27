"""
Normal load test scenario for Project Chimera.

Simulates typical theatre platform usage patterns during a normal performance.
Target: 50 concurrent users, steady state load.
"""

from locust import HttpUser, task, between, constant
import random


class NormalTheatreAudience(HttpUser):
    """
    Simulates a typical theatre audience member during a performance.

    User behavior:
    - Sends occasional sentiment feedback
    - Triggers lighting/safety systems passively
    - Views captioning/BSL translation
    """

    # Constant wait time for realistic simulation
    wait_time = constant(2)
    host = "http://localhost:8000"

    @task(8)
    def send_audience_feedback(self):
        """
        Send audience sentiment feedback - most common action.

        Audience members react to the performance naturally.
        """
        feedback_texts = [
            "This is wonderful!",
            "Amazing performance!",
            "So emotional!",
            "Beautiful staging!",
            "Great acting!",
            "Love this scene!",
            "Powerful moment!",
            "Incredible show!",
        ]

        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "sentiment",
                "input": {
                    "text": random.choice(feedback_texts),
                    "options": {
                        "include_emotions": True,
                        "include_trend": False,
                    },
                },
            },
            timeout=2,
        )

    @task(3)
    def view_captioning(self):
        """View real-time captioning."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "captioning",
                "input": {
                    "action": "get_latest",
                },
            },
            timeout=2,
        )

    @task(2)
    def request_bsl_translation(self):
        """Request BSL sign language translation."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "bsl-text2gloss",
                "input": {
                    "text": "The performance continues in the next scene.",
                },
            },
            timeout=3,
        )

    @task(1)
    def check_performance_status(self):
        """Check overall performance/system status."""
        self.client.get("/health/ready", timeout=1)


class PerformanceAdaptationUser(HttpUser):
    """
    Simulates the AI performance adaptation system.

    Continuously monitors sentiment and adapts the performance.
    """

    wait_time = between(1, 2)
    host = "http://localhost:8000"

    @task(5)
    def analyze_audience_sentiment(self):
        """Analyze aggregate audience sentiment."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "sentiment",
                "input": {
                    "texts": [
                        "Great show!",
                        "Love it!",
                        "Amazing!",
                    ]
                },
            },
            timeout=3,
        )

    @task(3)
    def generate_adaptive_dialogue(self):
        """Generate dialogue based on sentiment."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "scenespeak",
                "input": {
                    "current_scene": {
                        "scene_id": "adaptive-scene",
                        "title": "AI-Adapted Scene",
                    },
                    "sentiment_vector": {
                        "overall": random.choice(["positive", "neutral"]),
                        "intensity": round(random.uniform(0.5, 0.9), 2),
                    },
                },
            },
            timeout=5,
        )

    @task(2)
    def safety_check_generated_content(self):
        """Check safety of generated content."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "safety-filter",
                "input": {
                    "content": "Sample generated content for safety check.",
                },
            },
            timeout=2,
        )


class LightingAutomationUser(HttpUser):
    """
    Simulates automated lighting control based on performance.

    """

    wait_time = between(5, 10)
    host = "http://localhost:8000"

    @task(3)
    def adjust_lighting_by_mood(self):
        """Adjust lighting based on scene mood."""
        moods = ["dramatic", "peaceful", "tense", "joyful", "mysterious"]

        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "lighting-control",
                "input": {
                    "action": "set_scene",
                    "zone": "stage-main",
                    "params": {
                        "scene": random.choice(moods),
                        "intensity": round(random.uniform(0.5, 1.0), 2),
                    },
                },
            },
            timeout=2,
        )

    @task(1)
    def get_lighting_status(self):
        """Check current lighting status."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "lighting-control",
                "input": {
                    "action": "get_status",
                },
            },
            timeout=2,
        )


class OperatorConsoleUser(HttpUser):
    """
    Simulates operator console monitoring.

    Operators monitor the system and intervene when necessary.
    """

    wait_time = between(10, 20)
    host = "http://localhost:8000"

    @task(5)
    def check_pending_approvals(self):
        """Check for pending safety approvals."""
        self.client.get(
            "/api/v1/console/alerts",
            timeout=3,
        )

    @task(2)
    def review_flagged_content(self):
        """Review flagged content."""
        self.client.get(
            "/api/v1/console/approvals/pending",
            timeout=3,
        )

    @task(1)
    def check_system_health(self):
        """Check overall system health."""
        self.client.get(
            "/health/detailed",
            timeout=2,
        )
