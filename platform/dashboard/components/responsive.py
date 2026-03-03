"""
Responsive layout adapter for dashboard.

Provides screen size detection and data formatting for different viewports.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ScreenSize(Enum):
    """Screen size categories."""
    DESKTOP = "desktop"    # >= 1440px
    TABLET = "tablet"      # 768px - 1439px
    MOBILE = "mobile"      # < 768px

    @classmethod
    def from_width(cls, width: int, tablet_breakpoint: int = 768, desktop_breakpoint: int = 1440) -> "ScreenSize":
        """Determine screen size from width."""
        if width >= desktop_breakpoint:
            return cls.DESKTOP
        elif width >= tablet_breakpoint:
            return cls.TABLET
        else:
            return cls.MOBILE


@dataclass
class ResponsiveConfig:
    """
    Configuration for responsive behavior.

    Attributes:
        breakpoint_tablet: Minimum width for tablet view
        breakpoint_desktop: Minimum width for desktop view
        mobile_health_columns: Number of health columns on mobile
        tablet_health_columns: Number of health columns on tablet
        desktop_health_columns: Number of health columns on desktop
    """
    breakpoint_tablet: int = 768
    breakpoint_desktop: int = 1440
    mobile_health_columns: int = 2
    tablet_health_columns: int = 4
    desktop_health_columns: int = 8


class ResponsiveAdapter:
    """
    Adapts dashboard data for different screen sizes.

    Provides formatting and layout configuration based on viewport.
    """

    def __init__(self, config: Optional[ResponsiveConfig] = None):
        """
        Initialize responsive adapter.

        Args:
            config: Responsive configuration
        """
        self.config = config or ResponsiveConfig()
        logger.info("ResponsiveAdapter initialized")

    def detect_screen_size(self, width: int) -> ScreenSize:
        """
        Detect screen size from width.

        Args:
            width: Viewport width in pixels

        Returns:
            Detected screen size
        """
        return ScreenSize.from_width(
            width,
            self.config.breakpoint_tablet,
            self.config.breakpoint_desktop
        )

    def get_health_grid_columns(self, size: ScreenSize) -> int:
        """
        Get number of columns for health grid.

        Args:
            size: Screen size

        Returns:
            Number of columns
        """
        mapping = {
            ScreenSize.MOBILE: self.config.mobile_health_columns,
            ScreenSize.TABLET: self.config.tablet_health_columns,
            ScreenSize.DESKTOP: self.config.desktop_health_columns
        }
        return mapping.get(size, 2)

    def format_summary_cards(self, data: Dict[str, Any], size: ScreenSize) -> List[Dict[str, Any]]:
        """
        Format summary cards for screen size.

        Args:
            data: Summary data
            size: Screen size

        Returns:
            Formatted card data
        """
        cards = [
            {
                "title": "Total Tests",
                "value": str(data.get("total_tests", 0)),
                "subtitle": f"{data.get('passed', 0)} passed, {data.get('failed', 0)} failed",
                "type": "tests",
                "compact": size == ScreenSize.MOBILE
            },
            {
                "title": "Coverage",
                "value": f"{data.get('coverage', 0):.1f}%",
                "subtitle": "overall coverage",
                "type": "coverage",
                "compact": size == ScreenSize.MOBILE
            },
            {
                "title": "Success Rate",
                "value": f"{data.get('success_rate', 0):.1f}%",
                "subtitle": "test success rate",
                "type": "success",
                "compact": size == ScreenSize.MOBILE
            }
        ]

        return cards

    def format_service_health(self, services: List[Dict[str, Any]], size: ScreenSize) -> List[Dict[str, Any]]:
        """
        Format service health for screen size.

        Args:
            services: Service health data
            size: Screen size

        Returns:
            Formatted service data
        """
        formatted = []

        for svc in services:
            item = {
                "name": svc.get("name", ""),
                "status": svc.get("status", "unknown"),
                "compact": size == ScreenSize.MOBILE,
                "show_details": size != ScreenSize.MOBILE
            }

            # Add test info on larger screens
            if size != ScreenSize.MOBILE:
                item["tests"] = svc.get("tests", "")
                item["last_check"] = svc.get("last_check", "")

            formatted.append(item)

        return formatted

    def format_chart_data(
        self,
        chart: Dict[str, Any],
        size: ScreenSize,
        max_points: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format chart data for screen size.

        Args:
            chart: Chart data
            size: Screen size
            max_points: Maximum data points for mobile

        Returns:
            Formatted chart data
        """
        labels = chart.get("labels", [])
        data = chart.get("data", [])

        # Reduce data points for mobile
        if size == ScreenSize.MOBILE and max_points and len(labels) > max_points:
            # Sample points evenly
            step = len(labels) // max_points
            labels = labels[::step][:max_points]
            data = data[::step][:max_points]

        return {
            "labels": labels,
            "data": data,
            "responsive": True,
            "maintain_aspect_ratio": size != ScreenSize.MOBILE
        }

    def format_table_data(self, table: List[Dict[str, Any]], size: ScreenSize) -> Dict[str, Any]:
        """
        Format table data for screen size.

        Args:
            table: Table row data
            size: Screen size

        Returns:
            Formatted table data
        """
        if not table:
            return {"rows": [], "columns": []}

        all_columns = list(table[0].keys())

        # Select columns based on screen size
        if size == ScreenSize.MOBILE:
            # Show only most important columns
            columns = all_columns[:2]
        elif size == ScreenSize.TABLET:
            columns = all_columns[:3]
        else:
            columns = all_columns

        # Filter rows to selected columns
        rows = []
        for row in table:
            rows.append({k: row[k] for k in columns})

        return {
            "rows": rows,
            "columns": columns,
            "scrollable": size == ScreenSize.MOBILE
        }

    def get_layout_config(self, size: ScreenSize) -> Dict[str, Any]:
        """
        Get layout configuration for screen size.

        Args:
            size: Screen size

        Returns:
            Layout configuration
        """
        configs = {
            ScreenSize.DESKTOP: {
                "columns": 3,
                "show_sidebar": True,
                "card_size": "medium",
                "full_details": True
            },
            ScreenSize.TABLET: {
                "columns": 2,
                "show_sidebar": True,
                "card_size": "small",
                "full_details": False
            },
            ScreenSize.MOBILE: {
                "columns": 1,
                "show_sidebar": False,
                "card_size": "compact",
                "full_details": False,
                "hamburger_menu": True
            }
        }

        return configs.get(size, configs[ScreenSize.MOBILE])


class ViewportHelper:
    """
    Helper for viewport detection from user agent.

    Provides fallback detection when client width is not available.
    """

    # Mobile device patterns
    MOBILE_PATTERNS = [
        r"iPhone",
        r"iPod",
        r"Android",
        r"Mobile",
        r"BlackBerry",
        r"Opera Mini"
    ]

    # Tablet patterns
    TABLET_PATTERNS = [
        r"iPad",
        r"Tablet",
        r"Kindle"
    ]

    @classmethod
    def detect_from_ua(cls, user_agent: str) -> ScreenSize:
        """
        Detect screen size from user agent string.

        Args:
            user_agent: HTTP User-Agent header value

        Returns:
            Detected screen size
        """
        # Check for mobile
        for pattern in cls.MOBILE_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return ScreenSize.MOBILE

        # Check for tablet
        for pattern in cls.TABLET_PATTERNS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return ScreenSize.TABLET

        # Default to desktop
        return ScreenSize.DESKTOP

    @classmethod
    def is_mobile(cls, user_agent: str) -> bool:
        """Check if user agent is mobile."""
        return cls.detect_from_ua(user_agent) == ScreenSize.MOBILE

    @classmethod
    def is_tablet(cls, user_agent: str) -> bool:
        """Check if user agent is tablet."""
        return cls.detect_from_ua(user_agent) == ScreenSize.TABLET

    @classmethod
    def is_desktop(cls, user_agent: str) -> bool:
        """Check if user agent is desktop."""
        detected = cls.detect_from_ua(user_agent)
        return detected == ScreenSize.DESKTOP
