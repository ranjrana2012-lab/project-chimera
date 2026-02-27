"""Unit tests for Lighting Control base models."""

import pytest
from datetime import datetime, timezone

from services.lighting_control.src.models.request import (
    LightingRequest,
    FixtureValues,
    PresetRequest,
    CueRequest,
    OSCMessageRequest
)
from services.lighting_control.src.models.response import (
    LightingStatus,
    LightingResponse,
    FixtureState,
    LightingState,
    PresetResponse,
    CueResponse,
    OSCResponse,
    HealthResponse
)


@pytest.mark.unit
class TestLightingRequest:
    """Test cases for LightingRequest model."""

    def test_valid_request_minimal(self):
        """Test creating a valid request with minimal fields."""
        request = LightingRequest(values={1: 255, 2: 200})
        assert request.universe == 1
        assert request.values == {1: 255, 2: 200}
        assert request.fade_time == 0.0
        assert request.priority == 100

    def test_universe_validation(self):
        """Test universe validation."""
        with pytest.raises(ValueError):
            LightingRequest(universe=0, values={1: 255})

        with pytest.raises(ValueError):
            LightingRequest(universe=64000, values={1: 255})

    def test_valid_universe_boundaries(self):
        """Test universe boundary values."""
        request = LightingRequest(universe=1, values={1: 255})
        assert request.universe == 1

        request = LightingRequest(universe=63999, values={1: 255})
        assert request.universe == 63999

    def test_fade_time_validation(self):
        """Test fade_time validation."""
        with pytest.raises(ValueError):
            LightingRequest(values={1: 255}, fade_time=-1.0)

        with pytest.raises(ValueError):
            LightingRequest(values={1: 255}, fade_time=4000.0)

    def test_priority_validation(self):
        """Test priority validation."""
        with pytest.raises(ValueError):
            LightingRequest(values={1: 255}, priority=201)

        request = LightingRequest(values={1: 255}, priority=0)
        assert request.priority == 0

        request = LightingRequest(values={1: 255}, priority=200)
        assert request.priority == 200

    def test_full_request(self):
        """Test request with all fields."""
        request = LightingRequest(
            universe=5,
            fixture_addresses={"stage_left": 1, "stage_right": 5},
            values={1: 255, 2: 200, 5: 255},
            fade_time=2.5,
            priority=150
        )
        assert request.universe == 5
        assert request.fixture_addresses == {"stage_left": 1, "stage_right": 5}
        assert request.values == {1: 255, 2: 200, 5: 255}
        assert request.fade_time == 2.5
        assert request.priority == 150


@pytest.mark.unit
class TestFixtureValues:
    """Test cases for FixtureValues model."""

    def test_valid_fixture_values(self):
        """Test creating valid fixture values."""
        fixture = FixtureValues(
            fixture_id="stage_left",
            channels=[255, 200, 180],
            intensity=0.8
        )
        assert fixture.fixture_id == "stage_left"
        assert fixture.channels == [255, 200, 180]
        assert fixture.intensity == 0.8

    def test_intensity_validation(self):
        """Test intensity validation."""
        with pytest.raises(ValueError):
            FixtureValues(fixture_id="test", channels=[], intensity=-0.1)

        with pytest.raises(ValueError):
            FixtureValues(fixture_id="test", channels=[], intensity=1.1)

    def test_default_intensity(self):
        """Test default intensity value."""
        fixture = FixtureValues(fixture_id="test", channels=[255])
        assert fixture.intensity == 1.0


@pytest.mark.unit
class TestPresetRequest:
    """Test cases for PresetRequest model."""

    def test_valid_preset(self):
        """Test creating a valid preset request."""
        request = PresetRequest(
            name="warm_intimate",
            description="Warm intimate scene",
            values={1: 200, 2: 180},
            fade_time=3.0
        )
        assert request.name == "warm_intimate"
        assert request.description == "Warm intimate scene"
        assert request.values == {1: 200, 2: 180}
        assert request.fade_time == 3.0

    def test_name_validation(self):
        """Test name validation."""
        with pytest.raises(ValueError):
            PresetRequest(name="", values={1: 255})

        with pytest.raises(ValueError):
            PresetRequest(name="a" * 101, values={1: 255})

    def test_description_validation(self):
        """Test description validation."""
        with pytest.raises(ValueError):
            PresetRequest(
                name="test",
                description="a" * 501,
                values={1: 255}
            )

    def test_preset_with_fixtures(self):
        """Test preset with fixture configurations."""
        request = PresetRequest(
            name="full_stage",
            fixtures=[
                FixtureValues(fixture_id="stage_left", channels=[255, 200, 180]),
                FixtureValues(fixture_id="stage_right", channels=[255, 200, 180])
            ]
        )
        assert len(request.fixtures) == 2


@pytest.mark.unit
class TestCueRequest:
    """Test cases for CueRequest model."""

    def test_valid_cue(self):
        """Test creating a valid cue request."""
        request = CueRequest(
            cue_number="1",
            cue_list="main",
            preset_name="warm_intimate",
            fade_time=2.0
        )
        assert request.cue_number == "1"
        assert request.cue_list == "main"
        assert request.preset_name == "warm_intimate"
        assert request.fade_time == 2.0

    def test_delay_validation(self):
        """Test delay_secs validation."""
        with pytest.raises(ValueError):
            CueRequest(cue_number="1", delay_secs=-1.0)

    def test_default_values(self):
        """Test default cue values."""
        request = CueRequest(cue_number="1")
        assert request.cue_list == "main"
        assert request.delay_secs == 0.0
        assert request.follow_on is False


@pytest.mark.unit
class TestOSCMessageRequest:
    """Test cases for OSCMessageRequest model."""

    def test_valid_osc_message(self):
        """Test creating a valid OSC message."""
        request = OSCMessageRequest(
            address="/lighting/fixture/1/intensity",
            arguments=[0.8]
        )
        assert request.address == "/lighting/fixture/1/intensity"
        assert request.arguments == [0.8]
        assert request.port == 9000

    def test_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValueError):
            OSCMessageRequest(address="/test", port=0)

        with pytest.raises(ValueError):
            OSCMessageRequest(address="/test", port=70000)


@pytest.mark.unit
class TestLightingResponse:
    """Test cases for LightingResponse model."""

    def test_successful_response(self):
        """Test successful lighting response."""
        response = LightingResponse(
            status=LightingStatus.SUCCESS,
            affected_fixtures=["stage_left", "stage_right"],
            timing={"fade": 2.0, "total": 2.1},
            universe=1,
            channels_updated=6
        )
        assert response.status == LightingStatus.SUCCESS
        assert len(response.affected_fixtures) == 2
        assert response.channels_updated == 6

    def test_failed_response(self):
        """Test failed lighting response."""
        response = LightingResponse(
            status=LightingStatus.FAILED,
            affected_fixtures=[],
            timing={},
            universe=1,
            channels_updated=0,
            error_message="sACN connection failed"
        )
        assert response.status == LightingStatus.FAILED
        assert response.error_message == "sACN connection failed"


@pytest.mark.unit
class TestFixtureState:
    """Test cases for FixtureState model."""

    def test_valid_fixture_state(self):
        """Test creating valid fixture state."""
        state = FixtureState(
            fixture_id="stage_left",
            dmx_address=1,
            channel_values=[255, 200, 180],
            intensity=0.9
        )
        assert state.fixture_id == "stage_left"
        assert state.dmx_address == 1
        assert state.channel_values == [255, 200, 180]
        assert state.intensity == 0.9

    def test_dmx_address_validation(self):
        """Test DMX address validation."""
        with pytest.raises(ValueError):
            FixtureState(fixture_id="test", dmx_address=0, channel_values=[])

        with pytest.raises(ValueError):
            FixtureState(fixture_id="test", dmx_address=513, channel_values=[])


@pytest.mark.unit
class TestLightingState:
    """Test cases for LightingState model."""

    def test_valid_lighting_state(self):
        """Test creating valid lighting state."""
        state = LightingState(
            universe=1,
            dmx_values=[255, 200, 180] + [0] * 509,
            fixtures={
                "stage_left": FixtureState(
                    fixture_id="stage_left",
                    dmx_address=1,
                    channel_values=[255, 200, 180],
                    intensity=0.9
                )
            },
            active_preset="warm_intimate",
            sACN_active=True,
            OSC_active=True
        )
        assert state.universe == 1
        assert len(state.fixtures) == 1
        assert state.active_preset == "warm_intimate"
        assert state.sACN_active is True


@pytest.mark.unit
class TestPresetResponse:
    """Test cases for PresetResponse model."""

    def test_saved_preset(self):
        """Test successfully saved preset response."""
        response = PresetResponse(
            name="warm_intimate",
            saved=True,
            values={1: 200, 2: 180},
            fixtures=[],
            fade_time=3.0
        )
        assert response.name == "warm_intimate"
        assert response.saved is True

    def test_failed_preset(self):
        """Test failed preset save response."""
        response = PresetResponse(
            name="test",
            saved=False,
            error_message="Preset already exists"
        )
        assert response.saved is False
        assert response.error_message == "Preset already exists"


@pytest.mark.unit
class TestCueResponse:
    """Test cases for CueResponse model."""

    def test_executed_cue(self):
        """Test successfully executed cue response."""
        response = CueResponse(
            cue_number="1",
            executed=True,
            status="completed",
            preset_used="warm_intimate",
            timing={"delay": 0.5, "fade": 2.0, "total": 2.5}
        )
        assert response.cue_number == "1"
        assert response.executed is True
        assert response.status == "completed"


@pytest.mark.unit
class TestOSCResponse:
    """Test cases for OSCResponse model."""

    def test_sent_osc(self):
        """Test successfully sent OSC response."""
        response = OSCResponse(
            sent=True,
            address="/lighting/test",
            port=9000
        )
        assert response.sent is True
        assert response.address == "/lighting/test"


@pytest.mark.unit
class TestHealthResponse:
    """Test cases for HealthResponse model."""

    def test_healthy_response(self):
        """Test healthy response."""
        response = HealthResponse(
            status="healthy",
            sACN_connected=True,
            OSC_connected=True,
            uptime_seconds=3600.0,
            active_fixtures=3,
            active_presets=5
        )
        assert response.status == "healthy"
        assert response.sACN_connected is True
        assert response.active_fixtures == 3
