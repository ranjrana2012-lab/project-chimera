"""Tests for dashboard service main module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from datetime import datetime
from services.dashboard.main import (
    get_service_health,
    get_git_commits,
    get_ralph_loop_status,
    get_test_summary,
    generate_daily_summary,
    update_dashboard_data,
    DashboardData,
)


class TestGetServiceHealth:
    """Test get_service_health function."""

    @pytest.mark.asyncio
    async def test_get_service_health_returns_default_services(self):
        """Test get_service_health returns default services."""
        services = await get_service_health()
        assert "dashboard" in services
        assert "health_aggregator" in services
        assert "chimera_core" in services
        assert services["dashboard"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_service_health_with_error(self):
        """Test get_service_health handles errors gracefully."""
        with patch('services.dashboard.main.httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Network error")
            services = await get_service_health()
            assert len(services) > 0


class TestGetGitCommits:
    """Test get_git_commits function."""

    @pytest.mark.asyncio
    async def test_get_git_commits_returns_list(self):
        """Test get_git_commits returns a list."""
        commits = await get_git_commits()
        assert isinstance(commits, list)

    @pytest.mark.asyncio
    async def test_get_git_commits_with_error(self):
        """Test get_git_commits handles errors gracefully."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Git error")
            commits = await get_git_commits()
            assert commits == []


class TestGetRalphLoopStatus:
    """Test get_ralph_loop_status function."""

    def test_get_ralph_loop_status_structure(self):
        """Test get_ralph_loop_status returns correct structure."""
        status = get_ralph_loop_status()
        assert "queue" in status
        assert "learnings" in status
        assert "metrics" in status
        assert isinstance(status["queue"], list)
        assert isinstance(status["learnings"], str)
        assert isinstance(status["metrics"], dict)


class TestGetTestSummary:
    """Test get_test_summary function."""

    @pytest.mark.asyncio
    async def test_get_test_summary_returns_defaults(self):
        """Test get_test_summary returns default structure."""
        summary = await get_test_summary()
        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "skipped" in summary
        assert summary["total"] == 0

    @pytest.mark.asyncio
    async def test_get_test_summary_with_error(self):
        """Test get_test_summary handles errors gracefully."""
        with patch('services.dashboard.main.httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Network error")
            summary = await get_test_summary()
            assert summary["total"] == 0


class TestGenerateDailySummary:
    """Test generate_daily_summary function."""

    def test_generate_daily_summary_structure(self):
        """Test generate_daily_summary returns string."""
        services = {
            "svc1": {"status": "healthy"},
            "svc2": {"status": "down"}
        }
        test_summary = {"total": 10, "passed": 8}
        ralph_status = {"queue": ["item1", "item2"]}

        summary = generate_daily_summary(services, test_summary, ralph_status)

        assert isinstance(summary, str)
        assert "Services:" in summary
        assert "Tests:" in summary
        assert "Ralph Queue:" in summary

    def test_generate_daily_summary_with_zero_total_tests(self):
        """Test generate_daily_summary handles zero total tests."""
        services = {"svc1": {"status": "healthy"}}
        test_summary = {"total": 0, "passed": 0}
        ralph_status = {"queue": []}

        summary = generate_daily_summary(services, test_summary, ralph_status)

        assert "N/A" in summary

    def test_generate_daily_summary_includes_timestamp(self):
        """Test generate_daily_summary includes timestamp."""
        services = {"svc1": {"status": "healthy"}}
        test_summary = {"total": 1, "passed": 1}
        ralph_status = {"queue": []}

        summary = generate_daily_summary(services, test_summary, ralph_status)

        assert "Last update:" in summary


class TestUpdateDashboardData:
    """Test update_dashboard_data function."""

    @pytest.mark.asyncio
    async def test_update_dashboard_data_returns_dashboard_data(self):
        """Test update_dashboard_data returns DashboardData."""
        data = await update_dashboard_data()
        assert isinstance(data, DashboardData)
        assert isinstance(data.timestamp, str)
        assert isinstance(data.services, dict)
        assert isinstance(data.git_commits, list)
        assert isinstance(data.test_summary, dict)
        assert isinstance(data.daily_summary, str)


class TestDashboardData:
    """Test DashboardData model."""

    def test_dashboard_data_creation(self):
        """Test creating DashboardData."""
        data = DashboardData(
            timestamp="2026-04-10T12:00:00",
            services={"svc1": {"status": "healthy"}},
            git_commits=[{"hash": "abc123", "message": "Test commit"}],
            test_summary={"total": 10, "passed": 8},
            daily_summary="Test summary"
        )
        assert data.timestamp == "2026-04-10T12:00:00"
        assert len(data.git_commits) == 1
        assert data.test_summary["total"] == 10
        assert data.daily_summary == "Test summary"
