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
