"""Context models for WorldMonitor integration."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ThreatLevel(str, Enum):
    """Threat level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ThreatType(str, Enum):
    """Threat type classification."""
    CONFLICT = "conflict"
    CIVIL_UNREST = "civil_unrest"
    SECURITY = "security"
    NATURAL_DISASTER = "natural_disaster"
    OTHER = "other"


class Threat(BaseModel):
    """Threat information."""
    level: ThreatLevel = Field(..., description="Threat level")
    type: ThreatType = Field(..., description="Threat type")
    title: str = Field(..., description="Threat headline")
    source: str = Field(..., description="News source")
    location: str = Field(..., description="Geographic location")


class CountryContext(BaseModel):
    """Country-specific context."""
    country_code: str = Field(..., description="ISO country code")
    country_cii: int = Field(..., ge=0, le=100, description="CII score")
    trend: str = Field(..., description="Stability trend")
    recent_events: List[str] = Field(
        default_factory=list,
        description="Recent events in country"
    )
    news_summary: str = Field(
        ...,
        description="AI-generated news summary"
    )
    instability_factors: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contributing factors"
    )


class GlobalContext(BaseModel):
    """Global context information."""
    global_cii: int = Field(..., ge=0, le=100, description="Global CII")
    country_summary: Dict[str, CountryContext] = Field(
        default_factory=dict,
        description="Country-specific contexts"
    )
    active_threats: List[Threat] = Field(
        default_factory=list,
        description="Active threats"
    )
    major_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Major global events"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    stale: Optional[bool] = Field(
        default=False,
        description="Whether data is stale"
    )


class ContextEnrichmentOptions(BaseModel):
    """Options for context enrichment."""
    include_context: Optional[bool] = Field(
        default=True,
        description="Include global context"
    )
    include_threats: Optional[bool] = Field(
        default=True,
        description="Include threat information"
    )
    include_events: Optional[bool] = Field(
        default=True,
        description="Include major events"
    )
    include_cii: Optional[bool] = Field(
        default=True,
        description="Include CII scores"
    )
    country_code: Optional[str] = Field(
        default=None,
        description="Specific country code for context"
    )


class NewsSentimentRequest(BaseModel):
    """Request for news sentiment analysis."""
    sources: Optional[List[str]] = Field(
        default=None,
        description="News source names"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="News categories"
    )
    hours: Optional[int] = Field(
        default=24,
        ge=1,
        le=168,
        description="Time window in hours"
    )
    max_articles: Optional[int] = Field(
        default=500,
        ge=1,
        le=1000,
        description="Maximum articles to analyze"
    )


class NewsSentimentResponse(BaseModel):
    """Response from news sentiment analysis."""
    analyzed_articles: int = Field(..., description="Number analyzed")
    average_sentiment: str = Field(..., description="Average sentiment")
    sentiment_distribution: Dict[str, int] = Field(
        ...,
        description="Count of each sentiment type"
    )
    top_positive: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most positive articles"
    )
    top_negative: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most negative articles"
    )
    processing_time_ms: float = Field(..., description="Processing time")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )
