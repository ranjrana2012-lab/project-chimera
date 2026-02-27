"""Unit tests for fixture manager."""

import pytest
from services.lighting_control.src.core.fixture_manager import (
    FixtureManager,
    Preset
)
from services.lighting_control.src.models.request import PresetRequest, FixtureValues


@pytest.mark.unit
@pytest.mark.asyncio
class TestFixtureManager:
    """Test cases for fixture manager."""

    @pytest.fixture
    def manager(self):
        """Create a test manager."""
        return FixtureManager()

    async def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert len(manager.fixtures) == 0
        assert len(manager.presets) == 0
        assert manager.active_preset is None

    async def test_register_fixture(self, manager):
        """Test fixture registration."""
        result = manager.register_fixture("stage_left", 1, 3)
        assert result is True
        assert "stage_left" in manager.fixtures

    async def test_register_fixture_invalid_range(self, manager):
        """Test registering fixture exceeding DMX range."""
        result = manager.register_fixture("test", 510, 5)
        assert result is False

    async def test_unregister_fixture(self, manager):
        """Test unregistering fixture."""
        manager.register_fixture("test", 1, 3)
        result = manager.unregister_fixture("test")
        assert result is True
        assert "test" not in manager.fixtures

    async def test_get_fixture(self, manager):
        """Test getting fixture."""
        manager.register_fixture("test", 1, 3)
        fixture = manager.get_fixture("test")
        assert fixture is not None
        assert fixture.fixture_id == "test"

    async def test_update_fixture(self, manager):
        """Test updating fixture."""
        manager.register_fixture("test", 1, 3)
        result = manager.update_fixture("test", [255, 200, 180], 0.8)
        assert result is True
        fixture = manager.get_fixture("test")
        assert fixture.channel_values == [255, 200, 180]
        assert fixture.intensity == 0.8

    async def test_get_fixture_values(self, manager):
        """Test getting fixture values."""
        manager.register_fixture("test", 5, 3)
        manager.update_fixture("test", [100, 150, 200])
        values = manager.get_fixture_values("test")
        assert values == {5: 100, 6: 150, 7: 200}

    async def test_get_all_values(self, manager):
        """Test getting all fixture values."""
        manager.register_fixture("f1", 1, 2)
        manager.register_fixture("f2", 5, 2)
        manager.update_fixture("f1", [100, 150])
        manager.update_fixture("f2", [200, 250])
        values = manager.get_all_values()
        assert values == {1: 100, 2: 150, 5: 200, 6: 250}

    async def test_create_preset(self, manager):
        """Test creating a preset."""
        request = PresetRequest(
            name="test_preset",
            description="Test preset",
            values={1: 255, 2: 200},
            fade_time=2.0
        )
        response = await manager.create_preset(request)
        assert response.saved is True
        assert response.name == "test_preset"
        assert "test_preset" in manager.presets

    async def test_create_duplicate_preset(self, manager):
        """Test creating duplicate preset."""
        request = PresetRequest(
            name="test",
            values={1: 255}
        )
        await manager.create_preset(request)

        response = await manager.create_preset(request)
        assert response.saved is False
        assert "already exists" in response.error_message

    async def test_update_preset(self, manager):
        """Test updating a preset."""
        request = PresetRequest(
            name="test",
            values={1: 255}
        )
        await manager.create_preset(request)

        update_request = PresetRequest(
            name="test",
            values={1: 200, 2: 180},
            fade_time=3.0
        )
        response = await manager.update_preset("test", update_request)
        assert response.saved is True
        assert manager.presets["test"].values == {1: 200, 2: 180}

    async def test_delete_preset(self, manager):
        """Test deleting a preset."""
        request = PresetRequest(
            name="test",
            values={1: 255}
        )
        await manager.create_preset(request)

        result = await manager.delete_preset("test")
        assert result is True
        assert "test" not in manager.presets

    async def test_get_preset(self, manager):
        """Test getting a preset."""
        request = PresetRequest(
            name="test",
            values={1: 255}
        )
        await manager.create_preset(request)

        preset = manager.get_preset("test")
        assert preset is not None
        assert preset.name == "test"

    async def test_get_all_presets(self, manager):
        """Test getting all presets."""
        await manager.create_preset(PresetRequest(name="p1", values={1: 255}))
        await manager.create_preset(PresetRequest(name="p2", values={2: 200}))

        presets = manager.get_all_presets()
        assert len(presets) == 2
        assert "p1" in presets
        assert "p2" in presets

    async def test_get_preset_names(self, manager):
        """Test getting preset names."""
        await manager.create_preset(PresetRequest(name="p1", values={1: 255}))
        await manager.create_preset(PresetRequest(name="p2", values={2: 200}))

        names = manager.get_preset_names()
        assert set(names) == {"p1", "p2"}

    async def test_set_active_preset(self, manager):
        """Test setting active preset."""
        result = manager.set_active_preset("test")
        assert result is False  # Doesn't exist

        await manager.create_preset(PresetRequest(name="test", values={1: 255}))
        result = manager.set_active_preset("test")
        assert result is True
        assert manager.active_preset == "test"

    async def test_clear_active_preset(self, manager):
        """Test clearing active preset."""
        manager.set_active_preset("test")
        manager.clear_active_preset()
        assert manager.active_preset is None

    async def test_create_from_current_state(self, manager):
        """Test creating preset from current state."""
        manager.register_fixture("f1", 1, 2)
        manager.update_fixture("f1", [150, 200])

        preset = manager.create_from_current_state(
            "snapshot",
            fade_time=1.0,
            description="Current state"
        )
        assert preset.name == "snapshot"
        assert preset.values == {1: 150, 2: 200}
        assert preset.fade_time == 1.0

    async def test_apply_preset(self, manager):
        """Test applying preset."""
        request = PresetRequest(
            name="test",
            values={1: 255, 2: 200},
            fade_time=2.0
        )
        await manager.create_preset(request)

        values = await manager.apply_preset("test")
        assert values == {1: 255, 2: 200}
        assert manager.active_preset == "test"

    async def test_apply_preset_with_fixtures(self, manager):
        """Test applying preset with fixture data."""
        manager.register_fixture("f1", 1, 3)

        request = PresetRequest(
            name="test",
            fixtures=[
                FixtureValues(fixture_id="f1", channels=[255, 200, 180])
            ],
            fade_time=2.0
        )
        await manager.create_preset(request)

        values = await manager.apply_preset("test")
        assert values == {1: 255, 2: 200, 3: 180}

    async def test_get_preset_fade_time(self, manager):
        """Test getting preset fade time."""
        request = PresetRequest(
            name="test",
            values={1: 255},
            fade_time=3.5
        )
        await manager.create_preset(request)

        fade_time = manager.get_preset_fade_time("test")
        assert fade_time == 3.5

    async def test_export_presets(self, manager):
        """Test exporting presets."""
        await manager.create_preset(PresetRequest(name="p1", values={1: 255}))

        exported = manager.export_presets()
        assert "p1" in exported
        assert exported["p1"]["name"] == "p1"

    async def test_import_presets(self, manager):
        """Test importing presets."""
        data = {
            "imported": {
                "name": "imported",
                "values": {1: 100},
                "fixtures": [],
                "fade_time": 0.0,
                "description": "",
                "created_at": "2024-01-01T00:00:00"
            }
        }

        count = await manager.import_presets(data)
        assert count == 1
        assert "imported" in manager.presets


@pytest.mark.unit
class TestPreset:
    """Test cases for Preset class."""

    def test_preset_creation(self):
        """Test creating a preset."""
        preset = Preset(
            name="test",
            values={1: 255},
            fixtures=[],
            fade_time=2.0,
            description="Test preset"
        )
        assert preset.name == "test"
        assert preset.values == {1: 255}
        assert preset.fade_time == 2.0

    def test_preset_to_dict(self):
        """Test converting preset to dictionary."""
        preset = Preset(
            name="test",
            values={1: 255},
            fixtures=[],
            fade_time=2.0
        )
        data = preset.to_dict()
        assert data["name"] == "test"
        assert data["values"] == {1: 255}
        assert "created_at" in data

    def test_preset_from_dict(self):
        """Test creating preset from dictionary."""
        data = {
            "name": "test",
            "values": {1: 255},
            "fixtures": [],
            "fade_time": 2.0,
            "description": "Test"
        }
        preset = Preset.from_dict(data)
        assert preset.name == "test"
        assert preset.values == {1: 255}
        assert preset.fade_time == 2.0
