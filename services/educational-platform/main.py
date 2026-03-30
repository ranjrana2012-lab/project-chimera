"""Educational Platform Service - Main FastAPI Application.

AI-powered educational platform that integrates accessibility agents
for inclusive teaching and learning.

Based on research from arXiv:2603.11709 "Scaling Laws for Educational AI Agents"
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# ============================================================================
# Security Middleware (Environment-based CORS, Security Headers, Rate Limiting)
# ============================================================================
import sys
import os

# Add shared module to path for security middleware
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

# ... rest of imports after this

from config import settings
from models import (
    StudentProfile, Course, Lesson, Enrollment, Assessment,
    AssessmentAttempt, LearningSession, EducatorProfile,
    LearningAnalytics, ContentRecommendation,
    APIResponse, HealthResponse, MetricsResponse,
    LearningStyle, DifficultyLevel, ContentType, SkillStatus
)
from database import get_database, EducationalDatabase
from integrations import get_content_integrator, EducationalContentIntegrator
from metrics import (
    track_request_latency, increment_active_students,
    decrement_active_students, update_student_engagement,
    update_student_sentiment, record_lesson_completion,
    record_assessment_attempt, record_accessibility_usage,
    active_students as active_students_gauge, total_students,
    active_courses as active_courses_gauge
)
from tracing import setup_tracing, instrument_fastapi, get_tracer, shutdown_tracing


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize OpenTelemetry tracing
try:
    tracer = setup_tracing(
        service_name=settings.service_name,
        service_version="1.0.0",
        otlp_endpoint=settings.otlp_endpoint,
        environment=settings.environment
    )
    logger.info("Tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize tracing: {e}")
    tracer = None


# Global instances
db: Optional[EducationalDatabase] = None
content_integrator: Optional[EducationalContentIntegrator] = None
active_websockets: Dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Educational Platform Service...")
    global db, content_integrator

    try:
        # Instrument FastAPI with OpenTelemetry
        instrument_fastapi(app)

        # Initialize database
        db = get_database()
        logger.info("Database initialized")

        # Initialize content integrator
        content_integrator = get_content_integrator()
        logger.info("Content integrator initialized")

        # Initialize metrics
        total_students.set(0)
        active_courses_gauge.set(0)
        logger.info("Metrics initialized")

        logger.info("Educational Platform Service started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Educational Platform Service...")
    if content_integrator:
        await content_integrator.close_all()
    shutdown_tracing()
    logger.info("Educational Platform Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Educational Platform Service",
    description="AI-powered educational platform with accessibility integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware - replaced with security middleware
from shared.middleware import (
    SecurityHeadersMiddleware,
    configure_cors,
    setup_rate_limit_error_handler,
)


# ============================================================================
# Health & Metrics Endpoints
# ============================================================================

@app.get("/health/live", response_model=Dict[str, str])
async def liveness_probe():
    """Liveness probe endpoint."""
    return {"status": "alive"}


@app.get("/health/ready", response_model=HealthResponse)
async def readiness_probe():
    """Readiness probe endpoint."""
    dependencies = {}
    all_ready = True

    # Check database
    try:
        if db:
            dependencies["database"] = True
        else:
            dependencies["database"] = False
            all_ready = False
    except Exception as e:
        dependencies["database"] = False
        all_ready = False

    # Check integrations
    try:
        if content_integrator:
            dependencies["content_integrator"] = True
        else:
            dependencies["content_integrator"] = False
            all_ready = False
    except Exception as e:
        dependencies["content_integrator"] = False
        all_ready = False

    return HealthResponse(
        status="ready" if all_ready else "not_ready",
        service=settings.service_name,
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get educational platform metrics."""
    return MetricsResponse(
        active_students=int(active_students_gauge.labels(course_id='all')._value.get() or 0),
        active_courses=int(active_courses_gauge._value.get() or 0),
        total_sessions_today=0,  # Would calculate from database
        average_engagement=0.0,  # Would calculate from database
        accessibility_usage={}  # Would calculate from database
    )


# ============================================================================
# Student Profile Endpoints
# ============================================================================

@app.post("/api/v1/students", response_model=APIResponse)
async def create_student(student: StudentProfile):
    """Create a new student profile."""
    with track_request_latency("create_student"):
        try:
            success = db.create_student(student)
            if success:
                total_students.inc()
                return APIResponse(
                    success=True,
                    message="Student profile created successfully",
                    data={"student_id": student.id}
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to create student profile")
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/students/{student_id}", response_model=StudentProfile)
async def get_student(student_id: str):
    """Get student profile by ID."""
    with track_request_latency("get_student"):
        student = db.get_student(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student


@app.put("/api/v1/students/{student_id}", response_model=APIResponse)
async def update_student(student_id: str, updates: Dict[str, Any]):
    """Update student profile."""
    with track_request_latency("update_student"):
        try:
            success = db.update_student(student_id, updates)
            if success:
                return APIResponse(
                    success=True,
                    message="Student profile updated successfully"
                )
            else:
                raise HTTPException(status_code=404, detail="Student not found")
        except Exception as e:
            logger.error(f"Error updating student: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/students/{student_id}/analytics", response_model=LearningAnalytics)
async def get_student_analytics(
    student_id: str,
    days: int = 30
):
    """Get learning analytics for a student."""
    with track_request_latency("get_student_analytics"):
        analytics = db.get_student_analytics(student_id, days)
        if not analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")
        return analytics


# ============================================================================
# Course Management Endpoints
# ============================================================================

@app.post("/api/v1/courses", response_model=APIResponse)
async def create_course(course: Course):
    """Create a new course."""
    with track_request_latency("create_course"):
        try:
            success = db.create_course(course)
            if success:
                active_courses_gauge.inc()
                return APIResponse(
                    success=True,
                    message="Course created successfully",
                    data={"course_id": course.id}
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to create course")
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    """Get course by ID."""
    with track_request_latency("get_course"):
        course = db.get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course


@app.get("/api/v1/courses", response_model=List[Course])
async def list_courses(
    educator_id: Optional[str] = None,
    is_published: Optional[bool] = None
):
    """List courses with optional filters."""
    with track_request_latency("list_courses"):
        return db.list_courses(educator_id=educator_id, is_published=is_published)


# ============================================================================
# Enrollment & Learning Endpoints
# ============================================================================

@app.post("/api/v1/enrollments", response_model=APIResponse)
async def create_enrollment(
    student_id: str,
    course_id: str
):
    """Enroll a student in a course."""
    with track_request_latency("create_enrollment"):
        try:
            # Verify student and course exist
            student = db.get_student(student_id)
            course = db.get_course(course_id)

            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")

            # Create enrollment
            enrollment = Enrollment(
                student_id=student_id,
                course_id=course_id
            )

            success = db.create_enrollment(enrollment)
            if success:
                increment_active_students(course_id)
                return APIResponse(
                    success=True,
                    message="Enrollment created successfully",
                    data={"enrollment_id": enrollment.id}
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to create enrollment")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating enrollment: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/enrollments/{student_id}/{course_id}", response_model=Enrollment)
async def get_enrollment(student_id: str, course_id: str):
    """Get enrollment details."""
    with track_request_latency("get_enrollment"):
        enrollment = db.get_enrollment(student_id, course_id)
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return enrollment


@app.post("/api/v1/sessions", response_model=APIResponse)
async def create_learning_session(session: LearningSession):
    """Create a new learning session."""
    with track_request_latency("create_learning_session"):
        try:
            success = db.create_learning_session(session)
            if success:
                increment_active_students(session.course_id)
                update_student_engagement(session.student_id, session.engagement_score)

                return APIResponse(
                    success=True,
                    message="Learning session created successfully",
                    data={"session_id": session.id}
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to create session")
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{student_id}", response_model=List[LearningSession])
async def get_student_sessions(student_id: str, limit: int = 50):
    """Get recent learning sessions for a student."""
    with track_request_latency("get_student_sessions"):
        return db.get_student_sessions(student_id, limit)


# ============================================================================
# Assessment Endpoints
# ============================================================================

@app.post("/api/v1/assessments/{assessment_id}/attempts", response_model=APIResponse)
async def create_assessment_attempt(attempt: AssessmentAttempt):
    """Submit an assessment attempt."""
    with track_request_latency("create_assessment_attempt"):
        try:
            success = db.create_assessment_attempt(attempt)
            if success:
                # Record metrics
                record_assessment_attempt(
                    attempt.student_id,
                    attempt.assessment_id,
                    attempt.attempt_number,
                    attempt.score
                )

                # Update engagement and sentiment
                update_student_engagement(attempt.student_id, attempt.engagement_score)
                update_student_sentiment(attempt.student_id, attempt.id, attempt.sentiment_score)

                return APIResponse(
                    success=True,
                    message="Assessment attempt recorded successfully",
                    data={"attempt_id": attempt.id, "passed": attempt.passed}
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to record attempt")
        except Exception as e:
            logger.error(f"Error creating assessment attempt: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Accessibility Integration Endpoints
# ============================================================================

@app.post("/api/v1/content/enhance", response_model=APIResponse)
async def enhance_content_accessibility(
    content: str,
    student_id: str,
    session_id: str
):
    """Enhance educational content with accessibility features."""
    with track_request_latency("enhance_content"):
        try:
            student = db.get_student(student_id)
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")

            enhanced = await content_integrator.enhance_content_with_accessibility(
                content, student, session_id
            )

            # Record accessibility usage
            for feature in enhanced.get("accessibility_features", []):
                record_accessibility_usage(feature, student_id, session_id)

            return APIResponse(
                success=True,
                message="Content enhanced with accessibility features",
                data=enhanced
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error enhancing content: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/bsl/translate", response_model=APIResponse)
async def translate_to_bsl(text: str):
    """Translate text to BSL gloss notation."""
    with track_request_latency("bsl_translate"):
        try:
            result = await content_integrator.bsl.translate_text_to_bsl(text)
            if result:
                return APIResponse(
                    success=True,
                    message="Text translated to BSL",
                    data=result
                )
            else:
                raise HTTPException(status_code=500, detail="Translation failed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error translating to BSL: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sentiment/classroom/{course_id}", response_model=Dict[str, Any])
async def get_classroom_sentiment(course_id: str):
    """Get classroom sentiment overview for educators."""
    with track_request_latency("classroom_sentiment"):
        try:
            sentiment_data = await content_integrator.monitor_classroom_sentiment(course_id)
            return sentiment_data
        except Exception as e:
            logger.error(f"Error getting classroom sentiment: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Recommendation Endpoints
# ============================================================================

@app.get("/api/v1/recommendations/{student_id}", response_model=List[ContentRecommendation])
async def get_personalized_recommendations(student_id: str):
    """Get personalized content recommendations for a student."""
    with track_request_latency("get_recommendations"):
        try:
            student = db.get_student(student_id)
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")

            recent_sessions = db.get_student_sessions(student_id, limit=10)
            recommendations = await content_integrator.generate_personalized_recommendations(
                student, recent_sessions
            )

            return recommendations
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint for Real-time Updates
# ============================================================================

@app.websocket("/ws/educator/{educator_id}")
async def educator_websocket(websocket: WebSocket, educator_id: str):
    """WebSocket endpoint for real-time educator dashboard updates."""
    await websocket.accept()
    active_websockets[educator_id] = websocket

    try:
        while True:
            # Receive messages from educator
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "subscribe_course":
                course_id = data.get("course_id")
                # Educator wants to monitor this course
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "course_id": course_id
                })

            elif data.get("type") == "get_sentiment":
                course_id = data.get("course_id")
                sentiment_data = await content_integrator.monitor_classroom_sentiment(course_id)
                await websocket.send_json({
                    "type": "sentiment_update",
                    "data": sentiment_data
                })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        del active_websockets[educator_id]
        logger.info(f"Educator {educator_id} disconnected")


@app.websocket("/ws/student/{student_id}")
async def student_websocket(websocket: WebSocket, student_id: str):
    """WebSocket endpoint for real-time student learning updates."""
    await websocket.accept()
    active_websockets[student_id] = websocket

    try:
        while True:
            # Receive messages from student
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "start_session":
                lesson_id = data.get("lesson_id")
                course_id = data.get("course_id")

                # Create learning session
                session = LearningSession(
                    student_id=student_id,
                    lesson_id=lesson_id,
                    course_id=course_id
                )
                db.create_learning_session(session)

                await websocket.send_json({
                    "type": "session_started",
                    "session_id": session.id
                })

            elif data.get("type") == "update_engagement":
                engagement_score = data.get("engagement_score", 0.5)
                update_student_engagement(student_id, engagement_score)

                await websocket.send_json({
                    "type": "engagement_updated",
                    "engagement_score": engagement_score
                })

            elif data.get("type") == "request_bsl":
                text = data.get("text")
                bsl_animation = await content_integrator.bsl.text_to_bsl_animation(
                    text, student_id
                )

                await websocket.send_json({
                    "type": "bsl_animation",
                    "data": bsl_animation
                })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        del active_websockets[student_id]
        logger.info(f"Student {student_id} disconnected")


# ============================================================================
# Educator Interface Endpoints
# ============================================================================

@app.post("/api/v1/educators", response_model=APIResponse)
async def create_educator(educator: EducatorProfile):
    """Create a new educator profile."""
    with track_request_latency("create_educator"):
        try:
            success = db.create_educator(educator)
            if success:
                return APIResponse(
                    success=True,
                    message="Educator profile created successfully",
                    data={"educator_id": educator.id}
                )
            else:
                raise HTTPException(status_code=400, detail="Failed to create educator profile")
        except Exception as e:
            logger.error(f"Error creating educator: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/educators/{educator_id}", response_model=EducatorProfile)
async def get_educator(educator_id: str):
    """Get educator profile by ID."""
    with track_request_latency("get_educator"):
        educator = db.get_educator(educator_id)
        if not educator:
            raise HTTPException(status_code=404, detail="Educator not found")
        return educator


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
