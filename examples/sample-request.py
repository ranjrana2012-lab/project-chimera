#!/usr/bin/env python3
"""
Project Chimera Sample API Requests

This script demonstrates how to interact with all Project Chimera services.
Run this during the demo to show the AI capabilities.
"""

import requests
import json
import sys
from typing import Any, Dict


class ChimeraClient:
    """Client for interacting with Project Chimera services"""

    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.ports = {
            "orchestrator": 8000,
            "scenespeak": 8001,
            "captioning": 8002,
            "bsl": 8003,
            "sentiment": 8004,
            "lsm": 8005,
            "safety": 8006,
            "console": 8007,
        }

    def _make_request(
        self, service: str, endpoint: str, method: str = "GET", data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make a request to a Chimera service"""
        url = f"{self.base_url}:{self.ports[service]}{endpoint}"
        headers = {"Content-Type": "application/json"}

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def check_health(self, service: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        return self._make_request(service, "/health/live")

    def generate_dialogue(self, prompt: str, style: str = "dramatic") -> Dict[str, Any]:
        """Generate dialogue using SceneSpeak via orchestrator"""
        payload = {
            "skill": "dialogue_generator",
            "input": {"prompt": prompt, "style": style},
        }
        return self._make_request("orchestrator", "/v1/orchestrate", "POST", payload)

    def transcribe_audio(self, audio_data: str = None) -> Dict[str, Any]:
        """Transcribe audio (demo mode with text input)"""
        payload = {
            "text": "Hello and welcome to Project Chimera, the future of accessible theatre.",
            "language": "en",
        }
        return self._make_request("captioning", "/v1/transcribe", "POST", payload)

    def translate_to_bsl(self, text: str) -> Dict[str, Any]:
        """Translate text to BSL gloss"""
        payload = {
            "text": text,
            "source_language": "en",
            "target_format": "gloss",
        }
        return self._make_request("bsl", "/v1/translate", "POST", payload)

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        payload = {"text": text}
        return self._make_request("sentiment", "/v1/analyze", "POST", payload)

    def match_style(self, text: str, target_style: str) -> Dict[str, Any]:
        """Match text to a specific style using LSM"""
        payload = {"text": text, "target_style": target_style}
        return self._make_request("lsm", "/v1/match", "POST", payload)

    def check_safety(self, text: str, policy: str = "family") -> Dict[str, Any]:
        """Check if text is safe according to policy"""
        payload = {"text": text, "policy": policy}
        return self._make_request("safety", "/v1/check", "POST", payload)


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(service: str, result: Dict[str, Any]):
    """Print request result"""
    print(f"\n{service}:")
    print(json.dumps(result, indent=2))


def main():
    """Run sample requests for demo"""

    client = ChimeraClient()

    print("🎭 Project Chimera Demo - Sample API Requests")
    print("Make sure all services are running first!")
    print("Run: ./scripts/demo-start.sh")

    # Check all services first
    print_section("Step 1: Service Health Checks")
    all_healthy = True
    for service in client.ports.keys():
        result = client.check_health(service)
        status = result.get("status", "unknown")
        emoji = "✅" if status == "healthy" else "❌"
        print(f"  {emoji} {service.capitalize()}: {status}")
        if status != "healthy":
            all_healthy = False

    if not all_healthy:
        print("\n⚠️  Some services are not healthy. Continue anyway? (y/n)")
        if input().lower() != "y":
            sys.exit(1)

    # Generate dialogue
    print_section("Step 2: Generate Theatre Dialogue")
    result = client.generate_dialogue(
        prompt="A dramatic monologue about discovering a hidden letter",
        style="dramatic",
    )
    print_result("SceneSpeak Dialogue Generation", result)

    # Analyze sentiment
    print_section("Step 3: Sentiment Analysis")
    result = client.analyze_sentiment("I absolutely love this amazing platform!")
    print_result("Sentiment Analysis (Positive)", result)

    result = client.analyze_sentiment("This is terrible and I want my money back!")
    print_result("Sentiment Analysis (Negative)", result)

    # Translate to BSL
    print_section("Step 4: British Sign Language Translation")
    result = client.translate_to_bsl("Welcome to the theatre. Please enjoy the show!")
    print_result("BSL Translation", result)

    # Check safety
    print_section("Step 5: Safety Filter")
    result = client.check_safety("Hello and welcome to our wonderful show!", "family")
    print_result("Safety Check (Safe)", result)

    # Match style
    print_section("Step 6: Language Style Matching")
    result = client.match_style(
        "The quick brown fox jumps over the lazy dog.",
        "shakespearean",
    )
    print_result("Style Matching", result)

    # Captioning demo
    print_section("Step 7: Live Captioning")
    result = client.transcribe_audio()
    print_result("Captioning Service", result)

    # Full orchestration demo
    print_section("Step 8: Full Pipeline (Orchestration)")
    result = client.generate_dialogue(
        prompt="The hero discovers their true identity",
        style="epic",
    )
    print_result("Full Orchestration Flow", result)

    print_section("Demo Complete!")
    print("\nAll sample requests completed successfully.")
    print("\nFor more examples, see:")
    print("  - docs/demo/demo-script.md")
    print("  - examples/demo-scenario.json")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
