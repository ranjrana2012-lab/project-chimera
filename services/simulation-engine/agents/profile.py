from pydantic import BaseModel
from typing import List, Dict, Any
from enum import Enum


class MBTIType(str, Enum):
    """Myers-Briggs Type Indicator personality types."""
    INTJ = "INTJ"
    INTP = "INTP"
    ENTJ = "ENTJ"
    ENTP = "ENTP"
    INFJ = "INFJ"
    INFP = "INFP"
    ENFJ = "ENFJ"
    ENFP = "ENFP"
    ISTJ = "ISTJ"
    ISFJ = "ISFJ"
    ESTJ = "ESTJ"
    ESFJ = "ESFJ"
    ISTP = "ISTP"
    ISFP = "ISFP"
    ESTP = "ESTP"
    ESFP = "ESFP"


class PoliticalLeaning(str, Enum):
    """Political orientation categories."""
    FAR_LEFT = "far_left"
    LEFT = "left"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    RIGHT = "right"
    FAR_RIGHT = "far_right"


class Demographics(BaseModel):
    """Demographic characteristics."""
    age: int
    gender: str
    education: str
    occupation: str
    location: str
    income_level: str


class BehavioralProfile(BaseModel):
    """Behavioral tendencies and personality traits."""
    openness: float  # 0-1
    conscientiousness: float  # 0-1
    extraversion: float  # 0-1
    agreeableness: float  # 0-1
    neuroticism: float  # 0-1


class AgentProfile(BaseModel):
    """Complete agent persona definition."""
    id: str
    mbti: MBTIType
    demographics: Demographics
    behavioral: BehavioralProfile
    political_leaning: PoliticalLeaning
    information_sources: List[str]
    memory_capacity: int
