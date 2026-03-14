# Educational Platform API Documentation

**Version:** v1.0.0
**Base URL:** `http://localhost:8012`
**Service:** AI-powered educational platform with accessibility integration

---

## Overview

The Educational Platform Service provides:
- Student profile management with accessibility needs
- Course and curriculum management
- Personalized learning recommendations
- Assessment and feedback systems
- Learning analytics and insights
- Integration with BSL, captioning, and sentiment agents

---

## Endpoints

### Health & Metrics

#### Health Check
**Endpoint:** `GET /health/live`
**Response:** `{"status": "alive"}`

#### Readiness Check
**Endpoint:** `GET /health/ready`
**Response:**
```json
{
  "status": "ready",
  "service": "educational-platform",
  "timestamp": "2026-03-14T12:00:00Z",
  "dependencies": {
    "database": true,
    "content_integrator": true
  }
}
```

#### Platform Metrics
**Endpoint:** `GET /api/v1/metrics`
**Response:**
```json
{
  "active_students": 150,
  "active_courses": 25,
  "total_sessions_today": 450,
  "average_engagement": 0.72,
  "accessibility_usage": {
    "bsl": 89,
    "captions": 142,
    "audio_description": 23
  }
}
```

---

### Student Management

#### Create Student Profile
**Endpoint:** `POST /api/v1/students`

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@bmet.ac.uk",
  "grade_level": "Year 10",
  "institution": "BMet College",
  "learning_style": "visual",
  "interests": ["programming", "math"],
  "goals": ["Learn Python", "Build projects"],
  "accessibility_needs": {
    "requires_bsl": true,
    "requires_captions": true,
    "requires_audio_description": false,
    "requires_high_contrast": false,
    "font_size_preference": "large"
  },
  "accessibility_level": "significant"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Student profile created successfully",
  "data": {
    "student_id": "abc123-def456-ghi789"
  }
}
```

#### Get Student Profile
**Endpoint:** `GET /api/v1/students/{student_id}`

**Response:**
```json
{
  "id": "abc123-def456-ghi789",
  "name": "Jane Smith",
  "email": "jane.smith@bmet.ac.uk",
  "grade_level": "Year 10",
  "learning_style": "visual",
  "accessibility_needs": {
    "requires_bsl": true,
    "requires_captions": true
  },
  "average_engagement_score": 0.75,
  "total_learning_time_minutes": 450
}
```

#### Update Student Profile
**Endpoint:** `PUT /api/v1/students/{student_id}`

**Request Body:**
```json
{
  "grade_level": "Year 11",
  "interests": ["programming", "math", "robotics"]
}
```

#### Get Student Analytics
**Endpoint:** `GET /api/v1/students/{student_id}/analytics?days=30`

**Response:**
```json
{
  "student_id": "abc123-def456-ghi789",
  "period_start": "2026-02-12T00:00:00Z",
  "period_end": "2026-03-14T00:00:00Z",
  "total_sessions": 25,
  "total_learning_time_minutes": 750,
  "average_session_length_minutes": 30.0,
  "average_engagement_score": 0.75,
  "assessments_completed": 8,
  "average_assessment_score": 0.82,
  "skills_mastered": 5,
  "courses_started": 3,
  "courses_completed": 1,
  "completion_rate": 0.33
}
```

---

### Course Management

#### Create Course
**Endpoint:** `POST /api/v1/courses`

**Request Body:**
```json
{
  "title": "Introduction to Python Programming",
  "description": "Learn Python fundamentals",
  "subject": "Computer Science",
  "grade_level": "Year 10",
  "educator_id": "edu_123",
  "educator_name": "Dr. Smith",
  "department": "Digital Technologies",
  "difficulty_level": "beginner",
  "estimated_duration_hours": 10.0,
  "lessons": [
    {
      "title": "Variables and Data Types",
      "description": "Understanding variables",
      "content_type": "interactive",
      "duration_minutes": 30,
      "bsl_available": true,
      "captions_available": true,
      "text_content": "# Variables\\nVariables are containers..."
    }
  ],
  "learning_objectives": [
    {
      "title": "Write Python Programs",
      "description": "Create working Python programs",
      "blooms_taxonomy_level": "create"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Course created successfully",
  "data": {
    "course_id": "course_abc123"
  }
}
```

#### Get Course
**Endpoint:** `GET /api/v1/courses/{course_id}`

**Response:**
```json
{
  "id": "course_abc123",
  "title": "Introduction to Python Programming",
  "description": "Learn Python fundamentals",
  "subject": "Computer Science",
  "grade_level": "Year 10",
  "lessons": [...],
  "difficulty_level": "beginner",
  "estimated_duration_hours": 10.0,
  "educator_id": "edu_123",
  "educator_name": "Dr. Smith"
}
```

#### List Courses
**Endpoint:** `GET /api/v1/courses?educator_id={edu_id}&is_published=true`

**Query Parameters:**
- `educator_id` (optional): Filter by educator
- `is_published` (optional): Filter by published status

---

### Enrollment & Learning

#### Enroll Student in Course
**Endpoint:** `POST /api/v1/enrollments`

**Query Parameters:**
- `student_id`: Student ID
- `course_id`: Course ID

**Response:**
```json
{
  "success": true,
  "message": "Enrollment created successfully",
  "data": {
    "enrollment_id": "enroll_xyz789"
  }
}
```

#### Get Enrollment
**Endpoint:** `GET /api/v1/enrollments/{student_id}/{course_id}`

**Response:**
```json
{
  "id": "enroll_xyz789",
  "student_id": "student_abc",
  "course_id": "course_xyz",
  "enrolled_at": "2026-03-01T10:00:00Z",
  "progress_percentage": 65.0,
  "lessons_completed": ["lesson_1", "lesson_2"],
  "current_lesson_id": "lesson_3",
  "is_active": true,
  "average_assessment_score": 0.82
}
```

#### Create Learning Session
**Endpoint:** `POST /api/v1/sessions`

**Request Body:**
```json
{
  "student_id": "student_abc",
  "lesson_id": "lesson_3",
  "course_id": "course_xyz",
  "engagement_score": 0.8,
  "accessibility_features_used": ["bsl", "captions"]
}
```

#### Get Student Sessions
**Endpoint:** `GET /api/v1/sessions/{student_id}?limit=50`

---

### Assessments

#### Submit Assessment Attempt
**Endpoint:** `POST /api/v1/assessments/{assessment_id}/attempts`

**Request Body:**
```json
{
  "assessment_id": "assessment_123",
  "student_id": "student_abc",
  "attempt_number": 1,
  "answers": {
    "q1": "a",
    "q2": "b",
    "q3": "c"
  },
  "engagement_score": 0.7,
  "sentiment_score": 0.5,
  "frustration_indicators": []
}
```

**Response:**
```json
{
  "success": true,
  "message": "Assessment attempt recorded successfully",
  "data": {
    "attempt_id": "attempt_456",
    "passed": true
  }
}
```

---

### Accessibility Integration

#### Enhance Content with Accessibility
**Endpoint:** `POST /api/v1/content/enhance`

**Query Parameters:**
- `content`: Text content to enhance
- `student_id`: Student ID
- `session_id`: Session ID

**Response:**
```json
{
  "success": true,
  "message": "Content enhanced with accessibility features",
  "data": {
    "original_content": "Welcome to Python!",
    "accessibility_features": ["bsl", "captions"],
    "bsl_animation": {
      "animation_data": {...}
    },
    "captions_available": true
  }
}
```

#### Translate to BSL
**Endpoint:** `GET /api/v1/bsl/translate?text=Hello`

**Response:**
```json
{
  "success": true,
  "message": "Text translated to BSL",
  "data": {
    "gloss": "HELLO",
    "breakdown": ["HELLO"],
    "duration_estimate": 1.5,
    "confidence": 0.95
  }
}
```

#### Get Classroom Sentiment
**Endpoint:** `GET /api/v1/sentiment/classroom/{course_id}`

**Response:**
```json
{
  "course_id": "course_xyz",
  "sentiment_trend": {
    "trend": "rising",
    "current_score": 0.7,
    "change": "+0.2"
  },
  "emotion_breakdown": {
    "emotions": {
      "joy": 0.65,
      "surprise": 0.15,
      "neutral": 0.15,
      "confusion": 0.05
    },
    "dominant": "joy"
  }
}
```

---

### Recommendations

#### Get Personalized Recommendations
**Endpoint:** `GET /api/v1/recommendations/{student_id}`

**Response:**
```json
[
  {
    "student_id": "student_abc",
    "recommended_lessons": ["lesson_5", "lesson_6"],
    "recommended_courses": [],
    "recommended_skills": ["loops", "functions"],
    "reason": "High engagement - ready for more challenging content",
    "confidence_score": 0.8,
    "based_on_data": ["engagement_scores", "performance"],
    "accessibility_match": true
  }
]
```

---

### Educator Management

#### Create Educator Profile
**Endpoint:** `POST /api/v1/educators`

**Request Body:**
```json
{
  "name": "Dr. Sarah Chen",
  "email": "sarah.chen@bmet.ac.uk",
  "institution": "BMet College",
  "department": "Digital Technologies",
  "subjects": ["Computer Science", "Mathematics"],
  "areas_of_expertise": ["Programming", "Data Science"],
  "qualifications": ["PhD", "PGCE"],
  "years_of_experience": 15
}
```

**Response:**
```json
{
  "success": true,
  "message": "Educator profile created successfully",
  "data": {
    "educator_id": "educator_123"
  }
}
```

#### Get Educator Profile
**Endpoint:** `GET /api/v1/educators/{educator_id}`

---

## WebSocket Endpoints

### Educator Dashboard
**Endpoint:** `WS /ws/educator/{educator_id}`

**Client Messages:**
```json
{"type": "subscribe_course", "course_id": "course_123"}
{"type": "get_sentiment", "course_id": "course_123"}
{"type": "ping"}
```

**Server Messages:**
```json
{"type": "subscription_confirmed", "course_id": "course_123"}
{"type": "sentiment_update", "data": {...}}
{"type": "pong"}
```

### Student Learning Session
**Endpoint:** `WS /ws/student/{student_id}`

**Client Messages:**
```json
{"type": "start_session", "lesson_id": "lesson_1", "course_id": "course_1"}
{"type": "update_engagement", "engagement_score": 0.8}
{"type": "request_bsl", "text": "Hello"}
```

**Server Messages:**
```json
{"type": "session_started", "session_id": "session_123"}
{"type": "engagement_updated", "engagement_score": 0.8}
{"type": "bsl_animation", "data": {...}}
```

---

## Data Models

### StudentProfile
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Student name |
| `email` | string | Email address |
| `grade_level` | string | Grade/Year level |
| `learning_style` | enum | visual, auditory, kinesthetic, read_write, multimodal |
| `accessibility_needs` | object | Accessibility requirements |
| `average_engagement_score` | float | Engagement 0.0-1.0 |

### Course
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `title` | string | Course title |
| `subject` | string | Subject area |
| `lessons` | array | Course lessons |
| `difficulty_level` | enum | beginner, intermediate, advanced, expert |
| `educator_id` | string | Creator educator ID |

### Lesson
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `title` | string | Lesson title |
| `content_type` | enum | text, video, interactive, bsl_animation, assessment |
| `duration_minutes` | int | Estimated duration |
| `bsl_available` | boolean | BSL translation available |
| `captions_available` | boolean | Captions available |

### Assessment
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `title` | string | Assessment title |
| `assessment_type` | enum | quiz, practical, project, oral, peer_review |
| `questions` | array | Assessment questions |
| `passing_score_threshold` | float | Required score 0.0-1.0 |

---

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8012 | Service port |
| `BSL_AGENT_URL` | http://localhost:8003 | BSL agent endpoint |
| `CAPTIONING_AGENT_URL` | http://localhost:8002 | Captioning agent endpoint |
| `SENTIMENT_AGENT_URL` | http://localhost:8004 | Sentiment agent endpoint |
| `ENABLE_BSL` | true | Enable BSL integration |
| `ENABLE_CAPTIONS` | true | Enable captioning integration |
| `ENABLE_SENTIMENT` | true | Enable sentiment analysis |

---

## Metrics

Prometheus metrics exposed at `/metrics`:

### Student Metrics
- `educational_active_students` - Active students by course
- `educational_total_students` - Total registered students
- `educational_learning_time_seconds` - Time spent learning

### Content Metrics
- `educational_lesson_completion_total` - Lessons completed
- `educational_content_access_total` - Content accesses by type

### Engagement Metrics
- `educational_engagement_score` - Current engagement by student
- `educational_sentiment_score` - Sentiment by student

### Accessibility Metrics
- `educational_bsl_usage_total` - BSL usage count
- `educational_captions_usage_total` - Captions usage count

---

*Last Updated: March 2026*
*Educational Platform v1.0.0*
