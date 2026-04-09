# DMX Controller Service

Project Chimera Phase 2 - DMX512 lighting control service for live theatrical performances.

## Overview

The DMX Controller Service provides safe DMX512 lighting control with emergency stop functionality for live theatrical performances. It manages DMX fixtures, scenes, and provides real-time control with safety features.

## Features

- **DMX512 Protocol Support**: Full DMX512 protocol implementation (512 channels)
- **Fixture Management**: Add, configure, and control multiple lighting fixtures
- **Scene Control**: Create and activate lighting scenes with transitions
- **Emergency Stop**: Instant blackout functionality for safety
- **Safe Defaults**: Automatic reset to safe levels after emergency stop
- **Callback System**: Register callbacks for emergency events

## Installation

```bash
# Install dependencies
pip install -e .[dmx]

# Or install with all Phase 2 dependencies
pip install -e .[all]
```

## Quick Start

```python
from dmx_controller import DMXController, DMXChannel, Fixture

# Create controller
controller = DMXController(universe=1, refresh_rate=44)

# Create a fixture
channels = {
    1: DMXChannel(1, 0, "intensity"),
    2: DMXChannel(2, 0, "pan"),
    3: DMXChannel(3, 0, "tilt"),
    4: DMXChannel(4, 0, "color_red"),
    5: DMXChannel(5, 0, "color_green"),
    6: DMXChannel(6, 0, "color_blue"),
}
fixture = Fixture(
    id="mh_1",
    name="Moving Head 1",
    start_address=1,
    channel_count=6,
    channels=channels
)

# Add fixture and control
controller.add_fixture(fixture)
controller.set_fixture_channel("mh_1", 1, 255)  # Full intensity
controller.set_fixture_channels("mh_1", {
    4: 255,  # Red
    5: 0,    # Green
    6: 0     # Blue
})
```

## Usage Examples

See `examples/dmx_example.py` for comprehensive usage examples including:
- Basic fixture control
- Scene creation and activation
- Emergency stop functionality
- Status monitoring

Run the example:
```bash
cd services/dmx-controller
python examples/dmx_example.py
```

## Testing

```bash
# Run all tests
pytest tests/test_dmx_controller.py -v

# Run with coverage
pytest tests/test_dmx_controller.py --cov=dmx_controller --cov-report=html

# Run specific test
pytest tests/test_dmx_controller.py::TestDMXController::test_emergency_stop -v
```

## API Reference

### DMXController

Main controller class for DMX512 lighting control.

**Parameters:**
- `universe` (int): DMX universe number (1-512)
- `refresh_rate` (int): Refresh rate in Hz (default: 44)

**Methods:**
- `add_fixture(fixture)`: Add a fixture to the controller
- `remove_fixture(fixture_id)`: Remove a fixture
- `set_fixture_channel(fixture_id, channel, value)`: Set single channel value
- `set_fixture_channels(fixture_id, channels)`: Set multiple channel values
- `create_scene(name, fixture_values, transition_time_ms)`: Create a lighting scene
- `activate_scene(scene_name)`: Activate a lighting scene
- `emergency_stop()`: Activate emergency stop (instant blackout)
- `reset_from_emergency()`: Reset from emergency stop state
- `get_status()`: Get controller status

### Fixture

Represents a DMX lighting fixture.

**Attributes:**
- `id` (str): Fixture identifier
- `name` (str): Fixture name
- `start_address` (int): DMX start address
- `channel_count` (int): Number of channels
- `channels` (dict): Channel mapping

### Scene

Represents a lighting scene.

**Attributes:**
- `name` (str): Scene name
- `fixtures` (dict): Fixture values
- `transition_time_ms` (int): Transition time in milliseconds

## Safety Features

### Emergency Stop

The emergency stop feature provides instant blackout for safety:

```python
# Activate emergency stop
controller.emergency_stop()

# All channels set to 0
# System state = EMERGENCY_STOP
# Commands are blocked until reset

# Reset from emergency
controller.reset_from_emergency()
```

### Safe Defaults

After emergency stop reset, fixtures return to safe defaults:
- Intensity channels: 50% (128)
- Other channels: Previous values
- Volume limits enforced

### Volume Limits

Channel values are automatically clamped to safe ranges:
- Minimum: 0
- Maximum: 255

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=dmx_controller --cov-report=term-missing
```

### Code Formatting

```bash
# Format code
black dmx_controller.py

# Check linting
ruff check dmx_controller.py

# Type checking
mypy dmx_controller.py
```

## Hardware Requirements

### DMX Interface

- DMX512 USB interface or compatible hardware
- Driver support for your operating system
- DMX cables and terminators

### Lighting Fixtures

- DMX512-compatible lighting fixtures
- Proper addressing configuration
- Power distribution appropriate for fixtures

## Configuration

### Environment Variables

No environment variables required for basic operation.

### DMX Universe

Default: Universe 1
Range: 1-512

### Refresh Rate

Default: 44 Hz
Range: 1-100 Hz (typical: 30-44 Hz)

## Troubleshooting

### Fixtures not responding

1. Check DMX interface connection
2. Verify fixture start addresses
3. Check channel mappings
4. Ensure DMX terminator is installed

### Emergency stop not resetting

1. Check if system is in EMERGENCY_STOP state
2. Call `reset_from_emergency()` explicitly
3. Verify no hardware issues

### Commands blocked

If commands are blocked:
1. Check controller state with `get_status()`
2. If in EMERGENCY_STOP, call `reset_from_emergency()`
3. Check for error messages in logs

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/ranjrana2012-lab/project-chimera
- Issues: https://github.com/ranjrana2012-lab/project-chimera/issues

## Project Chimera

This service is part of Project Chimera, an AI-powered adaptive live theatre framework.

For more information:
- Documentation: https://github.com/ranjrana2012-lab/project-chimera/docs
- Phase 2 Plan: See `docs/PHASE_2_IMPLEMENTATION_PLAN.md`
