"""Unit tests for OSC handler."""

import pytest
from services.lighting_control.src.core.osc_handler import (
    OSCClient,
    OSCServer,
    OSCHandler
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestOSCClient:
    """Test cases for OSC client."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return OSCClient(host="127.0.0.1", port=9000)

    async def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.host == "127.0.0.1"
        assert client.port == 9000
        assert client.is_connected is False

    async def test_connect_without_library(self, client):
        """Test connection behavior without python-osc."""
        # Mock the availability check
        import services.lighting_control.src.core.osc_handler as osc_module
        original_available = osc_module.OSC_AVAILABLE
        osc_module.OSC_AVAILABLE = False

        result = await client.connect()
        assert result is False

        osc_module.OSC_AVAILABLE = original_available

    async def test_send_disconnected(self, client):
        """Test sending when disconnected."""
        result = await client.send("/test", 1)
        assert result is False

    async def test_send_int(self, client):
        """Test sending integer."""
        result = await client.send_int("/test", 100)
        assert result is False  # Not connected

    async def test_send_float(self, client):
        """Test sending float."""
        result = await client.send_float("/test", 0.5)
        assert result is False  # Not connected

    async def test_send_string(self, client):
        """Test sending string."""
        result = await client.send_string("/test", "hello")
        assert result is False  # Not connected

    async def test_close(self, client):
        """Test closing client."""
        await client.close()
        assert client.is_connected is False


@pytest.mark.unit
class TestOSCServer:
    """Test cases for OSC server."""

    @pytest.fixture
    def server(self):
        """Create a test server."""
        return OSCServer(host="0.0.0.0", port=9000)

    def test_server_initialization(self, server):
        """Test server initialization."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        assert server.host == "0.0.0.0"
        assert server.port == 9000
        assert server.is_running is False

    def test_map_address(self, server):
        """Test mapping an address."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        handler_called = []

        def handler(address, *args):
            handler_called.append((address, args))

        server.map_address("/test", handler)
        assert "/test" in server.message_handlers

    def test_map_default_handler(self, server):
        """Test mapping default handler."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        def default_handler(address, *args):
            pass

        server.map_default_handler(default_handler)
        # Should not raise exception


@pytest.mark.unit
class TestOSCHandler:
    """Test cases for OSC handler."""

    @pytest.fixture
    def handler(self):
        """Create a test handler."""
        return OSCHandler(
            server_host="0.0.0.0",
            server_port=9000,
            client_host="127.0.0.1",
            client_port=9000
        )

    def test_handler_initialization(self, handler):
        """Test handler initialization."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        assert handler.client.host == "127.0.0.1"
        assert handler.server.host == "0.0.0.0"
        assert handler.is_connected is False

    async def test_connect(self, handler):
        """Test connection."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        original_available = osc_module.OSC_AVAILABLE
        osc_module.OSC_AVAILABLE = False

        result = await handler.connect()
        assert result is False

        osc_module.OSC_AVAILABLE = original_available

    async def test_send(self, handler):
        """Test sending message."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        result = await handler.send("/test", 1)
        assert result is False  # Not connected

    async def test_client_connected(self, handler):
        """Test client_connected property."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        assert handler.client_connected is False

    async def test_server_running(self, handler):
        """Test server_running property."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        assert handler.server_running is False

    async def test_close(self, handler):
        """Test closing handler."""
        import services.lighting_control.src.core.osc_handler as osc_module
        if not osc_module.OSC_AVAILABLE:
            pytest.skip("python-osc not available")
        await handler.close()
        assert handler.is_connected is False
