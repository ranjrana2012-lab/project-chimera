class MusicServiceError(Exception):
    """Base exception for music service errors"""
    pass


class ModelNotFoundError(MusicServiceError):
    """Requested model not available"""
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Model '{model_name}' not found in pool")


class InsufficientVRAMError(MusicServiceError):
    """Not enough GPU memory to load/generate"""
    def __init__(self, required_mb: int, available_mb: int):
        self.required_mb = required_mb
        self.available_mb = available_mb
        super().__init__(
            f"Insufficient VRAM: need {required_mb}MB, have {available_mb}MB"
        )


class GenerationTimeoutError(MusicServiceError):
    """Generation exceeded maximum duration"""
    def __init__(self, duration_seconds: int, max_seconds: int):
        self.duration_seconds = duration_seconds
        self.max_seconds = max_seconds
        super().__init__(
            f"Generation timeout: {duration_seconds}s > {max_seconds}s limit"
        )


class InvalidPromptError(MusicServiceError):
    """Prompt contains blocked content or exceeds length"""
    def __init__(self, reason: str):
        super().__init__(f"Invalid prompt: {reason}")


class ApprovalRequiredError(MusicServiceError):
    """Show music requires manual approval before use"""
    def __init__(self, music_id: str):
        self.music_id = music_id
        super().__init__(f"Music {music_id} requires approval before show use")


class UnauthorizedError(MusicServiceError):
    """User lacks required permission"""
    def __init__(self, required_permission: str):
        super().__init__(f"Unauthorized: requires '{required_permission}' permission")
