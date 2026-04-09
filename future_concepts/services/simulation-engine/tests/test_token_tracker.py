"""Tests for token tracking and cost monitoring."""
import pytest
from cost.token_tracker import TokenBudget, TokenTracker


def test_token_budget_defaults():
    """Test that TokenBudget has sensible defaults."""
    budget = TokenBudget()

    assert budget.max_tokens == 100000
    assert budget.alert_threshold == 0.8
    assert "local_llm" in budget.cost_per_1k_tokens
    assert budget.cost_per_1k_tokens["local_llm"] == 0.0


def test_token_budget_custom():
    """Test creating a custom TokenBudget."""
    budget = TokenBudget(
        max_tokens=50000,
        alert_threshold=0.9,
        cost_per_1k_tokens={"local_llm": 0.0, "openai": 0.005}
    )

    assert budget.max_tokens == 50000
    assert budget.alert_threshold == 0.9
    assert budget.cost_per_1k_tokens["openai"] == 0.005


def test_token_tracker_initialization():
    """Test that TokenTracker initializes correctly."""
    tracker = TokenTracker()

    assert tracker.tokens_used == 0
    assert tracker.local_tokens == 0
    assert tracker.api_tokens == 0
    assert tracker.budget.max_tokens == 100000


def test_track_tokens():
    """Test that token usage is tracked correctly."""
    tracker = TokenTracker(budget=TokenBudget(max_tokens=100000))

    # Track some tokens
    tracker.track_tokens(1000, "local_llm", "test_operation")
    tracker.track_tokens(5000, "openai", "test_generation")

    stats = tracker.get_stats()

    assert stats["total_tokens"] == 6000
    assert stats["local_tokens"] == 1000
    assert stats["api_tokens"] == 5000
    assert stats["estimated_cost_usd"] > 0


def test_backend_classification():
    """Test that backends are correctly classified as local or API."""
    tracker = TokenTracker()

    tracker.track_tokens(1000, "local_llm", "test1")
    tracker.track_tokens(1000, "openai", "test2")
    tracker.track_tokens(1000, "anthropic", "test3")

    assert tracker.local_tokens == 1000
    assert tracker.api_tokens == 2000


def test_operation_tracking():
    """Test tracking by operation name."""
    tracker = TokenTracker()

    tracker.track_tokens(1000, "local_llm", "operation_a")
    tracker.track_tokens(500, "local_llm", "operation_a")
    tracker.track_tokens(2000, "openai", "operation_b")

    stats = tracker.get_stats()

    assert stats["usage_by_operation"]["operation_a"] == 1500
    assert stats["usage_by_operation"]["operation_b"] == 2000


def test_backend_tracking():
    """Test tracking by backend."""
    tracker = TokenTracker()

    tracker.track_tokens(1000, "openai", "op1")
    tracker.track_tokens(500, "openai", "op2")
    tracker.track_tokens(2000, "anthropic", "op3")

    stats = tracker.get_stats()

    assert stats["usage_by_backend"]["openai"] == 1500
    assert stats["usage_by_backend"]["anthropic"] == 2000


@pytest.mark.asyncio
async def test_budget_enforcement():
    """Test that budget limits are enforced."""
    tracker = TokenTracker(budget=TokenBudget(max_tokens=1000))

    # Should be within budget
    assert await tracker.check_budget(500) == True

    # Should exceed budget
    assert await tracker.check_budget(2000) == False


def test_is_near_limit():
    """Test near-limit detection."""
    budget = TokenBudget(max_tokens=1000, alert_threshold=0.8)
    tracker = TokenTracker(budget=budget)

    # Not near limit
    tracker.track_tokens(700, "local_llm", "test")
    assert not tracker.is_near_limit()

    # At limit (800 tokens = 80%)
    tracker.track_tokens(100, "local_llm", "test")
    assert tracker.is_near_limit()


def test_budget_alert_threshold():
    """Test budget alert triggers at threshold."""
    budget = TokenBudget(max_tokens=1000, alert_threshold=0.8)
    tracker = TokenTracker(budget=budget)

    # Below threshold
    tracker.track_tokens(799, "local_llm", "test")
    assert not tracker.is_near_limit()

    # At threshold
    tracker.track_tokens(1, "local_llm", "test")
    assert tracker.is_near_limit()  # 800/1000 = 80%


def test_cost_estimation():
    """Test cost estimation for different backends."""
    tracker = TokenTracker()

    # GPT-4o-mini: ~$0.00015 per 1K tokens
    cost_gpt4o = tracker.get_cost_estimate(1000, "gpt-4o-mini")
    assert cost_gpt4o == pytest.approx(0.00015, rel=0.01)

    # Local LLM: Free
    cost_local = tracker.get_cost_estimate(1000, "local_llm")
    assert cost_local == 0.0

    # OpenAI: Default $0.002 per 1K
    cost_openai = tracker.get_cost_estimate(1000, "openai")
    assert cost_openai == pytest.approx(0.002, rel=0.01)


def test_total_cost_calculation():
    """Test total cost calculation across backends."""
    tracker = TokenTracker()

    tracker.track_tokens(1000, "local_llm", "test1")  # Free
    tracker.track_tokens(1000, "openai", "test2")      # $0.002
    tracker.track_tokens(2000, "anthropic", "test3")   # $0.006

    stats = tracker.get_stats()

    # Total should be $0.008
    assert stats["estimated_cost_usd"] == pytest.approx(0.008, rel=0.01)


def test_reset():
    """Test resetting token tracker."""
    tracker = TokenTracker()

    tracker.track_tokens(1000, "local_llm", "test")
    tracker.track_tokens(5000, "openai", "test")

    assert tracker.tokens_used == 6000

    tracker.reset()

    assert tracker.tokens_used == 0
    assert tracker.local_tokens == 0
    assert tracker.api_tokens == 0
    assert len(tracker.usage_by_operation) == 0
    assert len(tracker.usage_by_backend) == 0


def test_over_budget_detection():
    """Test over-budget detection."""
    tracker = TokenTracker(budget=TokenBudget(max_tokens=1000))

    # Under budget
    tracker.track_tokens(500, "local_llm", "test")
    assert not tracker.is_over_budget()

    # Exactly at budget
    tracker.track_tokens(500, "local_llm", "test")
    assert not tracker.is_over_budget()

    # Over budget
    tracker.track_tokens(1, "local_llm", "test")
    assert tracker.is_over_budget()


def test_tokens_remaining():
    """Test tokens remaining calculation."""
    tracker = TokenTracker(budget=TokenBudget(max_tokens=10000))

    tracker.track_tokens(3000, "local_llm", "test")

    stats = tracker.get_stats()
    assert stats["tokens_remaining"] == 7000


def test_budget_utilization():
    """Test budget utilization percentage."""
    tracker = TokenTracker(budget=TokenBudget(max_tokens=10000))

    tracker.track_tokens(2500, "local_llm", "test")

    stats = tracker.get_stats()
    assert stats["budget_utilization"] == 0.25


def test_custom_pricing():
    """Test token tracker with custom pricing."""
    custom_costs = {
        "local_llm": 0.0,
        "custom_backend": 0.01
    }
    budget = TokenBudget(cost_per_1k_tokens=custom_costs)
    tracker = TokenTracker(budget=budget)

    tracker.track_tokens(1000, "custom_backend", "test")
    stats = tracker.get_stats()

    assert stats["estimated_cost_usd"] == pytest.approx(0.01, rel=0.01)


def test_negative_token_handling():
    """Test that negative token counts are handled gracefully."""
    tracker = TokenTracker()

    # Negative tokens should be logged but not crash
    tracker.track_tokens(-100, "local_llm", "test")

    assert tracker.tokens_used == 0


def test_usage_report():
    """Test generating a human-readable usage report."""
    tracker = TokenTracker()

    tracker.track_tokens(1000, "local_llm", "operation_a")
    tracker.track_tokens(2000, "openai", "operation_b")
    tracker.track_tokens(500, "openai", "operation_a")

    report = tracker.get_usage_report()

    assert "Token Usage Report" in report
    assert "Total tokens used: 3,500" in report
    assert "Local tokens: 1,000" in report
    assert "API tokens: 2,500" in report
    assert "local_llm:" in report
    assert "openai:" in report


def test_multiple_track_operations():
    """Test tracking multiple operations."""
    tracker = TokenTracker()

    # Track many operations
    for i in range(10):
        tracker.track_tokens(100, "local_llm", f"operation_{i}")

    stats = tracker.get_stats()

    assert stats["total_tokens"] == 1000
    assert len(stats["usage_by_operation"]) == 10


def test_alert_threshold_calculation():
    """Test that alert threshold is calculated correctly."""
    budget = TokenBudget(max_tokens=10000, alert_threshold=0.75)
    tracker = TokenTracker(budget=budget)

    assert tracker.alert_threshold_tokens == 7500

    tracker.track_tokens(7499, "local_llm", "test")
    assert not tracker.is_near_limit()

    tracker.track_tokens(1, "local_llm", "test")
    assert tracker.is_near_limit()
