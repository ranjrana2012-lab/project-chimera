"""Capability detection for Kimi K2.6 delegation."""

import re
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Use protobuf enum for consistency
from proto import kimi_pb2
CapabilityHint = kimi_pb2.CapabilityHint


@dataclass
class MultimodalContent:
    """Multimodal content data."""
    type: str
    data: bytes
    mime_type: str
    metadata: Dict[str, str] = None


class CapabilityDetector:
    """Detects when a request requires Kimi K2.6 capabilities."""

    # Patterns for agentic coding requests
    AGENTIC_CODING_PATTERNS = [
        r"create\s+(a\s+)?(new\s+)?agent",
        r"build\s+(a\s+)?agent",
        r"generate\s+(a\s+)?agent",
        r"write\s+(a\s+)?script",
        r"implement\s+(a\s+)?function",
        r"add\s+(a\s+)?feature",
        r"modify\s+(the\s+)?behavior",
    ]

    def __init__(
        self,
        long_context_threshold: int = None,
        enable_multimodal: bool = None,
        enable_agentic_coding: bool = None,
    ):
        self.long_context_threshold = long_context_threshold or int(
            os.getenv("KIMI_LONG_CONTEXT_THRESHOLD", "8192")
        )
        self.enable_multimodal = enable_multimodal if enable_multimodal is not None else \
            os.getenv("KIMI_ENABLE_MULTIMODAL", "true").lower() == "true"
        self.enable_agentic_coding = enable_agentic_coding if enable_agentic_coding is not None else \
            os.getenv("KIMI_ENABLE_AGENTIC_CODING", "true").lower() == "true"

        # Compile regex patterns
        self.coding_patterns = [re.compile(p, re.IGNORECASE) for p in self.AGENTIC_CODING_PATTERNS]

    def detect(self, request: Dict[str, Any]) -> kimi_pb2.CapabilityHint:
        """Detect required capability for a request.

        Args:
            request: Request dict with user_input and multimodal_content

        Returns:
            CapabilityHint indicating required capability
        """
        user_input = request.get("user_input", "")
        multimodal_content = request.get("multimodal_content", [])

        # Check multimodal (highest priority)
        if self.enable_multimodal and self._has_multimodal(multimodal_content):
            return CapabilityHint.MULTIMODAL

        # Check agentic coding
        if self.enable_agentic_coding and self._is_agentic_coding(user_input):
            return CapabilityHint.AGENTIC_CODING

        # Check long context
        if self._is_long_context(user_input, multimodal_content):
            return CapabilityHint.LONG_CONTEXT

        return CapabilityHint.NONE

    def _has_multimodal(self, content: List[Any]) -> bool:
        """Check if request has multimodal content."""
        if not content:
            return False

        for item in content:
            if isinstance(item, dict):
                content_type = item.get("type", "")
            elif hasattr(item, "type"):
                content_type = item.type
            else:
                continue

            if content_type in ("IMAGE", "VIDEO", "AUDIO"):
                return True

        return False

    def _is_agentic_coding(self, text: str) -> bool:
        """Check if request is for agentic coding."""
        for pattern in self.coding_patterns:
            if pattern.search(text):
                return True
        return False

    def _is_long_context(self, text: str, content: List[Any]) -> bool:
        """Check if request requires long context processing."""
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(text) // 4

        # Add tokens for multimodal content (video is expensive)
        for item in content:
            if isinstance(item, dict):
                content_type = item.get("type", "")
            elif hasattr(item, "type"):
                content_type = item.type
            else:
                continue

            if content_type == "VIDEO":
                estimated_tokens += 10000  # Video processing is expensive
            elif content_type in ("IMAGE", "AUDIO"):
                estimated_tokens += 1000

        return estimated_tokens > self.long_context_threshold
