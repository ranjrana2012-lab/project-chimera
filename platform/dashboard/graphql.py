"""GraphQL schema for Dashboard."""
import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class TestRun:
    """Test run GraphQL type."""
    run_id: str
    commit_sha: str
    branch: str
    status: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: int
    coverage_pct: float
    mutation_score: float
    created_at: datetime


@strawberry.type
class TrendPoint:
    """Trend data point."""
    date: str
    value: float


@strawberry.type
class TrendData:
    """Trend data for a metric."""
    metric: str
    days: int
    data: List[TrendPoint]


@strawberry.type
class Query:
    """GraphQL query resolvers."""

    @strawberry.field
    async def runs(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[TestRun]:
        """Get list of test runs."""
        # TODO: Query from database
        return []

    @strawberry.field
    async def run(self, run_id: str) -> Optional[TestRun]:
        """Get a specific test run by ID."""
        # TODO: Query from database
        return None

    @strawberry.field
    async def trends(
        self,
        metric: str,
        days: int = 30
    ) -> TrendData:
        """Get trend data for a metric."""
        # TODO: Query from database
        return TrendData(
            metric=metric,
            days=days,
            data=[]
        )


@strawberry.type
class Subscription:
    """GraphQL subscription resolvers for real-time updates."""

    @strawberry.subscription
    async def run_updates(self, run_id: str) -> TestRun:
        """Subscribe to real-time updates for a test run."""
        # TODO: Implement WebSocket-based subscription
        yield None


schema = strawberry.Schema(query=Query, subscription=Subscription)
