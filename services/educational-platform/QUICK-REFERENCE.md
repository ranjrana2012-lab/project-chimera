# Educational Platform - Quick Reference Guide

## 🚀 Quick Start (5 minutes)

```bash
# 1. Navigate to service directory
cd <repo>/services/educational-platform

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the service
python main.py

# 5. Access the API
# Browser: http://localhost:8012/docs
# Health: curl http://localhost:8012/health/live
```

## 📚 Quick Demo

```bash
# Run the educator CLI demo
python educator_cli.py --demo
```

This will:
- Create an educator profile
- Create a sample course
- Create students with accessibility needs
- Enroll students
- Demonstrate content enhancement

## 🎯 Key Endpoints

### Students
```bash
# Create student
POST /api/v1/students
{"name": "Jane Smith", "email": "jane@bmet.ac.uk", "accessibility_needs": {"requires_bsl": true}}

# Get student
GET /api/v1/students/{student_id}

# Get analytics
GET /api/v1/students/{student_id}/analytics?days=30
```

### Courses
```bash
# Create course
POST /api/v1/courses
{"title": "Python Basics", "subject": "Computer Science", "educator_id": "..."}

# List courses
GET /api/v1/courses

# Get course
GET /api/v1/courses/{course_id}
```

### Accessibility
```bash
# Enhance content
POST /api/v1/content/enhance?content=Hello&student_id=...&session_id=...

# Translate to BSL
GET /api/v1/bsl/translate?text=Hello

# Get classroom sentiment
GET /api/v1/sentiment/classroom/{course_id}
```

## 🔧 Configuration

Edit `.env` file:

```bash
PORT=8012
BSL_AGENT_URL=http://localhost:8003
CAPTIONING_AGENT_URL=http://localhost:8002
SENTIMENT_AGENT_URL=http://localhost:8004
ENABLE_BSL=true
ENABLE_CAPTIONS=true
ENABLE_SENTIMENT=true
```

## 📊 Monitoring

### Metrics (Prometheus)
- `http://localhost:8012/metrics`

### Key Metrics to Watch
- `educational_active_students` - Active students
- `educational_engagement_score` - Engagement levels
- `educational_bsl_usage_total` - BSL usage
- `educational_sentiment_score` - Student sentiment

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=.
```

## 💡 Common Use Cases

### 1. Create an Accessible Course
```python
from models import Course, Lesson, DifficultyLevel

course = Course(
    title="Introduction to Python",
    subject="Computer Science",
    educator_id="educator_123",
    difficulty_level=DifficultyLevel.BEGINNER,
    lessons=[
        Lesson(
            title="Variables",
            bsl_available=True,  # ← BSL support
            captions_available=True  # ← Captions
        )
    ]
)
```

### 2. Create a Student with Accessibility Needs
```python
from models import StudentProfile, AccessibilityNeeds

student = StudentProfile(
    name="Alex Johnson",
    email="alex@bmet.ac.uk",
    accessibility_needs=AccessibilityNeeds(
        requires_bsl=True,
        requires_captions=True,
        font_size_preference="large"
    )
)
```

### 3. Monitor Classroom Sentiment
```bash
curl http://localhost:8012/api/v1/sentiment/classroom/course_123
```

## 🔌 WebSocket Connections

### Educator Dashboard
```javascript
const ws = new WebSocket('ws://localhost:8012/ws/educator/edu_123');

// Subscribe to course
ws.send(JSON.stringify({
  type: 'subscribe_course',
  course_id: 'course_123'
}));

// Get sentiment updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'sentiment_update') {
    console.log('Classroom sentiment:', data.data);
  }
};
```

### Student Learning
```javascript
const ws = new WebSocket('ws://localhost:8012/ws/student/student_123');

// Start session
ws.send(JSON.stringify({
  type: 'start_session',
  lesson_id: 'lesson_1',
  course_id: 'course_123'
}));

// Request BSL
ws.send(JSON.stringify({
  type: 'request_bsl',
  text: 'Hello, welcome to class'
}));
```

## 📁 File Locations

| File | Location |
|------|----------|
| Main Application | `<repo>/services/educational-platform/main.py` |
| Data Models | `models.py` |
| Database Layer | `database.py` |
| Integrations | `integrations.py` |
| Educator CLI | `educator_cli.py` |
| Example Curriculum | `examples.py` |
| Tests | `tests/test_api.py` |
| API Documentation | `<repo>/docs/api/educational-platform.md` |
| Architecture | `<repo>/docs/architecture/educational-platform-architecture.md` |

## 🎓 Example Curriculum

The service includes a complete Python programming course:
- 5 lessons with progression
- 3 skill modules
- 2 assessments (quiz + practical)
- Full accessibility support

Run it: `python examples.py`

## 🚨 Troubleshooting

### Service won't start
- Check port 8012 is available: `lsof -i :8012`
- Check dependencies: `pip list | grep fastapi`
- Check configuration: `cat .env`

### BSL integration not working
- Verify BSL agent: `curl http://localhost:8003/health/live`
- Check BSL_AGENT_URL in .env
- Check service logs for errors

### Database errors
- Delete database file: `rm educational_platform.db`
- Restart service (will recreate database)

## 📞 Getting Help

1. Check the API documentation: `http://localhost:8012/docs`
2. Review the architecture document
3. Check the implementation summary
4. Review example code in `examples.py`

## ✅ BMet Partnership Checklist

- [x] Student profile system with accessibility needs
- [x] Curriculum data model
- [x] Educational service (port 8012)
- [x] BSL agent integration
- [x] Captioning agent integration
- [x] Sentiment agent integration
- [x] Educator interface (CLI)
- [x] Example curriculum
- [x] API documentation
- [x] Architecture documentation
- [x] Testing suite
- [x] Metrics and monitoring

## 🎯 Next Steps

1. **Development Testing**
   - Run the quick demo
   - Test API endpoints
   - Review example curriculum

2. **Pilot Preparation**
   - Customize curriculum for BMet
   - Set up production database
   - Configure monitoring

3. **Deployment**
   - Set up Kubernetes deployment
   - Configure load balancer
   - Set up CDN for static content

4. **Integration**
   - Connect to BSL agent (port 8003)
   - Connect to captioning agent (port 8002)
   - Connect to sentiment agent (port 8004)

---

**For detailed information, see:**
- Implementation Summary: `IMPLEMENTATION-SUMMARY.md`
- API Documentation: `README.md`
- Architecture: `<repo>/docs/architecture/educational-platform-architecture.md`
