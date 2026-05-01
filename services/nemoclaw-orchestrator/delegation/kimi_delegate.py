"""Kimi delegation logic for Nemo Claw orchestrator."""

import logging
from typing import Dict, Any, Optional

from .capability_checker import NemoCapabilityChecker
from .grpc_kimi_client import KimiGrpcClient

logger = logging.getLogger(__name__)


class KimiDelegator:
    """Handles delegation of requests to Kimi K2.6 super-agent."""

    def __init__(self):
        self.capability_checker = NemoCapabilityChecker()
        self.kimi_client = None  # Lazy initialization

    async def delegate_if_needed(
        self,
        request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Delegate request to Kimi if needed.

        Args:
            request: Request to potentially delegate

        Returns:
            Kimi response if delegated, None otherwise
        """
        # Check if delegation is needed
        if not self.capability_checker.should_delegate(request):
            logger.debug("Request does not require Kimi delegation")
            return None

        logger.info(f"Delegating request {request.get('request_id')} to Kimi")

        # Initialize client if needed
        if not self.kimi_client:
            self.kimi_client = KimiGrpcClient()

        # Delegate to Kimi
        try:
            response = await self.kimi_client.delegate(request)
            logger.info(f"Kimi response received for {request.get('request_id')}")
            return response

        except Exception as e:
            logger.error(f"Error delegating to Kimi: {e}")
            # Return None to fall back to local processing
            return None

    async def health_check(self) -> bool:
        """Check if Kimi is available for delegation."""
        if not self.kimi_client:
            return False

        return await self.kimi_client.health_check()
