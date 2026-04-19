# Project Chimera - Load Testing Script

from locust import HttpUser, task, between, events
from datetime import datetime

class ChimeraUser(HttpUser):
    """Simulated user for Project Chimera load testing."""

    wait_time = between(1, 3)

    def on_start(self):
        """Run on start - verifies service availability."""
        self.client.get("/")
        events.request_name.fire("health_check")

    @task(3)
    def health_check(self):
        """Basic health check - most frequent operation."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                events.request.fire("health_check_failed")
                response.failure()

    @task(2)
    def orchestrate_simple(self):
        """Simple orchestration without ML agents."""
        with self.client.post(
            "/api/orchestrate",
            json={
                "prompt": "Load test message",
                "show_id": f"load_test_{self.user_id}",
                "enable_sentiment": False,
                "enable_safety": False
            },
            catch_response=True
        ) as response:
            if response.status_code not in [200, 503]:
                events.request.fire("orchestrate_failed")
                response.failure()

    @task(1)
    def orchestrate_full(self):
        """Full orchestration with all agents - heavier load."""
        with self.client.post(
            "/api/orchestrate",
            json={
                "prompt": "Full load test with all agents",
                "show_id": f"load_test_full_{self.user_id}",
                "enable_sentiment": True,
                "enable_safety": True,
                "enable_translation": False
            },
            timeout=30.0,
            catch_response=True
        ) as response:
            if response.status_code not in [200, 503]:
                events.request.fire("full_orchestrate_failed")
                response.failure()

    @task(1)
    def sentiment_analysis(self):
        """Sentiment analysis endpoint."""
        with self.client.post(
            "http://localhost:8004/api/analyze",
            json={
                "text": "This is a load test message",
            },
            catch_response=True
        ) as response:
            if response.status_code not in [200, 503]:
                events.request.fire("sentiment_failed")
                response.failure()
