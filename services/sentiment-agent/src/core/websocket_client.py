"""WebSocket client for receiving WorldMonitor context updates."""

import asyncio
import json
import logging
from typing import Callable, Optional
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class WorldMonitorWebSocketClient:
    """WebSocket client for WorldMonitor sidecar context updates."""

    def __init__(self, url: str, reconnect_interval: int = 5, max_retries: int = 10):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self._context_cache = None
        self._connected = False
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._callbacks: list[Callable] = []

    async def connect(self) -> None:
        """Connect to the WebSocket server and start receiving updates."""
        self._running = True
        self._task = asyncio.create_task(self._connect_loop())
        logger.info(f"WebSocket client started for {self.url}")

    async def _connect_loop(self) -> None:
        """Connection and reconnection loop."""
        retry_count = 0

        while self._running and retry_count < self.max_retries:
            try:
                logger.info(f"Connecting to {self.url}...")
                async with websockets.connect(self.url) as websocket:
                    self._connected = True
                    retry_count = 0
                    logger.info("WebSocket connected successfully")

                    await websocket.send(json.dumps({"type": "subscribe"}))

                    while self._running:
                        try:
                            message = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=30.0
                            )
                            data = json.loads(message)
                            await self._handle_message(data)

                        except asyncio.TimeoutError:
                            try:
                                await websocket.ping()
                            except ConnectionClosed:
                                break

            except ConnectionClosed:
                self._connected = False
                logger.warning("WebSocket connection closed")

            except Exception as e:
                self._connected = False
                logger.error(f"WebSocket error: {e}")

            if self._running and retry_count < self.max_retries:
                retry_count += 1
                logger.info(f"Reconnecting in {self.reconnect_interval} seconds... (attempt {retry_count}/{self.max_retries})")
                await asyncio.sleep(self.reconnect_interval)

        if not self._connected:
            logger.error(f"Failed to connect after {self.max_retries} attempts")

    async def _handle_message(self, data: dict) -> None:
        """Handle incoming WebSocket message."""
        message_type = data.get("type")

        if message_type == "context_update":
            context_data = data.get("data", {})
            self._context_cache = context_data

            for callback in self._callbacks:
                try:
                    await callback(context_data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            logger.debug(f"Context updated: global_cii={context_data.get('global_cii')}")

    def get_context(self) -> Optional[dict]:
        """Get the current cached context."""
        return self._context_cache

    @property
    def is_connected(self) -> bool:
        """Check if the WebSocket client is connected."""
        return self._connected

    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be called on context updates."""
        self._callbacks.append(callback)

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        self._running = False
        self._connected = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("WebSocket client disconnected")
