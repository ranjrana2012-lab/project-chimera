"""Fixture state and preset management."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from ..models.request import FixtureValues, PresetRequest
from ..models.response import FixtureState, PresetResponse

logger = logging.getLogger(__name__)


class Preset:
    """Represents a lighting preset."""

    def __init__(
        self,
        name: str,
        values: Dict[int, int],
        fixtures: List[Dict[str, Any]],
        fade_time: float = 0.0,
        description: str = ""
    ):
        """Initialize preset.

        Args:
            name: Preset name
            values: Channel values
            fixtures: Fixture configurations
            fade_time: Default fade time
            description: Preset description
        """
        self.name = name
        self.values = values
        self.fixtures = fixtures
        self.fade_time = fade_time
        self.description = description
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary."""
        return {
            "name": self.name,
            "values": self.values,
            "fixtures": self.fixtures,
            "fade_time": self.fade_time,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Preset":
        """Create preset from dictionary."""
        return cls(
            name=data["name"],
            values=data.get("values", {}),
            fixtures=data.get("fixtures", []),
            fade_time=data.get("fade_time", 0.0),
            description=data.get("description", "")
        )


class FixtureManager:
    """Manages fixture states and lighting presets."""

    def __init__(self, preset_path: Optional[Path] = None):
        """Initialize fixture manager.

        Args:
            preset_path: Path to save/load presets
        """
        self.fixtures: Dict[str, FixtureState] = {}
        self.presets: Dict[str, Preset] = {}
        self.preset_path = preset_path or Path("/tmp/lighting_presets.json")
        self.active_preset: Optional[str] = None

    def register_fixture(
        self,
        fixture_id: str,
        dmx_address: int,
        num_channels: int = 3,
        fixture_type: str = "generic"
    ) -> bool:
        """Register a lighting fixture.

        Args:
            fixture_id: Unique fixture identifier
            dmx_address: Base DMX address (1-512)
            num_channels: Number of DMX channels
            fixture_type: Type of fixture (for metadata)

        Returns:
            True if registered successfully
        """
        if dmx_address + num_channels - 1 > 512:
            logger.error(f"Fixture {fixture_id} exceeds DMX range")
            return False

        if fixture_id in self.fixtures:
            logger.warning(f"Fixture {fixture_id} already registered")
            return False

        self.fixtures[fixture_id] = FixtureState(
            fixture_id=fixture_id,
            dmx_address=dmx_address,
            channel_values=[0] * num_channels,
            intensity=0.0
        )
        logger.info(f"Registered fixture {fixture_id} at address {dmx_address}")
        return True

    def unregister_fixture(self, fixture_id: str) -> bool:
        """Unregister a fixture.

        Args:
            fixture_id: Fixture identifier

        Returns:
            True if unregistered
        """
        if fixture_id in self.fixtures:
            del self.fixtures[fixture_id]
            logger.info(f"Unregistered fixture {fixture_id}")
            return True
        return False

    def get_fixture(self, fixture_id: str) -> Optional[FixtureState]:
        """Get fixture state.

        Args:
            fixture_id: Fixture identifier

        Returns:
            Fixture state or None
        """
        return self.fixtures.get(fixture_id)

    def get_all_fixtures(self) -> Dict[str, FixtureState]:
        """Get all fixture states.

        Returns:
            Dictionary of fixture states
        """
        return self.fixtures.copy()

    def update_fixture(
        self,
        fixture_id: str,
        channel_values: List[int],
        intensity: float = 1.0
    ) -> bool:
        """Update fixture state.

        Args:
            fixture_id: Fixture identifier
            channel_values: New channel values
            intensity: Intensity value

        Returns:
            True if updated successfully
        """
        if fixture_id not in self.fixtures:
            logger.warning(f"Unknown fixture: {fixture_id}")
            return False

        fixture = self.fixtures[fixture_id]
        num_channels = min(len(channel_values), len(fixture.channel_values))
        fixture.channel_values[:num_channels] = channel_values[:num_channels]
        fixture.intensity = intensity
        return True

    def get_fixture_values(self, fixture_id: str) -> Optional[Dict[int, int]]:
        """Get DMX channel values for a fixture.

        Args:
            fixture_id: Fixture identifier

        Returns:
            Dictionary mapping DMX channels to values
        """
        fixture = self.fixtures.get(fixture_id)
        if not fixture:
            return None

        values = {}
        for i, value in enumerate(fixture.channel_values):
            channel = fixture.dmx_address + i
            values[channel] = value
        return values

    def get_all_values(self) -> Dict[int, int]:
        """Get all DMX values from all fixtures.

        Returns:
            Dictionary mapping all channels to values
        """
        all_values = {}
        for fixture in self.fixtures.values():
            for i, value in enumerate(fixture.channel_values):
                channel = fixture.dmx_address + i
                if channel <= 512:
                    all_values[channel] = value
        return all_values

    async def create_preset(
        self,
        request: PresetRequest
    ) -> PresetResponse:
        """Create a new preset.

        Args:
            request: Preset creation request

        Returns:
            Preset response
        """
        if request.name in self.presets:
            return PresetResponse(
                name=request.name,
                saved=False,
                error_message=f"Preset '{request.name}' already exists"
            )

        # Build fixture data from request
        fixtures_data = []
        for fixture_req in request.fixtures:
            fixtures_data.append({
                "fixture_id": fixture_req.fixture_id,
                "channels": fixture_req.channels,
                "intensity": fixture_req.intensity
            })

        preset = Preset(
            name=request.name,
            values=request.values,
            fixtures=fixtures_data,
            fade_time=request.fade_time,
            description=request.description
        )

        self.presets[request.name] = preset
        await self._save_presets()

        return PresetResponse(
            name=request.name,
            saved=True,
            values=request.values,
            fixtures=fixtures_data,
            fade_time=request.fade_time
        )

    async def update_preset(
        self,
        name: str,
        request: PresetRequest
    ) -> PresetResponse:
        """Update an existing preset.

        Args:
            name: Preset name
            request: Updated preset data

        Returns:
            Preset response
        """
        if name not in self.presets:
            return PresetResponse(
                name=name,
                saved=False,
                error_message=f"Preset '{name}' not found"
            )

        # Build fixture data
        fixtures_data = []
        for fixture_req in request.fixtures:
            fixtures_data.append({
                "fixture_id": fixture_req.fixture_id,
                "channels": fixture_req.channels,
                "intensity": fixture_req.intensity
            })

        self.presets[name].values = request.values
        self.presets[name].fixtures = fixtures_data
        self.presets[name].fade_time = request.fade_time
        self.presets[name].description = request.description

        await self._save_presets()

        return PresetResponse(
            name=name,
            saved=True,
            values=request.values,
            fixtures=fixtures_data,
            fade_time=request.fade_time
        )

    async def delete_preset(self, name: str) -> bool:
        """Delete a preset.

        Args:
            name: Preset name

        Returns:
            True if deleted
        """
        if name in self.presets:
            del self.presets[name]
            await self._save_presets()
            return True
        return False

    def get_preset(self, name: str) -> Optional[Preset]:
        """Get a preset.

        Args:
            name: Preset name

        Returns:
            Preset or None
        """
        return self.presets.get(name)

    def get_all_presets(self) -> Dict[str, Preset]:
        """Get all presets.

        Returns:
            Dictionary of presets
        """
        return self.presets.copy()

    def get_preset_names(self) -> List[str]:
        """Get list of preset names.

        Returns:
            List of preset names
        """
        return list(self.presets.keys())

    def set_active_preset(self, name: str) -> bool:
        """Set the active preset.

        Args:
            name: Preset name

        Returns:
            True if set successfully
        """
        if name in self.presets:
            self.active_preset = name
            return True
        return False

    def get_active_preset(self) -> Optional[str]:
        """Get active preset name.

        Returns:
            Active preset name or None
        """
        return self.active_preset

    def clear_active_preset(self) -> None:
        """Clear the active preset."""
        self.active_preset = None

    def create_from_current_state(
        self,
        name: str,
        fade_time: float = 0.0,
        description: str = ""
    ) -> Preset:
        """Create a preset from current fixture states.

        Args:
            name: Preset name
            fade_time: Default fade time
            description: Preset description

        Returns:
            Created preset
        """
        # Collect current fixture states
        fixtures_data = []
        values = {}

        for fixture_id, fixture in self.fixtures.items():
            fixtures_data.append({
                "fixture_id": fixture_id,
                "channels": fixture.channel_values.copy(),
                "intensity": fixture.intensity
            })

            # Add to channel values
            for i, value in enumerate(fixture.channel_values):
                channel = fixture.dmx_address + i
                values[channel] = value

        preset = Preset(
            name=name,
            values=values,
            fixtures=fixtures_data,
            fade_time=fade_time,
            description=description
        )

        self.presets[name] = preset
        return preset

    async def _save_presets(self) -> None:
        """Save presets to file."""
        try:
            self.preset_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "presets": {
                    name: preset.to_dict()
                    for name, preset in self.presets.items()
                },
                "active_preset": self.active_preset
            }
            with open(self.preset_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.presets)} presets to {self.preset_path}")
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")

    async def load_presets(self) -> int:
        """Load presets from file.

        Returns:
            Number of presets loaded
        """
        if not self.preset_path.exists():
            logger.info(f"Preset file not found: {self.preset_path}")
            return 0

        try:
            with open(self.preset_path, "r") as f:
                data = json.load(f)

            for name, preset_data in data.get("presets", {}).items():
                self.presets[name] = Preset.from_dict(preset_data)

            self.active_preset = data.get("active_preset")
            loaded_count = len(self.presets)
            logger.info(f"Loaded {loaded_count} presets from {self.preset_path}")
            return loaded_count
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
            return 0

    async def apply_preset(
        self,
        name: str,
        fade_time: Optional[float] = None
    ) -> Optional[Dict[int, int]]:
        """Get values for a preset (for applying via sACN).

        Args:
            name: Preset name
            fade_time: Optional fade time override

        Returns:
            Dictionary of channel values or None
        """
        preset = self.presets.get(name)
        if not preset:
            return None

        # Start with preset's direct values
        all_values = preset.values.copy()

        # Apply fixture-specific values
        for fixture_data in preset.fixtures:
            fixture_id = fixture_data["fixture_id"]
            fixture = self.fixtures.get(fixture_id)

            if fixture:
                intensity = fixture_data.get("intensity", 1.0)
                channels = fixture_data["channels"]

                for i, value in enumerate(channels):
                    channel = fixture.dmx_address + i
                    if channel <= 512:
                        all_values[channel] = int(value * intensity)

        self.active_preset = name
        return all_values

    def get_preset_fade_time(self, name: str) -> float:
        """Get fade time for a preset.

        Args:
            name: Preset name

        Returns:
            Fade time in seconds
        """
        preset = self.presets.get(name)
        return preset.fade_time if preset else 0.0

    def export_presets(self) -> Dict[str, Any]:
        """Export all presets as dictionary.

        Returns:
            Dictionary of all presets
        """
        return {
            name: preset.to_dict()
            for name, preset in self.presets.items()
        }

    async def import_presets(self, data: Dict[str, Any]) -> int:
        """Import presets from dictionary.

        Args:
            data: Dictionary of preset data

        Returns:
            Number of presets imported
        """
        count = 0
        for name, preset_data in data.items():
            try:
                self.presets[name] = Preset.from_dict(preset_data)
                count += 1
            except Exception as e:
                logger.error(f"Failed to import preset {name}: {e}")

        if count > 0:
            await self._save_presets()

        return count
