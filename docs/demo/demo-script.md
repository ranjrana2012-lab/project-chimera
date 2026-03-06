# Project Chimera Demo Script

**Duration:** 30 minutes
**Audience:** Students
**Presenter:** [Your Name]
**Date:** Monday, March 10, 2026

## Pre-Demo Setup (Before Students Arrive)

1. Open browser tabs:
   - http://localhost:8007 (Operator Console)
   - http://localhost:3000 (Grafana - login: admin/admin)
   - http://localhost:16686 (Jaeger)
   - http://localhost:9090 (Prometheus)

2. Run pre-demo checks:
   ```bash
   ./scripts/demo-status.sh
   ```

3. Have terminal ready with demo script visible

4. Prepare sample requests in separate terminal windows

---

## Demo Script

### 0:00 - 0:05: Introduction and System Overview (5 minutes)

**[Slide: Project Chimera Title]**

"Good morning everyone! Today I'm excited to show you Project Chimera, an AI-powered live theatre platform that's revolutionizing accessibility in performing arts."

**[Slide: What is Project Chimera?]**

"Project Chimera provides real-time accessibility features for live theatre:

- AI-generated dialogue for script assistance
- Live captioning for deaf and hard-of-hearing audiences
- British Sign Language translation
- Sentiment analysis to gauge audience reaction
- Content safety filtering

All of this happens in real-time, powered by a distributed microservices architecture."

**[Slide: Architecture Diagram]**

"Let me show you how the system works. [point to diagram]

At the center is the **OpenClaw Orchestrator** - it's the brain that routes requests to the right AI services.

Surrounding it are our specialized AI agents:
- **SceneSpeak** generates theatrical dialogue
- **Captioning Service** transcribes speech in real-time
- **BSL Agent** translates text to British Sign Language gloss
- **Sentiment Analysis** understands emotional tone
- **Safety Filter** ensures content is appropriate

Everything is connected through NATS messaging, and we have full observability with Prometheus, Grafana, and Jaeger."

**[Show running services]**

"All of these services are currently running. Let me show you..."

```bash
docker-compose ps
```

"You can see 8 services running - all green and healthy!"

---

### 0:05 - 0:10: Orchestrator Demo (5 minutes)

**[Switch to browser: Operator Console]**

"Let's start with the heart of the system - the Orchestrator."

**[Switch to terminal]**

"The Orchestrator exposes a simple API endpoint at `/v1/orchestrate`. You tell it what skill you need and provide input, and it handles the rest."

**[Execute first request]**

```bash
curl -X POST http://localhost:8000/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "dialogue_generator",
    "input": {
      "prompt": "A mysterious figure enters the stage",
      "style": "dramatic"
    }
  }'
```

**[Wait for response, show output]**

"Look at that! In under 500ms, we got back a dramatic dialogue snippet. The Orchestrator:

1. Received the request
2. Identified it needed the dialogue_generator skill
3. Routed it to SceneSpeak via NATS
4. Got the generated dialogue back
5. Returned it to us

All with automatic tracing and metrics collection!"

**[Switch to Jaeger UI]**

"Let me show you the trace of that request..."

**[Find and display the trace]**

"You can see every step of the journey - how long each service took, the dependencies between services. This is incredibly powerful for debugging and optimization."

---

### 0:10 - 0:20: AI Agents Demo (10 minutes)

**[Slide: AI Agents Overview]**

"Now let's dive into each AI agent and see what they can do."

#### SceneSpeak - Dialogue Generation (2 minutes)

**[Switch to terminal]**

"First up, SceneSpeak. This is our creative engine - it generates theatrical dialogue."

```bash
curl -X POST http://localhost:8001/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The detective discovers the hidden letter",
    "style": "suspenseful",
    "max_tokens": 100
  }'
```

**[Show response]**

"Perfect! It captured the suspenseful tone and created context-appropriate dialogue. This can help playwrights overcome writer's block or generate variations during rehearsals."

#### Captioning Service (2 minutes)

"Next, the Captioning Service. In a real theatre setup, this would listen to the actors via microphones and display captions in real-time."

```bash
curl -X POST http://localhost:8002/v1/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio_placeholder",
    "language": "en"
  }'
```

**[Explain]**

"For this demo, we're using text input, but in production it processes audio streams. The service uses speech-to-text AI and can handle various accents and theatrical speech patterns."

#### BSL Agent (2 minutes)

**[Slide: BSL Translation]**

"One of our most innovative features is the BSL Agent. British Sign Language is a completely different language from English, with its own grammar and structure."

```bash
curl -X POST http://localhost:8003/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello and welcome to the theatre. I hope you enjoy the show!",
    "source_language": "en",
    "target_format": "gloss"
  }'
```

**[Show response]**

"The agent translates English text into BSL gloss notation. This can drive digital avatar systems or help human signers prepare their translations in advance."

#### Sentiment Analysis (2 minutes)

"Sentiment Analysis helps us understand the emotional tone of dialogue - useful for both content creation and audience feedback."

```bash
curl -X POST http://localhost:8004/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is absolutely terrible! I demand my money back!"
  }'
```

**[Show response]**

"You can see it detected:
- **Negative sentiment** (-0.8)
- **Anger** as the dominant emotion
- **High intensity** (0.9)

This could alert theatre staff to audience dissatisfaction in real-time!"

#### Safety Filter (2 minutes)

"Finally, the Safety Filter ensures all content is appropriate for the venue's policies."

```bash
curl -X POST http://localhost:8006/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What a wonderful performance!",
    "policy": "family"
  }'
```

**[Show response]**

"It passes the safety check. But watch what happens with inappropriate content..."

```bash
curl -X POST http://localhost:8006/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[INAPPROPRIATE CONTENT]",
    "policy": "family"
  }'
```

**[Show flagged response]**

"The Safety Filter catches it and can automatically filter or flag the content for review."

---

### 0:20 - 0:25: Operator Console Demo (5 minutes)

**[Switch to browser: Operator Console]**

"Now let's look at the Operator Console - our real-time monitoring dashboard."

**[Show main dashboard]**

"This gives us a complete view of the system health:

- **Service Status**: All services green and healthy
- **Request Rate**: Currently processing X requests/second
- **Response Times**: P50, P95, P99 latencies
- **Error Rates**: Near zero (as expected!)

**[Navigate to metrics page]**

"We can dive deeper into each service. Let's look at the Dialogue Generator..."

**[Show service-specific metrics]**

"You can see:
- Requests per minute
- Average response time
- Success rate
- Resource utilization

This helps us identify bottlenecks before they impact the audience."

**[Show alerts]**

"We can set up alerts for any metric. If a service starts failing or response times spike, we get notified immediately."

---

### 0:25 - 0:30: Observability Demo (5 minutes)

**[Slide: Observability Stack]**

"Let's wrap up with our observability tools - essential for any production system."

#### Grafana Dashboards (2 minutes)

**[Switch to Grafana]**

"Grafana gives us beautiful visualizations of all our metrics."

**[Show system overview dashboard]**

"This is our main dashboard showing CPU, memory, network, and request metrics across all services."

**[Show AI performance dashboard]**

"We have specialized dashboards too - this one tracks AI model performance:
- Token generation rate
- Model accuracy
- Inference time per model

This helps us optimize which models to use for different scenarios."

#### Prometheus (1 minute)

**[Switch to Prometheus]**

"Under the hood, Prometheus scrapes metrics from all services using the standard Prometheus format."

**[Run a sample query]**

"We can run any PromQL query. Let's see the request rate for the last hour..."

**[Execute and show query]**

"`rate(http_requests_total[5m])` - you can see we have a steady stream of requests."

#### Jaeger Tracing (2 minutes)

**[Switch to Jaeger]**

"Finally, Jaeger provides distributed tracing - we can follow a single request through the entire system."

**[Pull up a complex trace]**

"This trace shows a request that went through:
1. Orchestrator
2. SceneSpeak (dialogue generation)
3. Sentiment Analysis
4. Safety Filter

You can see exactly how long each service took and where the bottlenecks are."

**[Show trace details]**

"If we zoom in... you can see the actual request/response data, logs, and timings for each span."

---

### 0:30: Conclusion and Q&A (3 minutes)

**[Slide: Summary]**

"To summarize, Project Chimera demonstrates:

- **Microservices Architecture** - 8 independent services working together
- **AI Integration** - Multiple AI models for different tasks
- **Real-time Processing** - Sub-second response times
- **Full Observability** - Metrics, logs, and tracing
- **Production Ready** - Health checks, safety, monitoring

All built with modern technologies and designed for scale."

**[Slide: What's Next]**

"Future enhancements we're planning:
- More language support for BSL
- Real-time avatar generation
- Audience interaction features
- Multi-venue support"

**[Slide: Q&A]**

"Now, I'd love to answer your questions! But first, let me share how you can explore Project Chimera yourself."

**[Show GitHub/info slide]**

"The code is open source. You can:
- Clone the repository
- Run `docker-compose up`
- Try the sample requests
- Build your own AI agents!

Links are in the demo materials."

**[Open floor for questions]**

---

## Post-Demo Activities

1. **Distribute Feedback Forms**
2. **Stay for Individual Questions**
3. **Clean Up Demo Environment** (after students leave)
4. **Document Any Issues Encountered**

## Contingency Plans

### If a Service Goes Down During Demo

```bash
# Restart the service
docker-compose restart <service-name>

# If that doesn't work
docker-compose down
./scripts/demo-start.sh
```

### If Response is Slow

"Performance varies based on load. Let me try that again..." (Retry request)

### If Browser Won't Load

"Let me use the command line instead..." (Show curl requests in terminal)

### If Demo Time is Running Short

- Skip observability section
- Combine AI agent demos
- Focus on highlights only

---

## Practice Notes

- **Pacing**: 30 minutes is tight - practice transitions
- **Backup**: Keep terminal commands in a text file for quick copying
- **Engagement**: Ask questions throughout, not just at the end
- **Flexibility**: Be ready to skip sections if running behind
- **Energy**: Keep enthusiasm high - this is exciting technology!

---

**Script Version:** 1.0
**Last Updated:** 2026-03-06
**Rehearsal Check:** [ ] Practiced with timer [ ] Tested all demos [ ] Backup plans ready
