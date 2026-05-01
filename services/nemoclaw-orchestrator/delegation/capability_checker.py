"""Capability checking for Nemo Claw delegation."""

import os
from typing import Dict, Any, Optional


class NemoCapabilityChecker:
    """Checks if requests should be delegated to Kimi."""

    def __init__(self):
        self.kimi_enabled = os.getenv("KIMI_DELEGATION_ENABLED", "true").lower() == "true"
        self.long_context_threshold = int(os.getenv("KIMI_LONG_CONTEXT_THRESHOLD", "8192"))

    def should_delegate(self, request: Dict[str, Any]) -> bool:
        """Determine if request should be delegated to Kimi.

        Args:
            request: Request dict to evaluate

        Returns:
            True if should delegate, False otherwise
        """
        if not self.kimi_enabled:
            return False

        # Check for explicit delegation hint
        hint = request.get("capability_hint")
        if hint and hint in ("LONG_CONTEXT", "MULTIMODAL", "AGENTIC_CODING"):
            return True

        # Check token count
        user_input = request.get("user_input", "")
        estimated_tokens = len(user_input) // 4

        if estimated_tokens > self.long_context_threshold:
            return True

        # Check for multimodal content
        multimodal = request.get("multimodal_content", [])
        if multimodal:
            return True

        # Check for agentic coding keywords
        coding_keywords = [
            "agent", "script", "function", "implement", "feature"
        ]
        user_lower = user_input.lower()
        if any(keyword in user_lower for keyword in coding_keywords):
            return True

        return False
