"""Capability detection for Kimi K2.6 super-agent."""

import logging
import os
from typing import Dict, Any

# Use protobuf enum for consistency
from proto import kimi_pb2
CapabilityHint = kimi_pb2.CapabilityHint

logger = logging.getLogger(__name__)


class CapabilityDetector:
    """Detects required capabilities from user requests."""

    def __init__(self):
        self.long_context_threshold = int(
            os.getenv("KIMI_LONG_CONTEXT_THRESHOLD", "8000")
        )
        logger.info("CapabilityDetector initialized")

    def detect(self, request: Dict[str, Any]) -> kimi_pb2.CapabilityHint:
        """
        Detect required capability from request.

        Args:
            request: Internal request format with user_input and multimodal_content

        Returns:
            Detected capability hint
        """
        user_input = request.get("user_input", "")
        multimodal_content = request.get("multimodal_content", [])

        # Check for multimodal content
        has_non_text = any(
            content.get("type") != "TEXT"
            for content in multimodal_content
        )
        if has_non_text:
            return CapabilityHint.MULTIMODAL

        # Check for long context
        if len(user_input) > self.long_context_threshold:
            return CapabilityHint.LONG_CONTEXT

        # Check for agentic coding patterns
        coding_keywords = [
            "generate code", "write a function", "implement",
            "debug", "refactor", "create a class"
        ]
        if any(keyword in user_input.lower() for keyword in coding_keywords):
            return CapabilityHint.AGENTIC_CODING

        return CapabilityHint.NONE
