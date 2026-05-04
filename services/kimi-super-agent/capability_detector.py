"""Capability detection for Kimi K2.6 super-agent."""

import logging
import os
from typing import Dict, Any

try:
    from .proto import kimi_pb2
except ImportError:  # pragma: no cover - supports direct script execution
    from proto import kimi_pb2

CapabilityHint = kimi_pb2.CapabilityHint
MultimodalContent = kimi_pb2.MultimodalContent

logger = logging.getLogger(__name__)


class CapabilityDetector:
    """Detects required capabilities from user requests."""

    def __init__(self, long_context_threshold: int | None = None):
        self.long_context_threshold = (
            long_context_threshold
            if long_context_threshold is not None
            else int(os.getenv("KIMI_LONG_CONTEXT_THRESHOLD", "8000"))
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
        has_non_text = any(self._content_type(content) != "TEXT" for content in multimodal_content)
        if has_non_text:
            return CapabilityHint.MULTIMODAL

        # Check for long context
        if len(user_input) > self.long_context_threshold:
            return CapabilityHint.LONG_CONTEXT

        # Check for agentic coding patterns
        coding_keywords = [
            "generate code", "write a function", "implement",
            "debug", "refactor", "create a class", "create a new agent",
            "create an agent",
        ]
        if any(keyword in user_input.lower() for keyword in coding_keywords):
            return CapabilityHint.AGENTIC_CODING

        return CapabilityHint.NONE

    def _content_type(self, content: Any) -> str:
        if isinstance(content, dict):
            value = content.get("type", "TEXT")
        else:
            value = getattr(content, "type", "TEXT")

        if isinstance(value, int):
            try:
                return kimi_pb2.ContentType.Name(value)
            except ValueError:
                return "UNKNOWN"

        return str(value)
