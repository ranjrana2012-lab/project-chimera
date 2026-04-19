# GitHub Repository Description Settings

## Repository Description (Short - 150 chars max)

```
AI-powered live theatre platform creating performances that adapt in real-time to audience input. Open-source for universities and theatre companies.
```

## Repository About Section (Longer Description)

```
Project Chimera is an open-source, student-run AI-powered live theatre platform that creates performances adapting in real-time to audience input.

🎭 Real-Time AI Performance Generation
• AI-generated dialogue and scenes with adaptive storytelling
• Multi-agent coordination with sentiment analysis
• Safety-first content moderation with human oversight

🌍 Accessibility & Global Reach
• Multi-language translation support (15 languages)
• Captioning capabilities
• Free for universities and educational institutions

🔧 Developer Friendly
• 8 microservices with FastAPI
• Comprehensive API documentation
• Docker-based deployment
• 78% test coverage with load testing framework

• 8 core services operational
• Production-ready with monitoring and alerting
• Complete documentation for developers and operators
```

## Repository Topics/Tags

```
ai, theatre, live-performance, sentiment-analysis, real-time,
microservices, fastapi, python, docker, adaptive-systems,
education, university, open-source, machine-learning,
nlp, entertainment, accessibility
```

## GitHub Website URL

```
https://ranjrana2012-lab.github.io/project-chimera/
```

## How to Update GitHub Repository Settings

### Option 1: Via GitHub Web Interface
1. Go to https://github.com/ranjrana2012-lab/project-chimera
2. Click Settings tab
3. Under "General" section:
   - Add description (short version)
   - Add website URL
   - Add topics (comma-separated)
4. Click "Save changes"

### Option 2: Via GitHub CLI (if authenticated)
```bash
gh repo edit ranjrana2012-lab/project-chimera \
  --description "AI-powered live theatre platform creating performances that adapt in real-time to audience input. Open-source for universities and theatre companies." \
  --homepage-url "https://ranjrana2012-lab.github.io/project-chimera/"
```

### Option 3: Via GitHub API
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/ranjrana2012-lab/project-chimera \
  -d '{
    "name": "project-chimera",
    "description": "AI-powered live theatre platform creating performances that adapt in real-time to audience input. Open-source for universities and theatre companies.",
    "homepage": "https://ranjrana2012-lab.github.io/project-chimera/",
    "topics": ["ai", "theatre", "live-performance", "sentiment-analysis", "real-time", "microservices", "fastapi", "python", "docker", "adaptive-systems", "education", "university", "open-source", "machine-learning", "nlp", "entertainment", "accessibility"]
  }'
```

## Social Media Preview

For Twitter/LinkedIn shares:
```
🎭 Project Chimera: AI-powered live theatre platform
Real-time adaptive performances for universities & theatres

🔗 https://github.com/ranjrana2012-lab/project-chimera

#AI #Theatre #OpenSource #EdTech
```

---

**Status**: Ready to apply
**Last Updated**: April 19, 2026
