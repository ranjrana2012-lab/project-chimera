"""Educational Platform Database Layer.

SQLite-based database implementation for the educational platform,
with support for student profiles, courses, enrollments, and analytics.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import threading
from pathlib import Path

from models import (
    StudentProfile, Course, Lesson, Enrollment, Assessment,
    AssessmentAttempt, LearningSession, EducatorProfile,
    LearningAnalytics, ContentRecommendation, Skill
)
from config import settings


class EducationalDatabase:
    """Database handler for educational platform."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        self._local = threading.local()
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Get database connection (thread-local)."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        yield self._local.conn

    def _init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    grade_level TEXT,
                    institution TEXT,
                    learning_style TEXT DEFAULT 'multimodal',
                    interests TEXT,
                    goals TEXT,
                    accessibility_needs TEXT,
                    accessibility_level TEXT DEFAULT 'none',
                    current_skills TEXT,
                    skill_proficiency TEXT,
                    learning_history TEXT,
                    last_active TIMESTAMP,
                    total_learning_time_minutes INTEGER DEFAULT 0,
                    sessions_completed INTEGER DEFAULT 0,
                    average_engagement_score REAL DEFAULT 0.5,
                    preferred_content_types TEXT,
                    optimal_session_length_minutes INTEGER DEFAULT 30,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

            # Skills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    description TEXT,
                    difficulty_level TEXT,
                    prerequisites TEXT,
                    estimated_learning_hours REAL DEFAULT 1.0,
                    learning_objectives TEXT
                )
            """)

            # Courses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    subject TEXT,
                    grade_level TEXT,
                    lessons TEXT,
                    prerequisites TEXT,
                    learning_objectives TEXT,
                    skills_taught TEXT,
                    difficulty_level TEXT DEFAULT 'intermediate',
                    estimated_duration_hours REAL DEFAULT 10.0,
                    tags TEXT,
                    is_published BOOLEAN DEFAULT 0,
                    educator_id TEXT,
                    educator_name TEXT,
                    department TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

            # Lessons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    course_id TEXT,
                    order_index INTEGER DEFAULT 0,
                    content_type TEXT,
                    content_url TEXT,
                    text_content TEXT,
                    duration_minutes INTEGER DEFAULT 30,
                    learning_objectives TEXT,
                    skills_taught TEXT,
                    prerequisite_lessons TEXT,
                    prerequisite_skills TEXT,
                    bsl_available BOOLEAN DEFAULT 0,
                    captions_available BOOLEAN DEFAULT 0,
                    audio_description_available BOOLEAN DEFAULT 0,
                    alternative_formats TEXT,
                    assessment_id TEXT,
                    difficulty_level TEXT DEFAULT 'intermediate',
                    tags TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(id)
                )
            """)

            # Assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    assessment_type TEXT,
                    lesson_id TEXT,
                    questions TEXT,
                    time_limit_minutes INTEGER,
                    passing_score_threshold REAL DEFAULT 0.7,
                    max_attempts INTEGER DEFAULT 3,
                    randomize_questions BOOLEAN DEFAULT 0,
                    show_feedback BOOLEAN DEFAULT 1,
                    skills_assessed TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id)
                )
            """)

            # Enrollments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    enrolled_at TIMESTAMP,
                    progress_percentage REAL DEFAULT 0.0,
                    lessons_completed TEXT,
                    current_lesson_id TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    completed_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    average_assessment_score REAL DEFAULT 0.0,
                    assessments_completed TEXT,
                    assessment_scores TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (course_id) REFERENCES courses(id),
                    UNIQUE(student_id, course_id)
                )
            """)

            # Assessment attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_attempts (
                    id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    attempt_number INTEGER DEFAULT 1,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    time_taken_seconds INTEGER,
                    score REAL DEFAULT 0.0,
                    passed BOOLEAN DEFAULT 0,
                    answers TEXT,
                    feedback TEXT,
                    skills_demonstrated TEXT,
                    skills_need_practice TEXT,
                    engagement_score REAL DEFAULT 0.5,
                    sentiment_score REAL DEFAULT 0.0,
                    frustration_indicators TEXT,
                    FOREIGN KEY (assessment_id) REFERENCES assessments(id),
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            """)

            # Learning sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_minutes REAL DEFAULT 0.0,
                    content_types_accessed TEXT,
                    accessibility_features_used TEXT,
                    engagement_score REAL DEFAULT 0.5,
                    sentiment_scores TEXT,
                    interaction_events TEXT,
                    skills_practiced TEXT,
                    completion_percentage REAL DEFAULT 0.0,
                    assessment_completed BOOLEAN DEFAULT 0,
                    session_notes TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (lesson_id) REFERENCES lessons(id),
                    FOREIGN KEY (course_id) REFERENCES courses(id)
                )
            """)

            # Educators table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS educators (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    institution TEXT,
                    department TEXT,
                    subjects TEXT,
                    areas_of_expertise TEXT,
                    qualifications TEXT,
                    years_of_experience INTEGER DEFAULT 0,
                    courses_created TEXT,
                    total_students_taught INTEGER DEFAULT 0,
                    can_create_courses BOOLEAN DEFAULT 1,
                    can_review_content BOOLEAN DEFAULT 0,
                    can_view_analytics BOOLEAN DEFAULT 1,
                    can_manage_students BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP
                )
            """)

            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_student ON learning_sessions(student_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student ON assessment_attempts(student_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons(course_id)")

            conn.commit()

    # Student operations
    def create_student(self, student: StudentProfile) -> bool:
        """Create a new student profile."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO students (
                        id, name, email, grade_level, institution, learning_style,
                        interests, goals, accessibility_needs, accessibility_level,
                        current_skills, skill_proficiency, learning_history,
                        last_active, total_learning_time_minutes, sessions_completed,
                        average_engagement_score, preferred_content_types,
                        optimal_session_length_minutes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student.id, student.name, student.email, student.grade_level,
                    student.institution, student.learning_style.value,
                    json.dumps(student.interests), json.dumps(student.goals),
                    student.accessibility_needs.model_dump_json(),
                    student.accessibility_level.value,
                    json.dumps(student.current_skills),
                    json.dumps(student.skill_proficiency),
                    json.dumps(student.learning_history),
                    student.last_active.isoformat(),
                    student.total_learning_time_minutes,
                    student.sessions_completed,
                    student.average_engagement_score,
                    json.dumps([ct.value for ct in student.preferred_content_types]),
                    student.optimal_session_length_minutes,
                    student.created_at.isoformat(),
                    student.updated_at.isoformat()
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating student: {e}")
            return False

    def get_student(self, student_id: str) -> Optional[StudentProfile]:
        """Get student profile by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
                row = cursor.fetchone()

                if row:
                    return StudentProfile(
                        id=row['id'],
                        name=row['name'],
                        email=row['email'],
                        grade_level=row['grade_level'],
                        institution=row['institution'],
                        learning_style=row['learning_style'],
                        interests=json.loads(row['interests']) if row['interests'] else [],
                        goals=json.loads(row['goals']) if row['goals'] else [],
                        accessibility_needs=json.loads(row['accessibility_needs']),
                        accessibility_level=row['accessibility_level'],
                        current_skills=json.loads(row['current_skills']) if row['current_skills'] else {},
                        skill_proficiency=json.loads(row['skill_proficiency']) if row['skill_proficiency'] else {},
                        learning_history=json.loads(row['learning_history']) if row['learning_history'] else [],
                        last_active=datetime.fromisoformat(row['last_active']),
                        total_learning_time_minutes=row['total_learning_time_minutes'],
                        sessions_completed=row['sessions_completed'],
                        average_engagement_score=row['average_engagement_score'],
                        preferred_content_types=[ContentType(ct) for ct in json.loads(row['preferred_content_types'])] if row['preferred_content_types'] else [],
                        optimal_session_length_minutes=row['optimal_session_length_minutes'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None
        except Exception as e:
            print(f"Error getting student: {e}")
            return None

    def update_student(self, student_id: str, updates: Dict[str, Any]) -> bool:
        """Update student profile."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build dynamic UPDATE statement
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [datetime.utcnow().isoformat(), student_id]

                cursor.execute(f"""
                    UPDATE students
                    SET {set_clause}, updated_at = ?
                    WHERE id = ?
                """, values)

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating student: {e}")
            return False

    # Course operations
    def create_course(self, course: Course) -> bool:
        """Create a new course."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO courses (
                        id, title, description, subject, grade_level,
                        lessons, prerequisites, learning_objectives, skills_taught,
                        difficulty_level, estimated_duration_hours, tags, is_published,
                        educator_id, educator_name, department, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course.id, course.title, course.description, course.subject,
                    course.grade_level,
                    json.dumps([l.model_dump() for l in course.lessons]),
                    json.dumps(course.prerequisites),
                    json.dumps([lo.model_dump() for lo in course.learning_objectives]),
                    json.dumps(course.skills_taught),
                    course.difficulty_level.value,
                    course.estimated_duration_hours,
                    json.dumps(course.tags),
                    course.is_published,
                    course.educator_id, course.educator_name, course.department,
                    course.created_at.isoformat(),
                    course.updated_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating course: {e}")
            return False

    def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
                row = cursor.fetchone()

                if row:
                    return Course(
                        id=row['id'],
                        title=row['title'],
                        description=row['description'],
                        subject=row['subject'],
                        grade_level=row['grade_level'],
                        lessons=[Lesson(**l) for l in json.loads(row['lessons'])] if row['lessons'] else [],
                        prerequisites=json.loads(row['prerequisites']) if row['prerequisites'] else [],
                        learning_objectives=[LearningObjective(**lo) for lo in json.loads(row['learning_objectives'])] if row['learning_objectives'] else [],
                        skills_taught=json.loads(row['skills_taught']) if row['skills_taught'] else [],
                        difficulty_level=row['difficulty_level'],
                        estimated_duration_hours=row['estimated_duration_hours'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        is_published=row['is_published'],
                        educator_id=row['educator_id'],
                        educator_name=row['educator_name'],
                        department=row['department'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None
        except Exception as e:
            print(f"Error getting course: {e}")
            return None

    def list_courses(self, educator_id: Optional[str] = None, is_published: Optional[bool] = None) -> List[Course]:
        """List courses with optional filters."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM courses WHERE 1=1"
                params = []

                if educator_id:
                    query += " AND educator_id = ?"
                    params.append(educator_id)

                if is_published is not None:
                    query += " AND is_published = ?"
                    params.append(is_published)

                query += " ORDER BY created_at DESC"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                courses = []
                for row in rows:
                    courses.append(Course(
                        id=row['id'],
                        title=row['title'],
                        description=row['description'],
                        subject=row['subject'],
                        grade_level=row['grade_level'],
                        lessons=[Lesson(**l) for l in json.loads(row['lessons'])] if row['lessons'] else [],
                        prerequisites=json.loads(row['prerequisites']) if row['prerequisites'] else [],
                        learning_objectives=[LearningObjective(**lo) for lo in json.loads(row['learning_objectives'])] if row['learning_objectives'] else [],
                        skills_taught=json.loads(row['skills_taught']) if row['skills_taught'] else [],
                        difficulty_level=row['difficulty_level'],
                        estimated_duration_hours=row['estimated_duration_hours'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        is_published=row['is_published'],
                        educator_id=row['educator_id'],
                        educator_name=row['educator_name'],
                        department=row['department'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    ))
                return courses
        except Exception as e:
            print(f"Error listing courses: {e}")
            return []

    # Enrollment operations
    def create_enrollment(self, enrollment: Enrollment) -> bool:
        """Create a new enrollment."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO enrollments (
                        id, student_id, course_id, enrolled_at, progress_percentage,
                        lessons_completed, current_lesson_id, is_active, completed_at,
                        last_accessed, average_assessment_score, assessments_completed,
                        assessment_scores
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    enrollment.id, enrollment.student_id, enrollment.course_id,
                    enrollment.enrolled_at.isoformat(),
                    enrollment.progress_percentage,
                    json.dumps(enrollment.lessons_completed),
                    enrollment.current_lesson_id,
                    enrollment.is_active,
                    enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                    enrollment.last_accessed.isoformat(),
                    enrollment.average_assessment_score,
                    json.dumps(enrollment.assessments_completed),
                    json.dumps(enrollment.assessment_scores)
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating enrollment: {e}")
            return False

    def get_enrollment(self, student_id: str, course_id: str) -> Optional[Enrollment]:
        """Get enrollment by student and course."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM enrollments WHERE student_id = ? AND course_id = ?",
                    (student_id, course_id)
                )
                row = cursor.fetchone()

                if row:
                    return Enrollment(
                        id=row['id'],
                        student_id=row['student_id'],
                        course_id=row['course_id'],
                        enrolled_at=datetime.fromisoformat(row['enrolled_at']),
                        progress_percentage=row['progress_percentage'],
                        lessons_completed=json.loads(row['lessons_completed']) if row['lessons_completed'] else [],
                        current_lesson_id=row['current_lesson_id'],
                        is_active=row['is_active'],
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        last_accessed=datetime.fromisoformat(row['last_accessed']),
                        average_assessment_score=row['average_assessment_score'],
                        assessments_completed=json.loads(row['assessments_completed']) if row['assessments_completed'] else [],
                        assessment_scores=json.loads(row['assessment_scores']) if row['assessment_scores'] else {}
                    )
                return None
        except Exception as e:
            print(f"Error getting enrollment: {e}")
            return None

    def update_enrollment_progress(self, enrollment_id: str, updates: Dict[str, Any]) -> bool:
        """Update enrollment progress."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [enrollment_id]

                cursor.execute(f"""
                    UPDATE enrollments
                    SET {set_clause}
                    WHERE id = ?
                """, values)

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating enrollment: {e}")
            return False

    # Learning session operations
    def create_learning_session(self, session: LearningSession) -> bool:
        """Create a new learning session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO learning_sessions (
                        id, student_id, lesson_id, course_id, started_at, ended_at,
                        duration_minutes, content_types_accessed, accessibility_features_used,
                        engagement_score, sentiment_scores, interaction_events,
                        skills_practiced, completion_percentage, assessment_completed,
                        session_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.id, session.student_id, session.lesson_id, session.course_id,
                    session.started_at.isoformat(),
                    session.ended_at.isoformat() if session.ended_at else None,
                    session.duration_minutes,
                    json.dumps([ct.value for ct in session.content_types_accessed]),
                    json.dumps(session.accessibility_features_used),
                    session.engagement_score,
                    json.dumps(session.sentiment_scores),
                    json.dumps(session.interaction_events),
                    json.dumps(session.skills_practiced),
                    session.completion_percentage,
                    session.assessment_completed,
                    session.session_notes
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating learning session: {e}")
            return False

    def get_student_sessions(self, student_id: str, limit: int = 50) -> List[LearningSession]:
        """Get recent learning sessions for a student."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM learning_sessions
                    WHERE student_id = ?
                    ORDER BY started_at DESC
                    LIMIT ?
                """, (student_id, limit))
                rows = cursor.fetchall()

                sessions = []
                for row in rows:
                    sessions.append(LearningSession(
                        id=row['id'],
                        student_id=row['student_id'],
                        lesson_id=row['lesson_id'],
                        course_id=row['course_id'],
                        started_at=datetime.fromisoformat(row['started_at']),
                        ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
                        duration_minutes=row['duration_minutes'],
                        content_types_accessed=[ContentType(ct) for ct in json.loads(row['content_types_accessed'])] if row['content_types_accessed'] else [],
                        accessibility_features_used=json.loads(row['accessibility_features_used']) if row['accessibility_features_used'] else [],
                        engagement_score=row['engagement_score'],
                        sentiment_scores=json.loads(row['sentiment_scores']) if row['sentiment_scores'] else [],
                        interaction_events=json.loads(row['interaction_events']) if row['interaction_events'] else [],
                        skills_practiced=json.loads(row['skills_practiced']) if row['skills_practiced'] else [],
                        completion_percentage=row['completion_percentage'],
                        assessment_completed=row['assessment_completed'],
                        session_notes=row['session_notes']
                    ))
                return sessions
        except Exception as e:
            print(f"Error getting student sessions: {e}")
            return []

    # Assessment operations
    def create_assessment_attempt(self, attempt: AssessmentAttempt) -> bool:
        """Create a new assessment attempt."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO assessment_attempts (
                        id, assessment_id, student_id, attempt_number, started_at,
                        completed_at, time_taken_seconds, score, passed, answers,
                        feedback, skills_demonstrated, skills_need_practice,
                        engagement_score, sentiment_score, frustration_indicators
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attempt.id, attempt.assessment_id, attempt.student_id,
                    attempt.attempt_number, attempt.started_at.isoformat(),
                    attempt.completed_at.isoformat() if attempt.completed_at else None,
                    attempt.time_taken_seconds, attempt.score, attempt.passed,
                    json.dumps(attempt.answers),
                    attempt.feedback,
                    json.dumps(attempt.skills_demonstrated),
                    json.dumps(attempt.skills_need_practice),
                    attempt.engagement_score, attempt.sentiment_score,
                    json.dumps(attempt.frustration_indicators)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating assessment attempt: {e}")
            return False

    def get_assessment_attempts(self, assessment_id: str, student_id: str) -> List[AssessmentAttempt]:
        """Get all attempts for a specific assessment."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM assessment_attempts
                    WHERE assessment_id = ? AND student_id = ?
                    ORDER BY started_at DESC
                """, (assessment_id, student_id))
                rows = cursor.fetchall()

                attempts = []
                for row in rows:
                    attempts.append(AssessmentAttempt(
                        id=row['id'],
                        assessment_id=row['assessment_id'],
                        student_id=row['student_id'],
                        attempt_number=row['attempt_number'],
                        started_at=datetime.fromisoformat(row['started_at']),
                        completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                        time_taken_seconds=row['time_taken_seconds'],
                        score=row['score'],
                        passed=row['passed'],
                        answers=json.loads(row['answers']) if row['answers'] else {},
                        feedback=row['feedback'],
                        skills_demonstrated=json.loads(row['skills_demonstrated']) if row['skills_demonstrated'] else [],
                        skills_need_practice=json.loads(row['skills_need_practice']) if row['skills_need_practice'] else [],
                        engagement_score=row['engagement_score'],
                        sentiment_score=row['sentiment_score'],
                        frustration_indicators=json.loads(row['frustration_indicators']) if row['frustration_indicators'] else []
                    ))
                return attempts
        except Exception as e:
            print(f"Error getting assessment attempts: {e}")
            return []

    # Analytics operations
    def get_student_analytics(self, student_id: str, days: int = 30) -> Optional[LearningAnalytics]:
        """Get learning analytics for a student."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                period_start = datetime.utcnow() - timedelta(days=days)
                period_end = datetime.utcnow()

                # Get session data
                cursor.execute("""
                    SELECT COUNT(*) as total_sessions,
                           SUM(duration_minutes) as total_time,
                           AVG(engagement_score) as avg_engagement
                    FROM learning_sessions
                    WHERE student_id = ?
                    AND started_at >= ?
                    AND started_at <= ?
                """, (student_id, period_start.isoformat(), period_end.isoformat()))

                session_data = cursor.fetchone()

                # Get assessment data
                cursor.execute("""
                    SELECT COUNT(*) as assessments_completed,
                           AVG(score) as avg_score
                    FROM assessment_attempts
                    WHERE student_id = ?
                    AND started_at >= ?
                    AND started_at <= ?
                """, (student_id, period_start.isoformat(), period_end.isoformat()))

                assessment_data = cursor.fetchone()

                # Get enrollment data
                cursor.execute("""
                    SELECT COUNT(*) as courses_started,
                           SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) as courses_completed
                    FROM enrollments
                    WHERE student_id = ?
                    AND enrolled_at >= ?
                """, (student_id, period_start.isoformat()))

                enrollment_data = cursor.fetchone()

                # Calculate completion rate
                completion_rate = 0.0
                if enrollment_data['courses_started'] and enrollment_data['courses_started'] > 0:
                    completion_rate = enrollment_data['courses_completed'] / enrollment_data['courses_started']

                return LearningAnalytics(
                    student_id=student_id,
                    period_start=period_start,
                    period_end=period_end,
                    total_sessions=session_data['total_sessions'] or 0,
                    total_learning_time_minutes=int(session_data['total_time'] or 0),
                    average_session_length_minutes=float(session_data['total_time'] or 0) / max(session_data['total_sessions'] or 1, 1),
                    average_engagement_score=float(session_data['avg_engagement'] or 0.0),
                    assessments_completed=assessment_data['assessments_completed'] or 0,
                    average_assessment_score=float(assessment_data['avg_score'] or 0.0),
                    skills_mastered=0,  # Would need to calculate from skill_proficiency
                    skills_in_progress=0,
                    courses_started=enrollment_data['courses_started'] or 0,
                    courses_completed=enrollment_data['courses_completed'] or 0,
                    completion_rate=completion_rate,
                    average_sentiment_score=0.0,  # Would need to calculate from sessions
                    frustration_events=0,  # Would need to calculate from sessions
                    help_requests=0
                )
        except Exception as e:
            print(f"Error getting student analytics: {e}")
            return None

    # Educator operations
    def create_educator(self, educator: EducatorProfile) -> bool:
        """Create a new educator profile."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO educators (
                        id, name, email, institution, department, subjects,
                        areas_of_expertise, qualifications, years_of_experience,
                        courses_created, total_students_taught, can_create_courses,
                        can_review_content, can_view_analytics, can_manage_students,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    educator.id, educator.name, educator.email, educator.institution,
                    educator.department, json.dumps(educator.subjects),
                    json.dumps(educator.areas_of_expertise),
                    json.dumps(educator.qualifications),
                    educator.years_of_experience,
                    json.dumps(educator.courses_created),
                    educator.total_students_taught,
                    educator.can_create_courses, educator.can_review_content,
                    educator.can_view_analytics, educator.can_manage_students,
                    educator.created_at.isoformat()
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating educator: {e}")
            return False

    def get_educator(self, educator_id: str) -> Optional[EducatorProfile]:
        """Get educator profile by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM educators WHERE id = ?", (educator_id,))
                row = cursor.fetchone()

                if row:
                    return EducatorProfile(
                        id=row['id'],
                        name=row['name'],
                        email=row['email'],
                        institution=row['institution'],
                        department=row['department'],
                        subjects=json.loads(row['subjects']) if row['subjects'] else [],
                        areas_of_expertise=json.loads(row['areas_of_expertise']) if row['areas_of_expertise'] else [],
                        qualifications=json.loads(row['qualifications']) if row['qualifications'] else [],
                        years_of_experience=row['years_of_experience'],
                        courses_created=json.loads(row['courses_created']) if row['courses_created'] else [],
                        total_students_taught=row['total_students_taught'],
                        can_create_courses=row['can_create_courses'],
                        can_review_content=row['can_review_content'],
                        can_view_analytics=row['can_view_analytics'],
                        can_manage_students=row['can_manage_students'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                return None
        except Exception as e:
            print(f"Error getting educator: {e}")
            return None


# Global database instance
_db_instance = None

def get_database() -> EducationalDatabase:
    """Get global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = EducationalDatabase()
    return _db_instance
