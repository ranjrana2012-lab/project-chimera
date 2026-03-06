# metrics.py
"""Prometheus metrics for Captioning Agent"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time


# Request metrics
request_count = Counter(
    'captioning_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'captioning_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Captioning business metrics
transcription_count = Counter(
    'captioning_transcriptions_total',
    'Total audio transcriptions',
    ['status', 'language']
)

transcription_duration = Histogram(
    'captioning_transcription_duration_seconds',
    'Audio transcription duration',
    ['model_size']
)

audio_duration = Histogram(
    'captioning_audio_duration_seconds',
    'Processed audio duration',
    ['model_size']
)

websocket_connections = Gauge(
    'captioning_websocket_connections',
    'Current WebSocket connections'
)

websocket_messages = Counter(
    'captioning_websocket_messages_total',
    'Total WebSocket messages',
    ['message_type', 'direction']
)

# Whisper model metrics
model_load_time = Histogram(
    'captioning_model_load_seconds',
    'Time to load Whisper model',
    ['model_size']
)

model_info = Info(
    'captioning_model',
    'Whisper model information'
)

# Service info
service_info = Info(
    'captioning_service',
    'Captioning service information'
)


def init_service_info(service_name: str, version: str = "1.0.0"):
    """Initialize service info metric"""
    service_info.info({
        'name': service_name,
        'version': version,
        'component': 'captioning'
    })


def init_model_info(model_size: str, device: str):
    """Initialize model info metric"""
    model_info.info({
        'model_size': model_size,
        'device': device
    })


def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    request_count.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()
    request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_transcription(status: str, language: str, duration: float, audio_len: float, model_size: str):
    """Record transcription metrics"""
    transcription_count.labels(
        status=status,
        language=language
    ).inc()
    transcription_duration.labels(
        model_size=model_size
    ).observe(duration)
    audio_duration.labels(
        model_size=model_size
    ).observe(audio_len)


def record_websocket_connection(delta: int):
    """Record WebSocket connection change"""
    websocket_connections.inc(delta)


def record_websocket_message(message_type: str, direction: str):
    """Record WebSocket message"""
    websocket_messages.labels(
        message_type=message_type,
        direction=direction
    ).inc()
