"""Pydantic models for Visual Core service"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Resolution(str, Enum):
    """Video resolution options"""
    HD = "1920x1080"
    FHD = "1920x1080"
    UHD = "3840x2160"
    FOUR_K = "3840x2160"


class LTXModel(str, Enum):
    """LTX-2 model options"""
    PRO = "ltx-2-3-pro"
    FAST = "ltx-2-fast"


class CameraMotion(str, Enum):
    """Camera motion options"""
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACK_LEFT = "track_left"
    TRACK_RIGHT = "track_right"


class LTXVideoRequest(BaseModel):
    """Request for LTX-2 video generation"""
    prompt: str = Field(..., description="Text prompt for video generation")
    duration: int = Field(default=10, ge=6, le=20, description="Video duration in seconds")
    resolution: Resolution = Field(default=Resolution.HD, description="Video resolution")
    fps: int = Field(default=24, ge=24, le=50, description="Frames per second")
    model: LTXModel = Field(default=LTXModel.PRO, description="LTX-2 model to use")
    generate_audio: bool = Field(default=True, description="Generate synchronized audio")
    camera_motion: Optional[CameraMotion] = Field(None, description="Camera movement")
    lora_id: Optional[str] = Field(None, description="LoRA model to apply")


class LTXVideoResult(BaseModel):
    """Result from LTX-2 video generation"""
    video_id: str
    url: str
    duration: float
    resolution: str
    fps: int
    has_audio: bool
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoGenerationRequest(BaseModel):
    """API request for video generation"""
    prompt: str
    duration: int = 10
    resolution: str = "1920x1080"
    fps: int = 24
    model: str = "ltx-2-3-pro"
    generate_audio: bool = True
    camera_motion: Optional[str] = None
    lora_id: Optional[str] = None


class VideoGenerationResponse(BaseModel):
    """API response for video generation"""
    request_id: str
    video_id: str
    status: str
    url: Optional[str] = None
    error: Optional[str] = None


class BatchGenerationRequest(BaseModel):
    """Request for batch video generation"""
    requests: List[VideoGenerationRequest]


class BatchGenerationResponse(BaseModel):
    """Response for batch video generation"""
    batch_id: str
    requests: List[VideoGenerationResponse]
