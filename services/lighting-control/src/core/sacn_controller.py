"""sACN (E1.31) protocol controller for DMX over IP."""

import time
from typing import Dict, List, Optional, Tuple
import logging

try:
    import sacn
    SACN_AVAILABLE = True
except ImportError:
    SACN_AVAILABLE = False

from ..models.response import FixtureState

logger = logging.getLogger(__name__)


class sACNController:
    """Controller for sACN (Streaming ACN) DMX over IP protocol.

    sACN is the standard protocol for transmitting DMX data over Ethernet,
    defined in ANSI E1.31. This controller manages sACN sender functionality.
    """

    def __init__(
        self,
        universe: int = 1,
        priority: int = 100,
        source_name: str = "Project Chimera Lighting"
    ):
        """Initialize sACN controller.

        Args:
            universe: sACN universe number (1-63999)
            priority: sACN priority (0-200, 100=default)
            source_name: Source name for sACN packets
        """
        self.universe = universe
        self.priority = priority
        self.source_name = source_name
        self.sender: Optional[Any] = None
        self.is_active = False
        self.dmx_data = [0] * 512
        self.fixtures: Dict[str, FixtureState] = {}

    async def start(self) -> bool:
        """Start sACN sender.

        Returns:
            True if started successfully, False otherwise
        """
        if not SACN_AVAILABLE:
            logger.error("sACN library not available. Install with: pip install sacn")
            return False

        try:
            # Create sACN sender
            self.sender = sacn.sACNsender()
            self.sender.start()
            await self.activate_universe()
            self.is_active = True
            logger.info(f"sACN sender started on universe {self.universe}")
            return True
        except Exception as e:
            logger.error(f"Failed to start sACN sender: {e}")
            return False

    async def activate_universe(self) -> bool:
        """Activate the configured universe.

        Returns:
            True if activated successfully
        """
        if not self.sender:
            return False

        try:
            self.sender.activate_output(self.universe)
            self.sender[self.universe].priority = self.priority
            self.sender[self.universe].source_name = self.source_name
            return True
        except Exception as e:
            logger.error(f"Failed to activate universe {self.universe}: {e}")
            return False

    async def set_channel(self, channel: int, value: int) -> bool:
        """Set a single DMX channel.

        Args:
            channel: DMX channel number (1-512)
            value: DMX value (0-255)

        Returns:
            True if successful
        """
        if not 1 <= channel <= 512:
            logger.warning(f"Invalid channel: {channel}")
            return False

        if not 0 <= value <= 255:
            logger.warning(f"Invalid DMX value: {value}")
            return False

        self.dmx_data[channel - 1] = value
        return await self._send_dmx()

    async def set_channels(self, channels: Dict[int, int]) -> bool:
        """Set multiple DMX channels.

        Args:
            channels: Dictionary mapping channel numbers to values

        Returns:
            True if successful
        """
        for channel, value in channels.items():
            if 1 <= channel <= 512 and 0 <= value <= 255:
                self.dmx_data[channel - 1] = value
            else:
                logger.warning(f"Invalid channel/value: {channel}={value}")

        return await self._send_dmx()

    async def set_channels_range(
        self,
        start_channel: int,
        values: List[int]
    ) -> bool:
        """Set a range of channels.

        Args:
            start_channel: Starting channel number (1-512)
            values: List of DMX values

        Returns:
            True if successful
        """
        if not 1 <= start_channel <= 512:
            logger.warning(f"Invalid start channel: {start_channel}")
            return False

        for i, value in enumerate(values):
            channel = start_channel + i
            if channel <= 512 and 0 <= value <= 255:
                self.dmx_data[channel - 1] = value

        return await self._send_dmx()

    async def get_channel(self, channel: int) -> Optional[int]:
        """Get current value of a channel.

        Args:
            channel: DMX channel number (1-512)

        Returns:
            Current DMX value or None if invalid
        """
        if 1 <= channel <= 512:
            return self.dmx_data[channel - 1]
        return None

    async def get_all_channels(self) -> List[int]:
        """Get all 512 DMX channel values.

        Returns:
            List of 512 DMX values
        """
        return self.dmx_data.copy()

    async def _send_dmx(self) -> bool:
        """Send DMX data via sACN.

        Returns:
            True if sent successfully or in test mode
        """
        if not self.is_active or not self.sender:
            # Allow operation in test/offline mode
            logger.debug("sACN sender not active - storing values only")
            return True

        try:
            # sACN expects data starting from index 0 (DMX channel 1)
            # Find last non-zero value to minimize packet size
            last_non_zero = 511
            for i in range(511, -1, -1):
                if self.dmx_data[i] > 0:
                    last_non_zero = i
                    break

            data_to_send = self.dmx_data[:last_non_zero + 1]
            self.sender[self.universe].dmx_data = tuple(data_to_send)
            return True
        except Exception as e:
            logger.error(f"Failed to send sACN data: {e}")
            return False

    async def blackout(self) -> bool:
        """Blackout all channels (set to 0).

        Returns:
            True if successful
        """
        self.dmx_data = [0] * 512
        return await self._send_dmx()

    def register_fixture(
        self,
        fixture_id: str,
        dmx_address: int,
        num_channels: int = 3
    ) -> bool:
        """Register a fixture with its DMX address.

        Args:
            fixture_id: Fixture identifier
            dmx_address: Base DMX address (1-512)
            num_channels: Number of channels for this fixture

        Returns:
            True if registered successfully
        """
        if dmx_address + num_channels - 1 > 512:
            logger.error(f"Fixture {fixture_id} exceeds DMX range")
            return False

        self.fixtures[fixture_id] = FixtureState(
            fixture_id=fixture_id,
            dmx_address=dmx_address,
            channel_values=[0] * num_channels,
            intensity=0.0
        )
        logger.info(f"Registered fixture {fixture_id} at address {dmx_address}")
        return True

    async def set_fixture(
        self,
        fixture_id: str,
        channel_values: List[int],
        intensity: float = 1.0
    ) -> bool:
        """Set values for a specific fixture.

        Args:
            fixture_id: Fixture identifier
            channel_values: Channel values
            intensity: Intensity modifier (0.0-1.0)

        Returns:
            True if successful
        """
        if fixture_id not in self.fixtures:
            logger.warning(f"Unknown fixture: {fixture_id}")
            return False

        fixture = self.fixtures[fixture_id]
        base_address = fixture.dmx_address

        # Apply intensity modifier
        scaled_values = [int(v * intensity) for v in channel_values]

        # Update fixture state
        num_channels = min(len(scaled_values), len(fixture.channel_values))
        fixture.channel_values[:num_channels] = scaled_values[:num_channels]
        fixture.intensity = intensity

        # Update DMX data
        for i, value in enumerate(scaled_values):
            channel = base_address + i
            if channel <= 512:
                self.dmx_data[channel - 1] = value

        return await self._send_dmx()

    async def get_fixture_state(self, fixture_id: str) -> Optional[FixtureState]:
        """Get current state of a fixture.

        Args:
            fixture_id: Fixture identifier

        Returns:
            Fixture state or None if not found
        """
        return self.fixtures.get(fixture_id)

    async def get_all_fixtures(self) -> Dict[str, FixtureState]:
        """Get all registered fixture states.

        Returns:
            Dictionary of fixture states
        """
        return self.fixtures.copy()

    def set_priority(self, priority: int) -> bool:
        """Set sACN priority.

        Args:
            priority: Priority value (0-200)

        Returns:
            True if successful
        """
        if not 0 <= priority <= 200:
            return False

        self.priority = priority
        if self.is_active and self.sender:
            try:
                self.sender[self.universe].priority = priority
                return True
            except Exception as e:
                logger.error(f"Failed to set priority: {e}")
                return False
        return True

    async def close(self) -> None:
        """Close sACN sender."""
        if self.sender:
            try:
                # Blackout before closing
                await self.blackout()
                await self._send_dmx()
                self.sender.stop()
            except Exception as e:
                logger.error(f"Error closing sACN sender: {e}")
            finally:
                self.sender = None
                self.is_active = False
        logger.info("sACN sender closed")
