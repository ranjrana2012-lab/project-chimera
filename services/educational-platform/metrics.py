"""Educational Platform Metrics.

Prometheus metrics for monitoring the educational platform service,
including student engagement, learning outcomes, and accessibility usage.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
import time
from contextlib import contextmanager
from typing import Optional


# Student Metrics
active_students = Gauge(
    'educational_active_students',
    'Number of currently active students',
    ['course_id']
)

total_students = Gauge(
    'educational_total_students',
    'Total number of registered students'
)

student_sessions_total = Counter(
    'educational_student_sessions_total',
    'Total number of learning sessions',
    ['student_id', 'course_id']
)

student_learning_time_seconds = Counter(
    'educational_learning_time_seconds',
    'Total time spent learning',
    ['student_id', 'content_type']
)


# Course & Content Metrics
active_courses = Gauge(
    'educational_active_courses',
    'Number of active courses'
)

course_enrollments_total = Counter(
    'educational_course_enrollments_total',
    'Total course enrollments',
    ['course_id', 'student_id']
)

lesson_completion_total = Counter(
    'educational_lesson_completion_total',
    'Total lessons completed',
    ['lesson_id', 'student_id', 'accessibility_features']
)

content_access_total = Counter(
    'educational_content_access_total',
    'Total content accesses',
    ['content_type', 'accessibility_feature']
)


# Assessment Metrics
assessment_attempts_total = Counter(
    'educational_assessment_attempts_total',
    'Total assessment attempts',
    ['assessment_id', 'student_id', 'attempt_number']
)

assessment_scores = Histogram(
    'educational_assessment_scores',
    'Assessment scores distribution',
    ['assessment_id'],
    buckets=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

skills_mastered_total = Counter(
    'educational_skills_mastered_total',
    'Total skills mastered',
    ['skill_id', 'student_id']
)


# Engagement & Sentiment Metrics
engagement_score = Gauge(
    'educational_engagement_score',
    'Current student engagement score',
    ['student_id']
)

average_engagement = Gauge(
    'educational_average_engagement',
    'Average engagement across all students',
    ['course_id']
)

sentiment_score = Gauge(
    'educational_sentiment_score',
    'Current student sentiment score',
    ['student_id', 'session_id']
)

average_sentiment = Gauge(
    'educational_average_sentiment',
    'Average sentiment across all students',
    ['course_id']
)

frustration_events_total = Counter(
    'educational_frustration_events_total',
    'Total frustration events detected',
    ['student_id', 'type']
)


# Accessibility Metrics
bsl_usage_total = Counter(
    'educational_bsl_usage_total',
    'Total BSL (sign language) usage',
    ['student_id', 'lesson_id']
)

captions_usage_total = Counter(
    'educational_captions_usage_total',
    'Total captions usage',
    ['student_id', 'lesson_id']
)

audio_description_usage_total = Counter(
    'educational_audio_description_usage_total',
    'Total audio description usage',
    ['student_id', 'lesson_id']
)

accessibility_satisfaction = Gauge(
    'educational_accessibility_satisfaction',
    'Accessibility feature satisfaction score',
    ['feature', 'student_id']
)


# Performance Metrics
request_latency = Histogram(
    'educational_request_latency_seconds',
    'Request latency',
    ['endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

db_query_latency = Histogram(
    'educational_db_query_latency_seconds',
    'Database query latency',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

cache_hit_rate = Gauge(
    'educational_cache_hit_rate',
    'Cache hit rate',
    ['cache_type']
)


# Educator Metrics
educator_active_sessions = Gauge(
    'educational_educator_active_sessions',
    'Number of active educator dashboard sessions',
    ['educator_id']
)

content_created_total = Counter(
    'educational_content_created_total',
    'Total content items created by educators',
    ['educator_id', 'content_type']
)

student_monitoring_views_total = Counter(
    'educational_student_monitoring_views_total',
    'Total student profile views by educators',
    ['educator_id', 'student_id']
)


# Recommendation System Metrics
recommendations_generated_total = Counter(
    'educational_recommendations_generated_total',
    'Total recommendations generated',
    ['student_id', 'recommendation_type']
)

recommendation_acceptance_rate = Gauge(
    'educational_recommendation_acceptance_rate',
    'Recommendation acceptance rate',
    ['recommendation_type']
)


# Helper functions and context managers
@contextmanager
def track_request_latency(endpoint: str):
    """Context manager for tracking request latency."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        request_latency.labels(endpoint=endpoint).observe(duration)


@contextmanager
def track_db_query(query_type: str):
    """Context manager for tracking database query latency."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        db_query_latency.labels(query_type=query_type).observe(duration)


def update_student_engagement(student_id: str, score: float):
    """Update student engagement score."""
    engagement_score.labels(student_id=student_id).set(score)


def update_student_sentiment(student_id: str, session_id: str, score: float):
    """Update student sentiment score."""
    sentiment_score.labels(student_id=student_id, session_id=session_id).set(score)


def record_lesson_completion(student_id: str, lesson_id: str, accessibility_features: list):
    """Record a lesson completion event."""
    features_str = ','.join(accessibility_features) if accessibility_features else 'none'
    lesson_completion_total.labels(
        lesson_id=lesson_id,
        student_id=student_id,
        accessibility_features=features_str
    ).inc()


def record_assessment_attempt(student_id: str, assessment_id: str, attempt_number: int, score: float):
    """Record an assessment attempt."""
    assessment_attempts_total.labels(
        assessment_id=assessment_id,
        student_id=student_id,
        attempt_number=attempt_number
    ).inc()
    assessment_scores.labels(assessment_id=assessment_id).observe(score)


def record_accessibility_usage(feature: str, student_id: str, lesson_id: str):
    """Record usage of an accessibility feature."""
    if feature == 'bsl':
        bsl_usage_total.labels(student_id=student_id, lesson_id=lesson_id).inc()
    elif feature == 'captions':
        captions_usage_total.labels(student_id=student_id, lesson_id=lesson_id).inc()
    elif feature == 'audio_description':
        audio_description_usage_total.labels(student_id=student_id, lesson_id=lesson_id).inc()


def record_skill_mastered(skill_id: str, student_id: str):
    """Record a skill mastery event."""
    skills_mastered_total.labels(skill_id=skill_id, student_id=student_id).inc()


def increment_active_students(course_id: Optional[str] = None):
    """Increment active students counter."""
    if course_id:
        active_students.labels(course_id=course_id).inc()
    else:
        active_students.labels(course_id='all').inc()


def decrement_active_students(course_id: Optional[str] = None):
    """Decrement active students counter."""
    if course_id:
        active_students.labels(course_id=course_id).dec()
    else:
        active_students.labels(course_id='all').dec()
