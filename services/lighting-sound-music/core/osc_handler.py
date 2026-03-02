"""OSC (Open Sound Control) message handler."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import AsyncIOOSCUDPServer
    from pythonosc.udp_client import SimpleUDPClient
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False
    Dispatcher = None
    AsyncIOOSCUDPServer = None
    SimpleUDPClient = None

logger = logging.getLogger(__name__)


class OSCMessage:
    """Represents an OSC message."""

    def __init__(self, address: str, arguments: List[Any]):
        """Initialize OSC message.

        Args:
            address: OSC address pattern
            arguments: List of arguments
        """
        self.address = address
        self.arguments = arguments

    def __repr__(self) -> str:
        return f"OSCMessage(address='{self.address}', args={self.arguments})"


class OSCClient:
    """OSC client for sending messages."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        """Initialize OSC client.

        Args:
            host: Target host
            port: Target port
        """
        self.host = host
        self.port = port
        self.client: Optional[SimpleUDPClient] = None
        self.is_connected = False

    async def connect(self) -> bool:
        """Connect OSC client.

        Returns:
            True if connected successfully
        """
        if not OSC_AVAILABLE:
            logger.error("python-osc library not available. Install with: pip install python-osc")
            return False

        try:
            self.client = SimpleUDPClient(self.host, self.port)
            self.is_connected = True
            logger.info(f"OSC client connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect OSC client: {e}")
            return False

    async def send(self, address: str, *args: Any) -> bool:
        """Send OSC message.

        Args:
            address: OSC address pattern
            *args: Arguments to send

        Returns:
            True if sent successfully
        """
        if not self.is_connected or not self.client:
            logger.warning("OSC client not connected")
            return False

        try:
            self.client.send_message(address, args if args else [])
            logger.debug(f"OSC sent: {address} {args}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OSC message: {e}")
            return False

    async def send_int(self, address: str, value: int) -> bool:
        """Send integer OSC message.

        Args:
            address: OSC address pattern
            value: Integer value

        Returns:
            True if sent successfully
        """
        return await self.send(address, value)

    async def send_float(self, address: str, value: float) -> bool:
        """Send float OSC message.

        Args:
            address: OSC address pattern
            value: Float value

        Returns:
            True if sent successfully
        """
        return await self.send(address, value)

    async def send_string(self, address: str, value: str) -> bool:
        """Send string OSC message.

        Args:
            address: OSC address pattern
            value: String value

        Returns:
            True if sent successfully
        """
        return await self.send(address, value)

    async def close(self) -> None:
        """Close OSC client."""
        self.client = None
        self.is_connected = False
        logger.info("OSC client closed")


class OSCServer:
    """OSC server for receiving messages."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        dispatcher: Optional[Any] = None
    ):
        """Initialize OSC server.

        Args:
            host: Bind address
            port: Bind port
            dispatcher: Optional custom dispatcher
        """
        self.host = host
        self.port = port
        self.dispatcher = dispatcher or (Dispatcher() if OSC_AVAILABLE else None)
        self.server: Optional[Any] = None
        self.is_running = False
        self.message_handlers: Dict[str, List[Callable]] = {}

    def map_address(self, address: str, handler: Callable) -> None:
        """Map an address to a handler function.

        Args:
            address: OSC address pattern (supports wildcards)
            handler: Callback function receiving address, *args
        """
        self.dispatcher.map(address, handler)
        if address not in self.message_handlers:
            self.message_handlers[address] = []
        self.message_handlers[address].append(handler)
        logger.debug(f"Mapped OSC address: {address}")

    def map_default_handler(self, handler: Callable) -> None:
        """Set default handler for unmapped addresses.

        Args:
            handler: Callback function receiving address, *args
        """
        self.dispatcher.set_default_handler(handler)
        logger.debug("Set default OSC handler")

    def map_lighting_commands(self, lighting_handler: Any) -> None:
        """Map standard lighting command addresses.

        Args:
            lighting_handler: Handler object with lighting control methods
        """
        # Channel control
        self.map_address("/lighting/channel/set", self._handle_channel_set)
        self.map_address("/lighting/channel/*", self._handle_channel_set)

        # Fixture control
        self.map_address("/lighting/fixture/set", self._handle_fixture_set)
        self.map_address("/lighting/fixture/*", self._handle_fixture_set)

        # Scene/preset control
        self.map_address("/lighting/preset/recall", self._handle_preset_recall)
        self.map_address("/lighting/preset/*", self._handle_preset_recall)
        self.map_address("/lighting/scene/set", self._handle_scene_set)

        # Cue control
        self.map_address("/lighting/cue/go", self._handle_cue_go)
        self.map_address("/lighting/cue/*", self._handle_cue_go)

        # System control
        self.map_address("/lighting/blackout", self._handle_blackout)
        self.map_address("/lighting/panic", self._handle_blackout)

        # Store reference for handlers
        self._lighting_handler = lighting_handler

    async def _handle_channel_set(self, address: str, *args: Any) -> None:
        """Handle channel set command."""
        if hasattr(self, '_lighting_handler') and self._lighting_handler:
            # Parse address like /lighting/channel/1 or extract from args
            channel = None
            value = None

            # Try to extract channel from address
            parts = address.split('/')
            if len(parts) >= 4 and parts[3].isdigit():
                channel = int(parts[3])

            # Extract from args
            if len(args) >= 1:
                if isinstance(args[0], (int, float)):
                    if channel is None and len(args) >= 2:
                        channel = int(args[0])
                        value = int(args[1])
                    else:
                        value = int(args[0])

            if channel is not None and value is not None:
                await self._lighting_handler.set_channel(channel, value)
                logger.debug(f"OSC: Set channel {channel} to {value}")

    async def _handle_fixture_set(self, address: str, *args: Any) -> None:
        """Handle fixture set command."""
        if hasattr(self, '_lighting_handler') and self._lighting_handler:
            # Parse fixture ID and values from args
            fixture_id = None
            values = []

            for arg in args:
                if isinstance(arg, str):
                    fixture_id = arg
                elif isinstance(arg, (int, float)):
                    values.append(int(arg))

            if fixture_id and values:
                await self._lighting_handler.set_fixture(fixture_id, values)
                logger.debug(f"OSC: Set fixture {fixture_id} to {values}")

    async def _handle_preset_recall(self, address: str, *args: Any) -> None:
        """Handle preset recall command."""
        if hasattr(self, '_lighting_handler') and self._lighting_handler:
            preset_name = None
            fade_time = None

            for arg in args:
                if isinstance(arg, str):
                    preset_name = arg
                elif isinstance(arg, (int, float)) and fade_time is None:
                    fade_time = float(arg)

            if preset_name:
                await self._lighting_handler.recall_preset(preset_name, fade_time)
                logger.debug(f"OSC: Recall preset {preset_name}")

    async def _handle_scene_set(self, address: str, *args: Any) -> None:
        """Handle scene set command."""
        if hasattr(self, '_lighting_handler') and self._lighting_handler:
            scene_name = None
            if args and isinstance(args[0], str):
                scene_name = args[0]

            if scene_name:
                await self._lighting_handler.set_scene(scene_name)
                logger.debug(f"OSC: Set scene {scene_name}")

    async def _handle_cue_go(self, address: str, *args: Any) -> None:
        """Handle cue go command."""
        if hasattr(self, '_lighting_handler') and self._lighting_handler:
            cue_number = None
            if args and isinstance(args[0], (str, int, float)):
                cue_number = str(args[0])

            if cue_number:
                await self._lighting_handler.execute_cue(cue_number)
                logger.debug(f"OSC: Execute cue {cue_number}")

    async def _handle_blackout(self, address: str, *args: Any) -> None:
        """Handle blackout command."""
        if hasattr(self, '_lighting_handler') and self._lighting_handler:
            await self._lighting_handler.blackout()
            logger.debug("OSC: Blackout triggered")

    async def start(self) -> bool:
        """Start OSC server.

        Returns:
            True if started successfully
        """
        if not OSC_AVAILABLE:
            logger.error("python-osc library not available")
            return False

        try:
            self.server = AsyncIOOSCUDPServer(
                (self.host, self.port),
                self.dispatcher,
                asyncio.get_event_loop()
            )
            self.transport, self.protocol = await self.server.create_serve_endpoint()
            self.is_running = True
            logger.info(f"OSC server listening on {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start OSC server: {e}")
            return False

    async def stop(self) -> None:
        """Stop OSC server."""
        if self.transport:
            self.transport.close()
            self.is_running = False
            logger.info("OSC server stopped")


class OSCHandler:
    """Main OSC handler combining client and server."""

    def __init__(
        self,
        server_host: str = "0.0.0.0",
        server_port: int = 9000,
        client_host: str = "127.0.0.1",
        client_port: int = 9000
    ):
        """Initialize OSC handler.

        Args:
            server_host: Server bind address
            server_port: Server bind port
            client_host: Client target host
            client_port: Client target port
        """
        self.client = OSCClient(client_host, client_port)
        self.server = OSCServer(server_host, server_port)
        self.is_connected = False

    async def connect(self) -> bool:
        """Connect both client and server.

        Returns:
            True if both connected successfully
        """
        client_ok = await self.client.connect()
        # Server will be started separately with lighting handler mapping
        self.is_connected = client_ok
        return self.is_connected

    async def start_server(self, lighting_handler: Any) -> bool:
        """Start OSC server with lighting command mapping.

        Args:
            lighting_handler: Handler object with lighting control methods

        Returns:
            True if server started successfully
        """
        self.server.map_lighting_commands(lighting_handler)
        return await self.server.start()

    async def send(self, address: str, *args: Any) -> bool:
        """Send message via client.

        Args:
            address: OSC address pattern
            *args: Arguments to send

        Returns:
            True if sent successfully
        """
        return await self.client.send(address, *args)

    async def close(self) -> None:
        """Close both client and server."""
        await self.client.close()
        await self.server.stop()
        self.is_connected = False

    @property
    def client_connected(self) -> bool:
        """Check if client is connected."""
        return self.client.is_connected

    @property
    def server_running(self) -> bool:
        """Check if server is running."""
        return self.server.is_running
