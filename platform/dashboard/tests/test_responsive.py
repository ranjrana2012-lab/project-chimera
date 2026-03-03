"""
Unit tests for responsive layout adapter.

Tests screen size detection and data formatting for different viewports.
"""

import pytest
from pathlib import Path

# Add dashboard to path
dashboard_path = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(dashboard_path))


class TestScreenSize:
    """Test ScreenSize enum."""

    def test_size_values(self):
        """Test size values."""
        from components.responsive import ScreenSize

        assert ScreenSize.DESKTOP.value == "desktop"
        assert ScreenSize.TABLET.value == "tablet"
        assert ScreenSize.MOBILE.value == "mobile"

    def test_from_width(self):
        """Test determining size from width."""
        from components.responsive import ScreenSize

        assert ScreenSize.from_width(2000) == ScreenSize.DESKTOP
        assert ScreenSize.from_width(1440) == ScreenSize.DESKTOP
        assert ScreenSize.from_width(1000) == ScreenSize.TABLET
        assert ScreenSize.from_width(768) == ScreenSize.TABLET
        assert ScreenSize.from_width(500) == ScreenSize.MOBILE


class TestResponsiveConfig:
    """Test ResponsiveConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        from components.responsive import ResponsiveConfig

        config = ResponsiveConfig()
        assert config.breakpoint_tablet == 768
        assert config.breakpoint_desktop == 1440

    def test_custom_breakpoints(self):
        """Test custom breakpoints."""
        from components.responsive import ResponsiveConfig

        config = ResponsiveConfig(
            breakpoint_tablet=600,
            breakpoint_desktop=1200
        )
        assert config.breakpoint_tablet == 600
        assert config.breakpoint_desktop == 1200


class TestResponsiveAdapter:
    """Test ResponsiveAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create responsive adapter."""
        from components.responsive import ResponsiveAdapter
        return ResponsiveAdapter()

    def test_adapter_init(self, adapter):
        """Test adapter initialization."""
        assert adapter.config is not None

    def test_detect_screen_size(self, adapter):
        """Test screen size detection."""
        from components.responsive import ScreenSize

        assert adapter.detect_screen_size(2000) == ScreenSize.DESKTOP
        assert adapter.detect_screen_size(1000) == ScreenSize.TABLET
        assert adapter.detect_screen_size(500) == ScreenSize.MOBILE

    def test_get_health_grid_columns(self, adapter):
        """Test health grid column count by screen size."""
        from components.responsive import ScreenSize

        assert adapter.get_health_grid_columns(ScreenSize.DESKTOP) == 8
        assert adapter.get_health_grid_columns(ScreenSize.TABLET) == 4
        assert adapter.get_health_grid_columns(ScreenSize.MOBILE) == 2

    def test_format_summary_cards(self, adapter):
        """Test formatting summary cards for different screens."""
        from components.responsive import ScreenSize

        data = {
            "total_tests": 2547,
            "passed": 2401,
            "failed": 146,
            "coverage": 82.5,
            "success_rate": 94.2
        }

        # Desktop shows all cards
        desktop = adapter.format_summary_cards(data, ScreenSize.DESKTOP)
        assert len(desktop) == 3

        # Mobile shows compact view
        mobile = adapter.format_summary_cards(data, ScreenSize.MOBILE)
        assert len(mobile) == 3
        assert mobile[0]["compact"] is True

    def test_format_service_health(self, adapter):
        """Test formatting service health for different screens."""
        from components.responsive import ScreenSize

        services = [
            {"name": "svc1", "status": "up", "tests": "45/50"},
            {"name": "svc2", "status": "up", "tests": "120/125"},
        ]

        # Desktop shows full details
        desktop = adapter.format_service_health(services, ScreenSize.DESKTOP)
        assert "show_details" in desktop[0]
        assert desktop[0]["show_details"] is True

        # Mobile shows compact view
        mobile = adapter.format_service_health(services, ScreenSize.MOBILE)
        assert mobile[0]["compact"] is True

    def test_format_chart_data(self, adapter):
        """Test formatting chart data for different screens."""
        from components.responsive import ScreenSize

        chart = {
            "labels": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
            "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }

        # Desktop shows all points
        desktop = adapter.format_chart_data(chart, ScreenSize.DESKTOP)
        assert len(desktop["labels"]) == 10

        # Mobile shows fewer points
        mobile = adapter.format_chart_data(chart, ScreenSize.MOBILE, max_points=5)
        assert len(mobile["labels"]) == 5

    def test_format_table_data(self, adapter):
        """Test formatting table data for different screens."""
        from components.responsive import ScreenSize

        table = [
            {"col1": "A", "col2": "B", "col3": "C", "col4": "D"},
            {"col1": "E", "col2": "F", "col3": "G", "col4": "H"},
        ]

        # Desktop shows all columns
        desktop = adapter.format_table_data(table, ScreenSize.DESKTOP)
        assert len(desktop["columns"]) == 4

        # Mobile shows fewer columns
        mobile = adapter.format_table_data(table, ScreenSize.MOBILE)
        assert len(mobile["columns"]) <= 2

    def test_get_layout_config(self, adapter):
        """Test getting layout configuration."""
        from components.responsive import ScreenSize

        desktop_config = adapter.get_layout_config(ScreenSize.DESKTOP)
        assert desktop_config["columns"] == 3
        assert desktop_config["show_sidebar"] is True

        mobile_config = adapter.get_layout_config(ScreenSize.MOBILE)
        assert mobile_config["columns"] == 1
        assert mobile_config["show_sidebar"] is False


class TestViewportHelper:
    """Test ViewportHelper class."""

    def test_viewport_detection_from_user_agent(self):
        """Test viewport detection from user agent string."""
        from components.responsive import ViewportHelper, ScreenSize

        # Desktop user agent
        desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert ViewportHelper.detect_from_ua(desktop_ua) == ScreenSize.DESKTOP

        # Mobile user agent
        mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
        assert ViewportHelper.detect_from_ua(mobile_ua) == ScreenSize.MOBILE
