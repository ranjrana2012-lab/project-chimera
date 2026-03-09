"""
Pydantic models for Sentiment Agent.

Defines request/response models for sentiment analysis with rule-based
and ML model support.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class AnalyzeRequest(BaseModel):
    """Request for sentiment analysis"""
    text: str = Field(..., min_length=0, description="Text to analyze for sentiment")


class BatchRequest(BaseModel):
    """Request for batch sentiment analysis"""
    texts: List[str] = Field(..., min_length=0, description="List of texts to analyze")


class EmotionScores(BaseModel):
    """Emotion scores from sentiment analysis"""
    joy: float = Field(..., ge=0.0, le=1.0)
    surprise: float = Field(..., ge=0.0, le=1.0)
    neutral: float = Field(..., ge=0.0, le=1.0)
    sadness: float = Field(..., ge=0.0, le=1.0)
    anger: float = Field(..., ge=0.0, le=1.0)
    fear: float = Field(..., ge=0.0, le=1.0)


class SentimentResponse(BaseModel):
    """Response from sentiment analysis"""
    sentiment: str = Field(..., description="Sentiment classification: positive, negative, or neutral")
    score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 (negative) to 1 (positive)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0 to 1")
    emotions: Dict[str, float] = Field(..., description="Emotion scores for each emotion type")


class BatchResponse(BaseModel):
    """Response from batch sentiment analysis"""
    results: List[SentimentResponse] = Field(..., description="List of sentiment analysis results")


class ModelInfo(BaseModel):
    """Model information"""
    name: str
    loaded: bool
    version: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    model_available: bool
    model_info: Optional[ModelInfo] = None


class LivenessResponse(BaseModel):
    """Liveness probe response"""
    status: str


class ReadinessResponse(BaseModel):
    """Readiness probe response"""
    status: str
    service: str
    model_available: bool
