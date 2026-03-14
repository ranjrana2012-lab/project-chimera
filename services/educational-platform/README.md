# Educational Platform Service

AI-powered educational platform with integrated accessibility features for Project Chimera.

## Overview

The Educational Platform Service leverages Project Chimera's accessibility agents (BSL, captioning, sentiment analysis) to create an inclusive learning environment. It implements research-backed educational AI agent principles from arXiv:2603.11709 "Scaling Laws for Educational AI Agents."

## Features

### Core Capabilities
- **Student Profile Management**: Comprehensive learner profiles with accessibility needs
- **Curriculum Management**: Courses, lessons, and learning objectives
- **Personalized Learning**: Adaptive content based on learning style and performance
- **Assessment System**: Quizzes, practical tasks, and skill evaluation
- **Learning Analytics**: Detailed engagement and performance tracking
- **Accessibility Integration**: BSL sign language, captions, and sentiment analysis

### Accessibility Features
- **BSL Agent Integration**: 107+ sign language animations for deaf students
- **Real-time Captioning**: Live transcription for audio/video content
- **Sentiment Analysis**: Monitor student engagement and wellbeing
- **Adaptive Content**: Automatically adjusts to accessibility needs

### Educator Tools
- **Content Creation**: Easy course and lesson authoring
- **Student Monitoring**: Real-time classroom sentiment tracking
- **Analytics Dashboard**: Detailed learning outcomes and engagement metrics
- **Assessment Management**: Create and grade assessments

## Architecture

### Data Models
- **StudentProfile**: Comprehensive learner profile with accessibility needs
- **Course & Lesson**: Structured curriculum with prerequisites
- **Enrollment**: Student progress tracking through courses
- **Assessment & Attempt**: Testing and skill evaluation
- **LearningSession**: Detailed session analytics
- **LearningAnalytics**: Aggregated performance metrics

### Integration Agents
1. **BSL Agent** (port 8003)
   - Text-to-sign-language translation
   - 3D avatar rendering
   - 107+ animations (phrases, alphabet, numbers, emotions)

2. **Captioning Agent** (port 8002)
   - Speech-to-text transcription
   - Real-time streaming
   - Multi-language support

3. **Sentiment Agent** (port 8004)
   - Emotion analysis
   - Engagement tracking
   - Frustration detection

## Quick Start

### Installation

```bash
# Navigate to service directory
cd services/educational-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Running the Service

```bash
# Start the service
python main.py
```

The service will start on `http://localhost:8012`

### API Documentation

Once running, access the interactive API documentation:
- Swagger UI: `http://localhost:8012/docs`
- ReDoc: `http://localhost:8012/redoc`

## Usage Examples

### Creating a Student Profile

```bash
curl -X POST http://localhost:8012/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@bmet.ac.uk",
    "grade_level": "Year 10",
    "institution": "BMet College",
    "learning_style": "visual",
    "accessibility_needs": {
      "requires_bsl": true,
      "requires_captions": true
    }
  }'
```

### Creating a Course

```bash
curl -X POST http://localhost:8012/api/v1/courses \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to Computer Science",
    "description": "Learn the fundamentals of programming",
    "subject": "Computer Science",
    "grade_level": "Year 10",
    "educator_id": "educator_123",
    "educator_name": "Dr. Smith",
    "lessons": [
      {
        "title": "Variables and Data Types",
        "description": "Understanding variables in Python",
        "content_type": "interactive",
        "duration_minutes": 30,
        "bsl_available": true,
        "captions_available": true
      }
    ]
  }'
```

### Enrolling a Student

```bash
curl -X POST http://localhost:8012/api/v1/enrollments \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "course_id": "course_456"
  }'
```

### Enhancing Content with Accessibility

```bash
curl -X POST http://localhost:8012/api/v1/content/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Welcome to today lesson on variables",
    "student_id": "student_123",
    "session_id": "session_789"
  }'
```

### Getting Classroom Sentiment

```bash
curl http://localhost:8012/api/v1/sentiment/classroom/course_456
```

## WebSocket Connections

### Educator Dashboard

```javascript
const ws = new WebSocket('ws://localhost:8012/ws/educator/educator_123');

ws.onopen = () => {
  // Subscribe to course updates
  ws.send(JSON.stringify({
    type: 'subscribe_course',
    course_id: 'course_456'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'sentiment_update') {
    console.log('Classroom sentiment:', data.data);
  }
};
```

### Student Learning Session

```javascript
const ws = new WebSocket('ws://localhost:8012/ws/student/student_123');

ws.onopen = () => {
  // Start learning session
  ws.send(JSON.stringify({
    type: 'start_session',
    lesson_id: 'lesson_abc',
    course_id: 'course_456'
  }));
};

// Request BSL translation
ws.send(JSON.stringify({
  type: 'request_bsl',
  text: 'Hello, welcome to the lesson'
}));
```

## API Endpoints

### Health & Metrics
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/metrics` - Platform metrics

### Student Management
- `POST /api/v1/students` - Create student profile
- `GET /api/v1/students/{student_id}` - Get student profile
- `PUT /api/v1/students/{student_id}` - Update student profile
- `GET /api/v1/students/{student_id}/analytics` - Get learning analytics

### Course Management
- `POST /api/v1/courses` - Create course
- `GET /api/v1/courses/{course_id}` - Get course
- `GET /api/v1/courses` - List courses

### Enrollment & Learning
- `POST /api/v1/enrollments` - Enroll student in course
- `GET /api/v1/enrollments/{student_id}/{course_id}` - Get enrollment
- `POST /api/v1/sessions` - Create learning session
- `GET /api/v1/sessions/{student_id}` - Get student sessions

### Assessments
- `POST /api/v1/assessments/{assessment_id}/attempts` - Submit attempt

### Accessibility Integration
- `POST /api/v1/content/enhance` - Enhance content with accessibility
- `GET /api/v1/bsl/translate` - Translate to BSL
- `GET /api/v1/sentiment/classroom/{course_id}` - Get classroom sentiment

### Recommendations
- `GET /api/v1/recommendations/{student_id}` - Get personalized recommendations

### Educator Management
- `POST /api/v1/educators` - Create educator profile
- `GET /api/v1/educators/{educator_id}` - Get educator profile

## Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8012 | Service port |
| `BSL_AGENT_URL` | http://localhost:8003 | BSL agent endpoint |
| `CAPTIONING_AGENT_URL` | http://localhost:8002 | Captioning agent endpoint |
| `SENTIMENT_AGENT_URL` | http://localhost:8004 | Sentiment agent endpoint |
| `ENABLE_BSL` | true | Enable BSL integration |
| `ENABLE_CAPTIONS` | true | Enable captioning integration |
| `ENABLE_SENTIMENT` | true | Enable sentiment analysis |

## Metrics

The service exposes Prometheus metrics for monitoring:

### Student Metrics
- `educational_active_students` - Active students by course
- `educational_student_sessions_total` - Total learning sessions
- `educational_learning_time_seconds` - Time spent learning

### Content Metrics
- `educational_lesson_completion_total` - Lessons completed
- `educational_content_access_total` - Content accesses by type

### Assessment Metrics
- `educational_assessment_attempts_total` - Assessment attempts
- `educational_assessment_scores` - Score distribution
- `educational_skills_mastered_total` - Skills mastered

### Engagement Metrics
- `educational_engagement_score` - Current engagement by student
- `educational_sentiment_score` - Sentiment by student
- `educational_frustration_events_total` - Frustration events

### Accessibility Metrics
- `educational_bsl_usage_total` - BSL usage count
- `educational_captions_usage_total` - Captions usage count
- `educational_audio_description_usage_total` - Audio description usage

## Development

### Running Tests

```bash
pytest tests/ -v --cov=.
```

### Database Schema

The service uses SQLite (configurable for other databases). Tables include:
- `students` - Student profiles
- `skills` - Skill definitions
- `courses` - Course definitions
- `lessons` - Lesson content
- `assessments` - Assessment definitions
- `enrollments` - Student enrollments
- `assessment_attempts` - Assessment attempts
- `learning_sessions` - Learning session records
- `educators` - Educator profiles

## BMet Partnership

This platform is designed for potential BMet partnership with focus on:
1. **Accessibility First**: BSL and captioning at the core
2. **Real-time Monitoring**: Classroom sentiment tracking
3. **Personalized Learning**: Adaptive content delivery
4. **Educator Empowerment**: Simple content creation tools
5. **Comprehensive Analytics**: Learning outcomes tracking

## Future Enhancements

- [ ] Advanced ML-based recommendation engine
- [ ] Video content integration with BSL avatar overlay
- [ ] Peer collaboration features
- [ ] Parent/guardian monitoring portal
- [ ] Mobile application
- [ ] Offline mode with sync
- [ ] Advanced analytics dashboard
- [ ] Integration with learning management systems (LMS)

## License

Project Chimera - Educational Platform Service
Copyright 2026

## Support

For issues and questions, please contact the Project Chimera team.
