"""Token tracking and cost monitoring for LLM usage."""
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TokenBudget:
    """
    Token budget configuration.

    Defines budget limits and pricing for different LLM backends.
    """

    # Default costs per 1000 tokens (in USD)
    DEFAULT_COSTS_PER_1K = {
        "local_llm": 0.0,      # Free (local)
        "openai": 0.002,       # ~$0.002 per 1K (GPT-4o-mini)
        "anthropic": 0.003,    # ~$0.003 per 1K (Claude Haiku)
        "gpt-4o": 0.005,       # ~$0.005 per 1K (GPT-4o)
        "gpt-4o-mini": 0.00015,  # ~$0.00015 per 1K (GPT-4o-mini)
    }

    def __init__(
        self,
        max_tokens: int = 100000,
        alert_threshold: float = 0.8,
        cost_per_1k_tokens: Optional[Dict[str, float]] = None
    ):
        """
        Initialize token budget configuration.

        Args:
            max_tokens: Maximum number of tokens allowed
            alert_threshold: Fraction of budget at which to alert (0.0-1.0)
            cost_per_1k_tokens: Optional custom pricing per backend
        """
        self.max_tokens = max_tokens
        self.alert_threshold = alert_threshold
        self.cost_per_1k_tokens = cost_per_1k_tokens or self.DEFAULT_COSTS_PER_1K.copy()


class TokenTracker:
    """
    Track token usage and enforce budget limits.

    Monitors token consumption across different LLM backends
    and provides cost estimates for operations.
    """

    def __init__(self, budget: Optional[TokenBudget] = None):
        """
        Initialize the token tracker.

        Args:
            budget: Optional TokenBudget configuration. If None, uses default.
        """
        self.budget = budget or TokenBudget()
        self.tokens_used = 0
        self.local_tokens = 0
        self.api_tokens = 0
        self.usage_by_operation: Dict[str, int] = {}
        self.usage_by_backend: Dict[str, int] = {}

        # Calculate alert threshold in tokens
        self.alert_threshold_tokens = int(self.budget.max_tokens * self.budget.alert_threshold)

    def track_tokens(
        self,
        token_count: int,
        backend: str,
        operation: str
    ) -> None:
        """
        Track token usage for an operation.

        Args:
            token_count: Number of tokens used
            backend: LLM backend (local_llm, openai, anthropic, etc.)
            operation: Operation name (e.g., "agent_decision_round_1")
        """
        if token_count < 0:
            logger.warning(f"Negative token count: {token_count}")
            return

        self.tokens_used += token_count

        # Track by backend type
        if backend == "local_llm":
            self.local_tokens += token_count
        else:
            self.api_tokens += token_count

        self.usage_by_backend[backend] = (
            self.usage_by_backend.get(backend, 0) + token_count
        )

        # Track by operation
        self.usage_by_operation[operation] = (
            self.usage_by_operation.get(operation, 0) + token_count
        )

        logger.info(
            f"Token usage: {token_count} from {backend} for {operation}. "
            f"Total: {self.tokens_used}/{self.budget.max_tokens} "
            f"({self.tokens_used / self.budget.max_tokens * 100:.1f}%)"
        )

    def get_stats(self) -> Dict[str, any]:
        """
        Get current token usage statistics.

        Returns:
            Dictionary with usage statistics and cost estimates
        """
        # Calculate estimated cost
        cost = self._calculate_total_cost()

        return {
            "total_tokens": self.tokens_used,
            "local_tokens": self.local_tokens,
            "api_tokens": self.api_tokens,
            "tokens_remaining": self.budget.max_tokens - self.tokens_used,
            "budget_utilization": self.tokens_used / self.budget.max_tokens,
            "estimated_cost_usd": round(cost, 6),
            "usage_by_operation": self.usage_by_operation.copy(),
            "usage_by_backend": self.usage_by_backend.copy(),
            "is_near_limit": self.is_near_limit(),
            "is_over_budget": self.is_over_budget()
        }

    async def check_budget(self, required_tokens: int) -> bool:
        """
        Check if operation is within budget.

        Args:
            required_tokens: Number of tokens required for operation

        Returns:
            True if operation is within budget, False otherwise
        """
        if required_tokens < 0:
            logger.warning(f"Negative required tokens: {required_tokens}")
            return False

        return (self.tokens_used + required_tokens) <= self.budget.max_tokens

    def is_near_limit(self) -> bool:
        """
        Check if approaching budget alert threshold.

        Returns:
            True if at or above alert threshold
        """
        return self.tokens_used >= self.alert_threshold_tokens

    def is_over_budget(self) -> bool:
        """
        Check if budget has been exceeded.

        Returns:
            True if over budget
        """
        return self.tokens_used > self.budget.max_tokens

    def get_cost_estimate(self, tokens: int, backend: str) -> float:
        """
        Get estimated cost for token usage.

        Args:
            tokens: Number of tokens
            backend: LLM backend name

        Returns:
            Estimated cost in USD
        """
        cost_per_1k = self.budget.cost_per_1k_tokens.get(backend, 0.002)
        return (tokens * cost_per_1k) / 1000

    def _calculate_total_cost(self) -> float:
        """
        Calculate total cost from all tracked token usage.

        Returns:
            Total cost in USD
        """
        total_cost = 0.0

        for backend, tokens in self.usage_by_backend.items():
            cost_per_1k = self.budget.cost_per_1k_tokens.get(backend, 0.002)
            total_cost += (tokens * cost_per_1k) / 1000

        return total_cost

    def reset(self) -> None:
        """Reset all tracking counters."""
        self.tokens_used = 0
        self.local_tokens = 0
        self.api_tokens = 0
        self.usage_by_operation = {}
        self.usage_by_backend = {}
        logger.info("Token tracker reset")

    def get_usage_report(self) -> str:
        """
        Generate a human-readable usage report.

        Returns:
            Formatted usage report string
        """
        stats = self.get_stats()

        report_lines = [
            "Token Usage Report",
            "=" * 50,
            f"Total tokens used: {stats['total_tokens']:,}",
            f"Local tokens: {stats['local_tokens']:,}",
            f"API tokens: {stats['api_tokens']:,}",
            f"Tokens remaining: {stats['tokens_remaining']:,}",
            f"Budget utilization: {stats['budget_utilization'] * 100:.1f}%",
            f"Estimated cost: ${stats['estimated_cost_usd']:.6f}",
            "",
            "Usage by backend:"
        ]

        for backend, tokens in stats['usage_by_backend'].items():
            cost = self.get_cost_estimate(tokens, backend)
            report_lines.append(f"  {backend}: {tokens:,} tokens (${cost:.6f})")

        if stats['usage_by_operation']:
            report_lines.append("")
            report_lines.append("Top operations by token usage:")

            sorted_ops = sorted(
                stats['usage_by_operation'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            for op, tokens in sorted_ops:
                report_lines.append(f"  {op}: {tokens:,} tokens")

        return "\n".join(report_lines)
