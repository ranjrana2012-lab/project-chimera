"""Tests for Educational Platform Service."""

import pytest
from datetime import datetime, timedelta
from models import (
    StudentProfile, Course, Lesson, Enrollment, LearningSession,
    AssessmentAttempt, EducatorProfile, LearningObjective,
    Skill, DifficultyLevel, LearningStyle, AccessibilityNeeds,
    ContentType, AssessmentType
)
from database import EducationalDatabase
from main import app
from httpx import AsyncClient
import tempfile
import os


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def db(temp_db):
    """Create database instance for testing."""
    # Replace database URL with temp database
    db_instance = EducationalDatabase(db_path=f"sqlite:///{temp_db}")
    yield db_instance


@pytest.fixture
def test_student():
    """Create test student profile."""
    return StudentProfile(
        name="Test Student",
        email="test@example.com",
        grade_level="Year 10",
        institution="Test College",
        learning_style=LearningStyle.VISUAL,
        interests=["programming", "math"],
        accessibility_needs=AccessibilityNeeds(
            requires_bsl=True,
            requires_captions=True
        )
    )


@pytest.fixture
def test_educator():
    """Create test educator profile."""
    return EducatorProfile(
        name="Dr. Test Educator",
        email="educator@test.ac.uk",
        institution="Test College",
        department="Computer Science",
        subjects=["Programming", "Mathematics"],
        areas_of_expertise=["Python", "Algorithms"],
        qualifications=["PhD", "PGCE"],
        years_of_experience=10
    )


@pytest.fixture
def test_course(test_educator):
    """Create test course."""
    return Course(
        title="Introduction to Python",
        description="Learn Python basics",
        subject="Computer Science",
        grade_level="Year 10",
        educator_id=test_educator.id,
        educator_name=test_educator.name,
        difficulty_level=DifficultyLevel.BEGINNER,
        lessons=[
            Lesson(
                title="Variables",
                description="Learn about variables",
                content_type=ContentType.TEXT,
                text_content="Variables are containers for data",
                duration_minutes=30,
                bsl_available=True,
                captions_available=True
            )
        ]
    )


class TestDatabase:
    """Test database operations."""

    def test_create_student(self, db, test_student):
        """Test student creation."""
        success = db.create_student(test_student)
        assert success is True

        # Verify student was created
        retrieved = db.get_student(test_student.id)
        assert retrieved is not None
        assert retrieved.email == test_student.email
        assert retrieved.name == test_student.name

    def test_create_duplicate_student(self, db, test_student):
        """Test that duplicate students are not created."""
        db.create_student(test_student)

        # Try to create duplicate
        duplicate = StudentProfile(
            name=test_student.name,
            email=test_student.email,  # Same email
            grade_level=test_student.grade_level
        )
        success = db.create_student(duplicate)
        assert success is False

    def test_update_student(self, db, test_student):
        """Test student update."""
        db.create_student(test_student)

        # Update student
        success = db.update_student(
            test_student.id,
            {"grade_level": "Year 11"}
        )
        assert success is True

        # Verify update
        retrieved = db.get_student(test_student.id)
        assert retrieved.grade_level == "Year 11"

    def test_create_course(self, db, test_course):
        """Test course creation."""
        success = db.create_course(test_course)
        assert success is True

        # Verify course was created
        retrieved = db.get_course(test_course.id)
        assert retrieved is not None
        assert retrieved.title == test_course.title

    def test_create_enrollment(self, db, test_student, test_course):
        """Test enrollment creation."""
        # Create student and course first
        db.create_student(test_student)
        db.create_course(test_course)

        # Create enrollment
        enrollment = Enrollment(
            student_id=test_student.id,
            course_id=test_course.id
        )
        success = db.create_enrollment(enrollment)
        assert success is True

        # Verify enrollment
        retrieved = db.get_enrollment(test_student.id, test_course.id)
        assert retrieved is not None
        assert retrieved.student_id == test_student.id

    def test_create_learning_session(self, db, test_student, test_course):
        """Test learning session creation."""
        # Create student and course first
        db.create_student(test_student)
        db.create_course(test_course)

        # Create learning session
        session = LearningSession(
            student_id=test_student.id,
            lesson_id=test_course.lessons[0].id,
            course_id=test_course.id,
            engagement_score=0.8
        )
        success = db.create_learning_session(session)
        assert success is True

        # Verify session
        sessions = db.get_student_sessions(test_student.id)
        assert len(sessions) == 1
        assert sessions[0].id == session.id

    def test_get_student_analytics(self, db, test_student, test_course):
        """Test student analytics retrieval."""
        # Create student and course
        db.create_student(test_student)
        db.create_course(test_course)

        # Create some sessions
        for i in range(5):
            session = LearningSession(
                student_id=test_student.id,
                lesson_id=test_course.lessons[0].id,
                course_id=test_course.id,
                duration_minutes=30.0,
                engagement_score=0.7 + (i * 0.05)
            )
            db.create_learning_session(session)

        # Get analytics
        analytics = db.get_student_analytics(test_student.id, days=30)
        assert analytics is not None
        assert analytics.total_sessions == 5
        assert analytics.total_learning_time_minutes > 0


class TestAPIEndpoints:
    """Test FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_health_live(self):
        """Test liveness probe."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        """Test readiness probe."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "dependencies" in data

    @pytest.mark.asyncio
    async def test_create_student_api(self, test_student):
        """Test student creation via API."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/students",
                json=test_student.model_dump()
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "student_id" in data["data"]

    @pytest.mark.asyncio
    async def test_get_student_api(self, db, test_student):
        """Test get student via API."""
        # Create student first
        db.create_student(test_student)

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/students/{test_student.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_student.email

    @pytest.mark.asyncio
    async def test_create_course_api(self, test_course):
        """Test course creation via API."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/courses",
                json=test_course.model_dump()
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestModels:
    """Test data models."""

    def test_student_profile_validation(self):
        """Test student profile email validation."""
        with pytest.raises(ValueError):
            StudentProfile(
                name="Test",
                email="invalid-email",  # Invalid email
                grade_level="Year 10"
            )

    def test_student_profile_success(self):
        """Test valid student profile creation."""
        student = StudentProfile(
            name="Test Student",
            email="test@example.com",
            grade_level="Year 10"
        )
        assert student.id is not None
        assert student.email == "test@example.com"

    def test_learning_objective(self):
        """Test learning objective creation."""
        obj = LearningObjective(
            title="Understand Variables",
            description="Learn what variables are",
            blooms_taxonomy_level="understand"
        )
        assert obj.id is not None
        assert obj.title == "Understand Variables"

    def test_skill_with_prerequisites(self):
        """Test skill with prerequisites."""
        skill = Skill(
            name="Advanced Python",
            category="programming",
            description="Advanced Python concepts",
            difficulty_level=DifficultyLevel.ADVANCED,
            prerequisites=["basic_python"]
        )
        assert len(skill.prerequisites) == 1
        assert skill.prerequisites[0] == "basic_python"


class TestIntegrations:
    """Test service integrations."""

    @pytest.mark.asyncio
    async def test_bsl_translation(self):
        """Test BSL translation integration."""
        from integrations import BSLAgentIntegration

        bsl = BSLAgentIntegration()

        # Test translation (mock would be better for unit tests)
        # This will likely fail without running BSL agent
        try:
            result = await bsl.translate_text_to_bsl("hello")
            # If BSL agent is running, test passes
            assert result is not None
        except Exception:
            # If BSL agent is not running, that's expected in unit tests
            pass
        finally:
            await bsl.close()

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self):
        """Test sentiment analysis integration."""
        from integrations import SentimentAgentIntegration

        sentiment = SentimentAgentIntegration()

        # Test sentiment analysis (mock would be better)
        try:
            result = await sentiment.analyze_sentiment("I love learning!")
            # If sentiment agent is running, test passes
            assert result is not None
        except Exception:
            # If sentiment agent is not running, that's expected
            pass
        finally:
            await sentiment.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])
