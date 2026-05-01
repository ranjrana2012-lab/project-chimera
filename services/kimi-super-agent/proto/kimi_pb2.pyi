from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ContentType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TEXT: _ClassVar[ContentType]
    IMAGE: _ClassVar[ContentType]
    VIDEO: _ClassVar[ContentType]
    AUDIO: _ClassVar[ContentType]

class CapabilityHint(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[CapabilityHint]
    LONG_CONTEXT: _ClassVar[CapabilityHint]
    MULTIMODAL: _ClassVar[CapabilityHint]
    AGENTIC_CODING: _ClassVar[CapabilityHint]
TEXT: ContentType
IMAGE: ContentType
VIDEO: ContentType
AUDIO: ContentType
NONE: CapabilityHint
LONG_CONTEXT: CapabilityHint
MULTIMODAL: CapabilityHint
AGENTIC_CODING: CapabilityHint

class DelegationRequest(_message.Message):
    __slots__ = ("request_id", "user_input", "multimodal_content", "context", "capability_hint")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    USER_INPUT_FIELD_NUMBER: _ClassVar[int]
    MULTIMODAL_CONTENT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    CAPABILITY_HINT_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    user_input: str
    multimodal_content: _containers.RepeatedCompositeFieldContainer[MultimodalContent]
    context: ContextMetadata
    capability_hint: CapabilityHint
    def __init__(self, request_id: _Optional[str] = ..., user_input: _Optional[str] = ..., multimodal_content: _Optional[_Iterable[_Union[MultimodalContent, _Mapping]]] = ..., context: _Optional[_Union[ContextMetadata, _Mapping]] = ..., capability_hint: _Optional[_Union[CapabilityHint, str]] = ...) -> None: ...

class MultimodalContent(_message.Message):
    __slots__ = ("type", "data", "mime_type", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    type: ContentType
    data: bytes
    mime_type: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, type: _Optional[_Union[ContentType, str]] = ..., data: _Optional[bytes] = ..., mime_type: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ContextMetadata(_message.Message):
    __slots__ = ("session_id", "timestamp", "performance_state")
    class PerformanceStateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PERFORMANCE_STATE_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    timestamp: int
    performance_state: _containers.ScalarMap[str, str]
    def __init__(self, session_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., performance_state: _Optional[_Mapping[str, str]] = ...) -> None: ...

class DelegationResponse(_message.Message):
    __slots__ = ("request_id", "response", "agents_used", "generated_code", "metadata")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    AGENTS_USED_FIELD_NUMBER: _ClassVar[int]
    GENERATED_CODE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    response: str
    agents_used: _containers.RepeatedCompositeFieldContainer[AgentInvocation]
    generated_code: GeneratedCode
    metadata: ResponseMetadata
    def __init__(self, request_id: _Optional[str] = ..., response: _Optional[str] = ..., agents_used: _Optional[_Iterable[_Union[AgentInvocation, _Mapping]]] = ..., generated_code: _Optional[_Union[GeneratedCode, _Mapping]] = ..., metadata: _Optional[_Union[ResponseMetadata, _Mapping]] = ...) -> None: ...

class AgentInvocation(_message.Message):
    __slots__ = ("agent_name", "agent_type", "duration_ms", "success")
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    AGENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    agent_name: str
    agent_type: str
    duration_ms: int
    success: bool
    def __init__(self, agent_name: _Optional[str] = ..., agent_type: _Optional[str] = ..., duration_ms: _Optional[int] = ..., success: bool = ...) -> None: ...

class GeneratedCode(_message.Message):
    __slots__ = ("code", "language", "description")
    CODE_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    code: str
    language: str
    description: str
    def __init__(self, code: _Optional[str] = ..., language: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class ResponseMetadata(_message.Message):
    __slots__ = ("tokens_processed", "processing_time_ms", "delegated_to_kimi", "model_version")
    TOKENS_PROCESSED_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    DELEGATED_TO_KIMI_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    tokens_processed: int
    processing_time_ms: int
    delegated_to_kimi: bool
    model_version: str
    def __init__(self, tokens_processed: _Optional[int] = ..., processing_time_ms: _Optional[int] = ..., delegated_to_kimi: bool = ..., model_version: _Optional[str] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("healthy", "message")
    HEALTHY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    healthy: bool
    message: str
    def __init__(self, healthy: bool = ..., message: _Optional[str] = ...) -> None: ...
