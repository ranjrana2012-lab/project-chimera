"""Load tests using Locust"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time


class ChimeraUser(HttpUser):
    """Simulated user for Project Chimera load testing."""

    wait_time = between(1, 3)
    host = "http://openclaw-orchestrator:8000"

    @task(3)
    def invoke_scenespeak(self):
        """Invoke SceneSpeak skill."""
        self.client.post(
            "/api/v1/orchestration/invoke",
            json={
                "skill_name": "scenespeak",
                "input": {
                    "current_scene": {"title": "Load Test Scene"},
                    "dialogue_context": [],
                },
                "timeout_ms": 3000,
            },
        )

    @task(2)
    def invoke_sentiment(self):
        """Invoke Sentiment skill."""
        self.client.post(
            "/api/v1/orchestration/invoke",
            json={
                "skill_name": "sentiment",
                "input": {"text": "This is a load test message!"},
                "timeout_ms": 500,
            },
        )

    @task(1)
    def invoke_lighting(self):
        """Invoke Lighting skill."""
        self.client.post(
            "/api/v1/orchestration/invoke",
            json={
                "skill_name": "lighting-control",
                "input": {
                    "action": "get_status",
                },
                "timeout_ms": 200,
            },
        )

    @task(1)
    def list_skills(self):
        """List available skills."""
        self.client.get("/api/v1/skills")


# Custom event handlers for detailed metrics
def on_request(request_type, name, response_time, response_length, **kwargs):
    """Custom request event handler."""
    events.request.fire(
        request_type=request_type,
        name=name,
        response_time=response_time,
        response_length=response_length,
        **kwargs,
    )
