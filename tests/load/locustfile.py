"""
Load tests using Locust for Project Chimera.

Tests the system under load with multiple concurrent users.
Target: 100 concurrent users, 1000 requests total.
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time
import random
from typing import Dict, Any


class ChimeraUser(HttpUser):
    """
    Simulated user for Project Chimera load testing.

    Models realistic theatre platform usage patterns:
    - Frequent sentiment analysis (audience feedback)
    - Regular dialogue generation (AI performance)
    - Occasional safety checks
    - Infrequent BSL translation
    """

    # Wait between tasks (1-3 seconds to simulate realistic pacing)
    wait_time = between(1, 3)

    # Base host - override with --host when running Locust
    host = "http://localhost:8000"

    def on_start(self):
        """Called when a user starts. Perform any initialization."""
        # Could do warmup requests here
        pass

    @task(5)
    def analyze_sentiment(self):
        """
        Analyze audience sentiment - most frequent operation.

        Weight: 5 (highest priority)
        This represents real-time audience feedback analysis.
        """
        sample_texts = [
            "The performance is absolutely amazing!",
            "I'm really enjoying this show so far.",
            "The actors are incredibly talented.",
            "What a wonderful experience!",
            "This is the best theatre performance I've seen.",
            "Great staging and lighting effects.",
            "The dialogue is very engaging.",
            "Emotional and powerful performance.",
            "Outstanding production quality.",
            "Beautiful set design and costumes.",
        ]

        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "sentiment",
                "input": {
                    "text": random.choice(sample_texts),
                },
                "config": {
                    "timeout_ms": 1000,
                },
            },
            catch_response=True,
            name="/api/v1/orchestrate [sentiment]",
        )

        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            if "output" not in data and "status" not in data:
                response.failure("Invalid response structure")
            else:
                response.success()
        elif response.status_code == 503:
            # Service unavailable - acceptable under load
            response.failure("Service unavailable")
        else:
            response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def generate_dialogue(self):
        """
        Generate AI dialogue - frequent operation.

        Weight: 3 (medium priority)
        This represents AI-driven performance adaptation.
        """
        scene_contexts = [
            {"scene_id": "scene-001", "title": "Opening", "mood": "dramatic"},
            {"scene_id": "scene-002", "title": "Conflict", "mood": "tense"},
            {"scene_id": "scene-003", "title": "Resolution", "mood": "peaceful"},
            {"scene_id": "scene-004", "title": "Finale", "mood": "triumphant"},
        ]

        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "scenespeak",
                "input": {
                    "current_scene": random.choice(scene_contexts),
                    "dialogue_context": [],
                    "sentiment_vector": {
                        "overall": random.choice(["positive", "neutral", "negative"]),
                        "intensity": round(random.uniform(0.3, 0.9), 2),
                    },
                },
                "config": {
                    "timeout_ms": 5000,
                },
            },
            catch_response=True,
            name="/api/v1/orchestrate [scenespeak]",
        )

        if response.status_code == 200:
            data = response.json()
            if "output" not in data:
                response.failure("Missing output in response")
            else:
                # Check latency for performance metrics
                latency = data.get("latency_ms", 0)
                if latency > 10000:  # 10 second threshold
                    response.failure(f"High latency: {latency}ms")
                else:
                    response.success()
        else:
            response.failure(f"Status: {response.status_code}")

    @task(2)
    def check_safety(self):
        """
        Check content safety - moderate frequency.

        Weight: 2 (lower priority)
        This represents safety filtering for generated content.
        """
        safe_contents = [
            "Welcome to our performance today.",
            "The actors are now taking the stage.",
            "Please enjoy the show.",
            "Thank you for your attention.",
        ]

        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "safety-filter",
                "input": {
                    "content": random.choice(safe_contents),
                },
                "config": {
                    "timeout_ms": 500,
                },
            },
            catch_response=True,
            name="/api/v1/orchestrate [safety]",
        )

        if response.status_code == 200:
            data = response.json()
            if "output" not in data:
                response.failure("Missing output")
            else:
                output = data["output"]
                if "decision" not in output and "safe" not in output:
                    response.failure("Invalid safety response")
                else:
                    response.success()
        else:
            response.failure(f"Status: {response.status_code}")

    @task(1)
    def list_available_skills(self):
        """
        List available skills - low frequency operation.

        Weight: 1 (lowest priority)
        This represents UI/dashboard queries.
        """
        response = self.client.get(
            "/api/v1/skills",
            catch_response=True,
            name="/api/v1/skills",
        )

        if response.status_code == 200:
            data = response.json()
            skills = data if isinstance(data, list) else data.get("skills", [])
            if len(skills) == 0:
                response.failure("No skills returned")
            else:
                response.success()
        else:
            response.failure(f"Status: {response.status_code}")

    @task(1)
    def translate_to_bsl(self):
        """
        Translate to BSL gloss - low frequency operation.

        Weight: 1 (specialized feature)
        This represents accessibility features.
        """
        texts = [
            "Hello and welcome.",
            "The show is starting now.",
            "Please sit back and enjoy.",
            "Thank you for coming.",
        ]

        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "bsl-text2gloss",
                "input": {
                    "text": random.choice(texts),
                    "format": "gloss",
                },
                "config": {
                    "timeout_ms": 2000,
                },
            },
            catch_response=True,
            name="/api/v1/orchestrate [bsl]",
        )

        # BSL service might not be available
        if response.status_code in [200, 503]:
            if response.status_code == 200:
                response.success()
            else:
                # Service unavailable is acceptable for optional features
                response.success()
        else:
            response.failure(f"Status: {response.status_code}")

    @task(1)
    def check_lighting_status(self):
        """
        Check lighting control status - low frequency.

        Weight: 1 (infrequent operation)
        This represents IoT device status checks.
        """
        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "lighting-control",
                "input": {
                    "action": "get_status",
                    "zone": "stage-main",
                },
                "config": {
                    "timeout_ms": 500,
                },
            },
            catch_response=True,
            name="/api/v1/orchestrate [lighting]",
        )

        # Accept various status codes
        if response.status_code in [200, 503]:
            response.success()
        else:
            response.failure(f"Status: {response.status_code}")

    @task(2)
    def health_check(self):
        """
        Perform health checks - moderate frequency.

        Weight: 2 (monitoring)
        This represents monitoring/probe traffic.
        """
        response = self.client.get(
            "/health/live",
            catch_response=True,
            name="/health/live",
        )

        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Health check failed: {response.status_code}")


class CacheHitUser(HttpUser):
    """
    User specifically testing cache performance.

    This user class tests cache hit/miss ratios
    by making repeated identical requests.
    """

    wait_time = between(0.5, 1)
    host = "http://localhost:8000"

    # Fixed request data for testing cache hits
    CACHED_SENTIMENT = "This is a test message for cache performance testing."
    CACHED_SCENE = {
        "scene_id": "scene-cache-test",
        "title": "Cache Test Scene",
        "mood": "neutral",
    }

    @task(10)
    def cached_sentiment_request(self):
        """Request that should hit cache after first call."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "sentiment",
                "input": {"text": self.CACHED_SENTIMENT},
                "config": {"use_cache": True},
            },
            name="[CACHE] sentiment (cached)",
        )

    @task(5)
    def cached_dialogue_request(self):
        """Request that should hit cache after first call."""
        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "scenespeak",
                "input": {
                    "current_scene": self.CACHED_SCENE,
                    "dialogue_context": [],
                },
                "config": {"use_cache": True},
            },
            name="[CACHE] dialogue (cached)",
        )

    @task(1)
    def uncached_request(self):
        """Request that should always be a cache miss."""
        import time

        self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "sentiment",
                "input": {
                    "text": f"Unique message {time.time()} {random.randint(1000, 9999)}"
                },
                "config": {"use_cache": True},
            },
            name="[CACHE] sentiment (miss)",
        )


class HighLatencyUser(HttpUser):
    """
    User testing high-latency operations.

    Focuses on operations that take longer (dialogue generation,
    BSL translation) to test system behavior under stress.
    """

    wait_time = between(3, 5)
    host = "http://localhost:8000"

    @task(5)
    def complex_dialogue_generation(self):
        """Generate complex dialogue with full context."""
        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "scenespeak",
                "input": {
                    "current_scene": {
                        "scene_id": "complex-scene",
                        "title": "Complex Scene",
                        "characters": ["CHAR_A", "CHAR_B", "CHAR_C"],
                        "setting": "Detailed setting description here",
                        "mood": "dramatic",
                    },
                    "dialogue_context": [
                        {
                            "character": "CHAR_A",
                            "text": "Previous dialogue line one",
                            "timestamp": "2026-02-27T10:00:00Z",
                        },
                        {
                            "character": "CHAR_B",
                            "text": "Previous dialogue line two",
                            "timestamp": "2026-02-27T10:00:05Z",
                        },
                    ],
                    "sentiment_vector": {
                        "overall": "positive",
                        "intensity": 0.8,
                        "engagement": 0.9,
                    },
                },
                "config": {
                    "timeout_ms": 10000,
                    "max_tokens": 200,
                },
            },
            catch_response=True,
            name="[SLOW] complex dialogue",
        )

        if response.status_code == 200:
            data = response.json()
            latency = data.get("latency_ms", 0)
            events.request.fire(
                request_type="POST",
                name="[SLOW] complex dialogue latency",
                response_time=latency,
                response_length=len(str(data)),
                context={},
            )
            response.success()
        else:
            response.failure(f"Status: {response.status_code}")

    @task(2)
    def batch_sentiment_analysis(self):
        """Perform batch sentiment analysis."""
        texts = [f"Sample text {i}" for i in range(10)]

        response = self.client.post(
            "/api/v1/orchestrate",
            json={
                "skill_name": "sentiment",
                "input": {"texts": texts},
                "config": {"timeout_ms": 5000},
            },
            catch_response=True,
            name="[SLOW] batch sentiment",
        )

        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Status: {response.status_code}")


# Event handlers for metrics and reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, **kwargs):
    """
    Custom request event handler for detailed metrics.

    Tracks:
    - Response times by endpoint
    - Cache performance
    - Error rates
    """
    # Log slow requests
    if response_time > 5000:  # 5 seconds
        print(f"Slow request: {name} took {response_time}ms")

    # Could send to external monitoring system here


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print(f"Starting load test with {environment.target_user_count} users")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print(f"Load test completed. Processed {environment.stats.total.num_requests} requests")

    # Print summary statistics
    stats = environment.stats
    print(f"\n=== Load Test Summary ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failure rate: {stats.total.fail_ratio:.2%}")
    print(f"Average response time: {stats.total.avg_response_time:.0f}ms")
    print(f"Median response time: {stats.total.median_response_time:.0f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")


# Custom command-line arguments for Locust
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize Locust with custom settings."""
    # Could add custom arguments here
    pass
