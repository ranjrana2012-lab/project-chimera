"""Educational Platform Data Models.

This module defines the core data models for the educational platform,
including student profiles, curriculum structure, assessments, and learning analytics.
Based on educational AI agent research from arXiv:2603.11709.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


class AccessibilityLevel(str, Enum):
    """Accessibility needs levels."""
    NONE = "none"
    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"


class LearningStyle(str, Enum):
    """Learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READ_WRITE = "read_write"
    MULTIMODAL = "multimodal"


class ContentType(str, Enum):
    """Types of educational content."""
    TEXT = "text"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    BSL_ANIMATION = "bsl_animation"
    ASSESSMENT = "assessment"
    DEMONSTRATION = "demonstration"


class DifficultyLevel(str, Enum):
    """Content difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AssessmentType(str, Enum):
    """Types of assessments."""
    QUIZ = "quiz"
    PRACTICAL = "practical"
    PROJECT = "project"
    ORAL = "oral"
    PEER_REVIEW = "peer_review"


class SkillStatus(str, Enum):
    """Skill mastery status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PRACTICE = "practice"
    REVIEW = "review"
    MASTERED = "mastered"


class AccessibilityNeeds(BaseModel):
    """Accessibility requirements for a student."""
    requires_bsl: bool = False
    requires_captions: bool = False
    requires_audio_description: bool = False
    requires_high_contrast: bool = False
    requires_text_to_speech: bool = False
    requires_speech_to_text: bool = False
    font_size_preference: str = "medium"  # small, medium, large, extra_large
    color_blindness_mode: Optional[str] = None  # protanopia, deuteranopia, tritanopia
    additional_notes: Optional[str] = None


class LearningObjective(BaseModel):
    """Learning objective for a lesson or course."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    blooms_taxonomy_level: str  # remember, understand, apply, analyze, evaluate, create
    required_for_completion: bool = True


class Skill(BaseModel):
    """Individual skill that can be learned."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # e.g., "programming", "mathematics", "language"
    description: str
    difficulty_level: DifficultyLevel
    prerequisites: List[str] = []  # Skill IDs
    estimated_learning_hours: float = 1.0
    learning_objectives: List[LearningObjective] = []


class StudentProfile(BaseModel):
    """Comprehensive student profile for personalized learning."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Basic Information
    name: str
    email: str
    grade_level: Optional[str] = None  # e.g., "Year 10", "Undergraduate"
    institution: Optional[str] = None

    # Learning Preferences
    learning_style: LearningStyle = LearningStyle.MULTIMODAL
    interests: List[str] = []
    goals: List[str] = []

    # Accessibility
    accessibility_needs: AccessibilityNeeds = Field(default_factory=AccessibilityNeeds)
    accessibility_level: AccessibilityLevel = AccessibilityLevel.NONE

    # Learning State
    current_skills: Dict[str, SkillStatus] = {}  # skill_id -> status
    skill_proficiency: Dict[str, float] = {}  # skill_id -> proficiency (0.0-1.0)
    learning_history: List[Dict[str, Any]] = []

    # Session Information
    last_active: datetime = Field(default_factory=datetime.utcnow)
    total_learning_time_minutes: int = 0
    sessions_completed: int = 0

    # Analytics
    average_engagement_score: float = 0.5
    preferred_content_types: List[ContentType] = []
    optimal_session_length_minutes: int = 30

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class Lesson(BaseModel):
    """Individual lesson within a course."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    order: int = 0

    # Content
    content_type: ContentType
    content_url: Optional[str] = None
    text_content: Optional[str] = None
    duration_minutes: int = 30

    # Learning Objectives
    learning_objectives: List[LearningObjective] = []
    skills_taught: List[str] = []  # Skill IDs

    # Prerequisites
    prerequisite_lessons: List[str] = []  # Lesson IDs
    prerequisite_skills: List[str] = []  # Skill IDs

    # Accessibility
    bsl_available: bool = False
    captions_available: bool = False
    audio_description_available: bool = False
    alternative_formats: Dict[str, str] = {}  # format -> URL

    # Assessment
    assessment_id: Optional[str] = None

    # Metadata
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Assessment(BaseModel):
    """Assessment for evaluating student understanding."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    assessment_type: AssessmentType
    lesson_id: Optional[str] = None

    # Questions
    questions: List[Dict[str, Any]] = []  # Each question has structure

    # Settings
    time_limit_minutes: Optional[int] = None
    passing_score_threshold: float = 0.7
    max_attempts: int = 3
    randomize_questions: bool = False
    show_feedback: bool = True

    # Skills Assessed
    skills_assessed: List[str] = []  # Skill IDs

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Course(BaseModel):
    """Course containing multiple lessons."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    subject: str
    grade_level: Optional[str] = None

    # Structure
    lessons: List[Lesson] = []
    prerequisites: List[str] = []  # Course IDs or Skill IDs

    # Learning Outcomes
    learning_objectives: List[LearningObjective] = []
    skills_taught: List[str] = []  # Skill IDs

    # Metadata
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    estimated_duration_hours: float = 10.0
    tags: List[str] = []
    is_published: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Educator Information
    educator_id: str
    educator_name: str
    department: Optional[str] = None


class Enrollment(BaseModel):
    """Student enrollment in a course."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)

    # Progress
    progress_percentage: float = 0.0
    lessons_completed: List[str] = []  # Lesson IDs
    current_lesson_id: Optional[str] = None

    # Status
    is_active: bool = True
    completed_at: Optional[datetime] = None
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

    # Performance
    average_assessment_score: float = 0.0
    assessments_completed: List[str] = []  # Assessment IDs
    assessment_scores: Dict[str, float] = {}  # assessment_id -> score


class AssessmentAttempt(BaseModel):
    """Record of a student's attempt at an assessment."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assessment_id: str
    student_id: str
    attempt_number: int = 1

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None

    # Performance
    score: float = 0.0
    passed: bool = False
    answers: Dict[str, Any] = {}  # question_id -> answer
    feedback: Optional[str] = None

    # Skills
    skills_demonstrated: List[str] = []
    skills_need_practice: List[str] = []

    # Sentiment & Engagement
    engagement_score: float = 0.5
    sentiment_score: float = 0.0  # -1.0 to 1.0
    frustration_indicators: List[str] = []


class LearningSession(BaseModel):
    """Record of a learning session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    lesson_id: str
    course_id: str

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_minutes: float = 0.0

    # Content
    content_types_accessed: List[ContentType] = []
    accessibility_features_used: List[str] = []  # e.g., "bsl", "captions"

    # Engagement
    engagement_score: float = 0.5
    sentiment_scores: List[float] = []  # Time-series sentiment data
    interaction_events: List[Dict[str, Any]] = []  # Clicks, pauses, etc.

    # Learning Outcomes
    skills_practiced: List[str] = []
    completion_percentage: float = 0.0
    assessment_completed: bool = False

    # Notes
    session_notes: Optional[str] = None


class EducatorProfile(BaseModel):
    """Educator profile for content creation and student monitoring."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Basic Information
    name: str
    email: str
    institution: str
    department: Optional[str] = None
    subjects: List[str] = []

    # Expertise
    areas_of_expertise: List[str] = []
    qualifications: List[str] = []
    years_of_experience: int = 0

    # Content Creation
    courses_created: List[str] = []  # Course IDs
    total_students_taught: int = 0

    # Permissions
    can_create_courses: bool = True
    can_review_content: bool = False
    can_view_analytics: bool = True
    can_manage_students: bool = False


class LearningAnalytics(BaseModel):
    """Aggregated learning analytics for a student."""
    student_id: str
    period_start: datetime
    period_end: datetime

    # Engagement Metrics
    total_sessions: int = 0
    total_learning_time_minutes: int = 0
    average_session_length_minutes: float = 0.0
    average_engagement_score: float = 0.0

    # Performance Metrics
    assessments_completed: int = 0
    average_assessment_score: float = 0.0
    skills_mastered: int = 0
    skills_in_progress: int = 0

    # Progress Metrics
    courses_started: int = 0
    courses_completed: int = 0
    completion_rate: float = 0.0

    # Sentiment & Wellbeing
    average_sentiment_score: float = 0.0
    frustration_events: int = 0
    help_requests: int = 0

    # Accessibility Usage
    bsl_usage_count: int = 0
    captions_usage_count: int = 0
    accessibility_satisfaction_score: float = 0.0

    # Recommendations
    recommended_skills: List[str] = []
    recommended_content_types: List[ContentType] = []
    intervention_needed: bool = False


class ContentRecommendation(BaseModel):
    """Personalized content recommendation for a student."""
    student_id: str
    recommended_lessons: List[str] = []  # Lesson IDs
    recommended_courses: List[str] = []  # Course IDs
    recommended_skills: List[str] = []  # Skill IDs

    # Reasoning
    reason: str
    confidence_score: float = 0.0
    based_on_data: List[str] = []  # e.g., "past_performance", "interests"

    # Accessibility Considerations
    accessibility_match: bool = True
    alternative_formats_available: bool = True


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, bool] = {}


class MetricsResponse(BaseModel):
    """Metrics response."""
    active_students: int = 0
    active_courses: int = 0
    total_sessions_today: int = 0
    average_engagement: float = 0.0
    accessibility_usage: Dict[str, int] = {}
