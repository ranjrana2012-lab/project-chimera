"""
OpenClaw Bot: Public Opinion Reporter

Reports public opinion analysis and predictions
via Telegram/Discord during live shows.
"""

from typing import Optional
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

OPINION_API_URL = "http://opinion-pipeline-agent:8020"


class OpinionReporterBot:
    """Bot that reports public opinion insights from BettaFish/MiroFish."""

    def __init__(self, opinion_api_url: str = OPINION_API_URL):
        """
        Initialize the opinion reporter bot.

        Args:
            opinion_api_url: URL of the opinion pipeline service
        """
        self.opinion_api_url = opinion_api_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_daily_summary(self) -> Optional[str]:
        """
        Get daily opinion summary formatted for chat.

        Returns:
            Formatted string with public opinion summary, or None if unavailable
        """
        try:
            response = await self.client.get(
                f"{self.opinion_api_url}/api/v1/latest/sentiment"
            )

            if response.status_code == 200:
                data = response.json()
                return self._format_opinion_summary(data)
            else:
                logger.warning(f"Opinion API returned {response.status_code}")
                return None

        except httpx.ConnectError:
            logger.warning("Could not connect to opinion pipeline")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch opinion data: {e}")
            return None

    async def get_prediction_alert(self) -> Optional[str]:
        """
        Get prediction alerts from MiroFish simulations.

        Returns:
            Formatted string with prediction alert, or None if unavailable
        """
        try:
            # Get latest simulation (would need specific endpoint)
            response = await self.client.get(
                f"{self.opinion_api_url}/api/v1/status"
            )

            if response.status_code == 200:
                data = response.json()
                return self._format_prediction_alert(data)
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to fetch prediction data: {e}")
            return None

    def _format_opinion_summary(self, data: dict) -> str:
        """Format opinion data for chat display."""
        latest = data.get("latest_analysis", {})

        if not latest:
            return "📊 *Public Opinion Summary*\n\nNo recent analysis available."

        report = latest.get("report_path", "Unknown")
        timestamp = latest.get("timestamp", "Unknown")

        return f"""📊 *Public Opinion Summary*

Latest Analysis: `{latest.get("analysis_id", "N/A")}`
Report Path: `{report}`
Timestamp: `{timestamp}`

*Source: BettaFish Public Opinion Analysis*"""

    def _format_prediction_alert(self, data: dict) -> str:
        """Format prediction alert for chat display."""
        simulation_active = data.get("simulation_active", False)

        if not simulation_active:
            return None

        return """⚠️ *Prediction Alert*

MiroFish simulation is currently running.
Swarm intelligence agents are analyzing public sentiment trends.

*Source: MiroFish Swarm Intelligence*"""


# Singleton instance for bot registration
_opinion_reporter_instance: Optional[OpinionReporterBot] = None


def get_opinion_reporter_bot() -> OpinionReporterBot:
    """Get or create the opinion reporter bot singleton."""
    global _opinion_reporter_instance

    if _opinion_reporter_instance is None:
        logger.info("Creating OpinionReporterBot instance")
        _opinion_reporter_instance = OpinionReporterBot()

    return _opinion_reporter_instance


async def close_opinion_reporter_bot():
    """Close the opinion reporter bot."""
    global _opinion_reporter_instance

    if _opinion_reporter_instance:
        await _opinion_reporter_instance.close()
        _opinion_reporter_instance = None
