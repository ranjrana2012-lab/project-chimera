"""Core handler for Safety Filter"""

import time
from typing import Dict, Any, List
from .layers.pattern_matcher import PatternMatcher
from .layers.classifier import Classifier
from .layers.rule_engine import RuleEngine
from .queue.review_queue import ReviewQueue


class SafetyHandler:
    def __init__(self, settings):
        self.settings = settings
        self.pattern_matcher = PatternMatcher()
        self.classifier = Classifier()
        self.rule_engine = RuleEngine()
        self.review_queue = ReviewQueue(max_size=settings.review_queue_size)

    async def initialize(self):
        await self.classifier.load_model()
        await self.rule_engine.load_rules(self.settings.policy_path)

    async def filter(self, content: str) -> Dict[str, Any]:
        """Apply safety filtering to content."""
        start_time = time.time()

        # Layer 1: Pattern matching
        pattern_result = await self.pattern_matcher.check(content)

        # Layer 2: Classification
        classification = await self.classifier.classify(content)

        # Layer 3: Rule engine
        rule_result = await self.rule_engine.evaluate(content)

        # Combine results
        decision = self._make_decision(pattern_result, classification, rule_result)

        result = {
            "decision": decision["action"],
            "category": decision.get("category"),
            "confidence": decision.get("confidence", 0.0),
            "details": {
                "patterns": pattern_result,
                "classification": classification,
                "rules": rule_result,
            },
            "latency_ms": (time.time() - start_time) * 1000,
        }

        # Queue for review if flagged
        if decision["action"] in ["flag", "review"]:
            await self.review_queue.add(content, result)

        return result

    def _make_decision(self, pattern_result, classification, rule_result) -> Dict[str, Any]:
        """Make final decision from all layers."""
        # If blocked by any layer
        if (pattern_result.get("action") == "block" or
            rule_result.get("action") == "block" or
            classification.get("harm_probability", 0) > 0.9):
            return {"action": "block", "category": "blocked", "confidence": 1.0}

        # If flagged by any layer
        if (pattern_result.get("action") in ["flag", "review"] or
            rule_result.get("action") in ["flag", "review"] or
            classification.get("harm_probability", 0) > 0.7):
            return {"action": "flag", "category": "flagged", "confidence": 0.8}

        # Otherwise allow
        return {"action": "allow", "category": "safe", "confidence": 0.95}

    async def get_review_queue(self) -> List[Dict[str, Any]]:
        """Get items in review queue."""
        return await self.review_queue.get_items()

    async def review_decision(self, item_id: str, decision: str) -> Dict[str, Any]:
        """Record review decision."""
        await self.review_queue.decide(item_id, decision)
        return {"success": True}

    async def close(self):
        await self.classifier.close()
