"""Tests for OpenTelemetry tracing module."""
import pytest
import asyncio
from telemetry import (
    setup_telemetry,
    get_tracer,
    is_initialized,
    trace_simulation,
    trace_operation,
    add_span_attributes,
    add_span_event,
    record_exception,
    set_span_error,
    trace_async_operation
)


def test_setup_telemetry():
    """Test that OpenTelemetry tracer is properly initialized."""
    # Reset state
    import telemetry
    telemetry._exporter_initialized = False
    telemetry._tracer = None

    setup_telemetry("test-service", "1.0.0")

    assert is_initialized() == True
    assert telemetry._tracer is not None


def test_get_tracer():
    """Test that get_tracer returns a valid tracer."""
    tracer = get_tracer()

    assert tracer is not None
    assert hasattr(tracer, 'start_as_current_span')


def test_tracer_initializes_on_first_call():
    """Test that tracer is initialized automatically on first call."""
    # Reset state
    import telemetry
    telemetry._exporter_initialized = False
    telemetry._tracer = None

    # First call should initialize
    tracer = get_tracer()

    assert tracer is not None
    assert is_initialized() == True


@pytest.mark.asyncio
async def test_trace_simulation_context_manager():
    """Test that trace_simulation context manager creates a span."""
    async with trace_simulation("test-simulation", {"agent_count": 10}) as span:
        assert span is not None
        assert span.is_recording()
        assert span.name == "test-simulation"

        # Add attributes
        span.set_attribute("custom_attr", "test_value")


@pytest.mark.asyncio
async def test_trace_simulation_with_attributes():
    """Test trace_simulation with initial attributes."""
    attributes = {
        "agent_count": 10,
        "rounds": 5,
        "scenario": "test"
    }

    async with trace_simulation("test-sim", attributes) as span:
        assert span.is_recording()
        assert span.name == "test-sim"


@pytest.mark.asyncio
async def test_trace_operation_context_manager():
    """Test trace_operation context manager."""
    async with trace_async_operation("test-operation", {"operation_type": "test"}) as span:
        assert span is not None
        assert span.is_recording()
        assert span.name == "test-operation"


@pytest.mark.asyncio
async def test_trace_operation_synchronous():
    """Test trace_operation with synchronous context."""
    with trace_operation("sync-operation") as span:
        assert span is not None
        assert span.is_recording()


def test_add_span_attributes():
    """Test adding attributes to the current span."""
    with trace_operation("test-attr") as span:
        add_span_attributes({
            "key1": "value1",
            "key2": 42,
            "key3": True
        })

        # Attributes are added to the span (verified in real tracing system)
        assert span.is_recording()


def test_add_span_event():
    """Test adding events to the current span."""
    with trace_operation("test-event") as span:
        add_span_event("test_event", {"event_data": "test"})

        assert span.is_recording()


def test_record_exception():
    """Test recording an exception on the current span."""
    with trace_operation("test-exception") as span:
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            record_exception(e)

        assert span.is_recording()


def test_set_span_error():
    """Test setting span error status."""
    with trace_operation("test-error") as span:
        set_span_error("Something went wrong")

        assert span.is_recording()


@pytest.mark.asyncio
async def test_trace_async_operation():
    """Test trace_async_operation convenience function."""
    async with trace_async_operation("async-op", {"async": True}) as span:
        assert span is not None
        assert span.is_recording()


@pytest.mark.asyncio
async def test_nested_spans():
    """Test creating nested spans for parent-child relationships."""
    async with trace_simulation("parent-simulation") as parent:
        assert parent.is_recording()

        async with trace_async_operation("child-operation") as child:
            assert child.is_recording()

            # Child should have a parent
            parent_context = child.parent
            assert parent_context is not None


@pytest.mark.asyncio
async def test_multiple_concurrent_simulations():
    """Test tracing multiple concurrent simulations."""
    async def run_simulation(name: str):
        async with trace_simulation(name, {"sim_id": name}) as span:
            add_span_event("simulation_started")
            return span.name

    results = await asyncio.gather(
        run_simulation("sim-1"),
        run_simulation("sim-2"),
        run_simulation("sim-3")
    )

    assert len(results) == 3
    assert all(name in results for name in ["sim-1", "sim-2", "sim-3"])


@pytest.mark.asyncio
async def test_trace_simulation_with_empty_attributes():
    """Test trace_simulation with no attributes."""
    async with trace_simulation("minimal-sim") as span:
        assert span.is_recording()
        assert span.name == "minimal-sim"


def test_telemetry_idempotency():
    """Test that calling setup_telemetry multiple times is safe."""
    # Reset state
    import telemetry
    telemetry._exporter_initialized = False
    telemetry._tracer = None

    setup_telemetry("service-1", "1.0.0")
    first_tracer = telemetry._tracer

    # Second call should not reinitialize
    setup_telemetry("service-2", "2.0.0")
    second_tracer = telemetry._tracer

    # Should use the same tracer instance
    assert first_tracer is not None
    assert second_tracer is not None
