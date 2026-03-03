# WorldMonitor Context Usage Guide

This guide provides practical examples for using the WorldMonitor integration with the Sentiment Agent to enrich sentiment analysis with real-time global context.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The WorldMonitor integration provides:

- **Real-time global context** - Streaming events from WorldMonitor sidecar
- **News sentiment analysis** - Understand current events impact
- **Context-aware scoring** - Sentiment analysis enriched with global events
- **Category filtering** - Focus on specific event categories

## Quick Start

### 1. Check WorldMonitor Status

First, verify WorldMonitor is connected:

```bash
curl http://sentiment-agent:8004/health/ready
```

Response should include `"worldmonitor_connected": true`.

### 2. Get Current Context

Retrieve the current global context:

```bash
curl http://sentiment-agent:8004/api/v1/context
```

### 3. Analyze with Context

Perform sentiment analysis with context enrichment:

```bash
curl -X POST http://sentiment-agent:8004/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["The tech references in this show are so timely!"],
    "include_context": true
  }'
```

## Basic Usage

### Sentiment Analysis Without Context

```python
import requests

response = requests.post(
    "http://sentiment-agent:8004/api/v1/analyze",
    json={
        "texts": [
            "Amazing performance!",
            "I love the tech references"
        ]
    }
)

data = response.json()
for result in data["results"]:
    print(f"{result['text']} -> {result['sentiment']} ({result['confidence']:.2f})")
```

### Sentiment Analysis With Context

```python
import requests

response = requests.post(
    "http://sentiment-agent:8004/api/v1/analyze",
    json={
        "texts": ["The tech references feel so timely!"],
        "include_context": True
    }
)

data = response.json()

# Basic sentiment results
for result in data["results"]:
    print(f"Sentiment: {result['sentiment']}")

# Context information
print("\nContext:")
for event in data["context"]["global_events"]:
    print(f"- {event['headline']}: {event['sentiment']}")
```

### Get Context by Category

```python
import requests

# Get only technology events
response = requests.get(
    "http://sentiment-agent:8004/api/v1/context?category=technology"
)

data = response.json()
print(f"Technology events: {data['metadata']['total_events']}")

for event in data["events"]:
    print(f"- {event['headline']}")
```

## Advanced Usage

### News Sentiment Analysis

Analyze the sentiment of news headlines:

```python
import requests

headlines = [
    "AI breakthrough transforms healthcare industry",
    "Markets show volatility amid economic concerns",
    "New streaming service launches with revolutionary features"
]

response = requests.post(
    "http://sentiment-agent:8004/api/v1/news-sentiment",
    json={
        "headlines": headlines,
        "categories": ["technology", "business"]
    }
)

data = response.json()

print(f"Overall Sentiment: {data['overall_sentiment']}\n")

for result in data["results"]:
    print(f"{result['headline']}")
    print(f"  Sentiment: {result['sentiment']} (score: {result['score']:.2f})")
    print(f"  Category: {result['category']}\n")
```

### Context Statistics

Get statistics about current context data:

```python
import requests

response = requests.get(
    "http://sentiment-agent:8004/api/v1/context/stats"
)

data = response.json()

stats = data["statistics"]
print(f"Total Events: {stats['total_events']}")
print(f"By Category: {stats['by_category']}")
print(f"Sentiment Distribution: {stats['sentiment_distribution']}")
```

### Force Context Refresh

Force a refresh of the context cache:

```python
import requests

response = requests.get(
    "http://sentiment-agent:8004/api/v1/context?refresh=true"
)

data = response.json()
cache_info = data["metadata"]
print(f"Last Updated: {cache_info['last_updated']}")
print(f"Cache Age: {cache_info['cache_age_seconds']}s")
```

### Batch Analysis with Context Categories

Analyze multiple texts with specific context categories:

```python
import requests

texts = [
    "The AI references feel so current!",
    "Love how they incorporated the tech news"
]

response = requests.post(
    "http://sentiment-agent:8004/api/v1/analyze-with-context",
    json={
        "texts": texts,
        "include_context": True,
        "context_categories": ["technology", "business"]
    }
)

data = response.json()

# Results will include context filtered by specified categories
for event in data["context"]["global_events"]:
    print(f"Context: {event['headline']}")
```

## Use Cases

### 1. Content Performance Analysis

Understand how content performs relative to current events:

```python
def analyze_content_performance(content: str):
    response = requests.post(
        "http://sentiment-agent:8004/api/v1/analyze-with-context",
        json={
            "texts": [content],
            "include_context": True
        }
    )

    data = response.json()
    result = data["results"][0]
    context = data["context"]

    # Check if content aligns with positive global events
    positive_events = [
        e for e in context["global_events"]
        if e["sentiment"] == "positive"
    ]

    return {
        "content_sentiment": result["sentiment"],
        "positive_context_count": len(positive_events),
        "recommendation": "aligns_with_positive_trends" if len(positive_events) > 0 else "neutral"
    }

# Example
analysis = analyze_content_performance("The AI innovation scene was inspiring!")
print(analysis)
```

### 2. Real-time Content Adaptation

Adapt content based on current global sentiment:

```python
def get_context_recommendation():
    response = requests.get(
        "http://sentiment-agent:8004/api/v1/context/stats"
    )

    data = response.json()
    sentiment_dist = data["statistics"]["sentiment_distribution"]

    if sentiment_dist["positive"] > sentiment_dist["negative"]:
        return "positive_theme"
    elif sentiment_dist["negative"] > sentiment_dist["positive"]:
        return "cautious_approach"
    else:
        return "neutral_ground"

# Use recommendation for content generation
theme = get_context_recommendation()
print(f"Recommended theme: {theme}")
```

### 3. News Impact Assessment

Assess how news events might impact audience sentiment:

```python
def assess_news_impact(headlines: list[str]):
    # Analyze headlines
    response = requests.post(
        "http://sentiment-agent:8004/api/v1/news-sentiment",
        json={
            "headlines": headlines,
            "categories": ["technology", "business", "entertainment"]
        }
    )

    data = response.json()

    # Calculate impact score
    avg_score = sum(r["score"] for r in data["results"]) / len(data["results"])

    return {
        "impact_level": "high" if avg_score > 0.7 else "medium" if avg_score > 0.4 else "low",
        "overall_sentiment": data["overall_sentiment"],
        "category_breakdown": data["category_summary"]
    }

# Example
impact = assess_news_impact([
    "Major AI breakthrough announced",
    "Tech stocks surge on innovation news"
])
print(impact)
```

### 4. Context-Aware Trending Analysis

Analyze trends with global context awareness:

```python
def analyze_trends_with_context(social_posts: list[str]):
    response = requests.post(
        "http://sentiment-agent:8004/api/v1/analyze",
        json={
            "texts": social_posts,
            "include_context": True
        }
    )

    data = response.json()

    # Correlate sentiment with context
    positive_posts = [r for r in data["results"] if r["sentiment"] == "positive"]
    context_events = data["context"]["global_events"]

    return {
        "trend_sentiment": data["summary"]["overall"],
        "positive_ratio": len(positive_posts) / len(social_posts),
        "relevant_context": len(context_events),
        "context_alignment": _calculate_alignment(positive_posts, context_events)
    }

def _calculate_alignment(posts, events):
    # Simple alignment calculation
    positive_events = [e for e in events if e["sentiment"] == "positive"]
    return len(positive_events) / len(events) if events else 0

# Example
trends = analyze_trends_with_context([
    "Love the AI theme!",
    "So timely with current events",
    "Amazing performance all around"
])
print(trends)
```

## Best Practices

### 1. Cache Management

- Context is cached for 300 seconds (5 minutes) by default
- Use `refresh=true` when you need fresh data
- Check `cache_age_seconds` in metadata to determine staleness

```python
def get_fresh_context():
    response = requests.get(
        "http://sentiment-agent:8004/api/v1/context?refresh=true"
    )
    return response.json()
```

### 2. Category Filtering

- Specify categories to reduce noise and improve relevance
- Use categories that match your domain or content

```python
# Good: Specific categories
response = requests.get(
    "http://sentiment-agent:8004/api/v1/context?category=technology"
)

# Avoid: Getting all categories if you only need one
# response = requests.get("http://sentiment-agent:8004/api/v1/context")
```

### 3. Error Handling

Always handle potential connection issues:

```python
import requests
from requests.exceptions import RequestException

def safe_context_call():
    try:
        response = requests.get(
            "http://sentiment-agent:8004/api/v1/context",
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Error fetching context: {e}")
        return {"events": [], "error": str(e)}
```

### 4. Performance Optimization

- Use batch endpoints when processing multiple items
- Leverage context caching to reduce redundant calls
- Consider async operations for high-volume scenarios

```python
import asyncio
import aiohttp

async def analyze_batch_async(texts: list[str]):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://sentiment-agent:8004/api/v1/analyze",
            json={"texts": texts, "include_context": True}
        ) as response:
            return await response.json()

# Use for high-volume scenarios
results = await analyze_batch_async(texts)
```

## Troubleshooting

### WorldMonitor Not Connected

**Problem:** Sentiment Agent health check shows `"worldmonitor_connected": false`

**Solutions:**

1. Check WorldMonitor is running:
```bash
kubectl get pods -n live | grep worldmonitor
```

2. Check WorldMonitor logs:
```bash
kubectl logs deployment/sentiment-agent -c worldmonitor-sidecar -n live
```

3. Verify connection configuration:
```bash
kubectl exec sentiment-agent -n live -- env | grep WORLDMONITOR
```

### Context Returns Empty

**Problem:** `/api/v1/context` returns empty events array

**Solutions:**

1. Force refresh:
```bash
curl "http://sentiment-agent:8004/api/v1/context?refresh=true"
```

2. Check WorldMonitor is sending events:
```bash
# WorldMonitor logs
kubectl logs deployment/sentiment-agent -c worldmonitor-sidecar -n live | grep -i event
```

3. Verify category configuration:
```bash
# Check configured categories
kubectl exec sentiment-agent -n live -- env | grep CATEGORIES
```

### High Latency

**Problem:** Context requests are slow

**Solutions:**

1. Check if using cached data:
```python
data = requests.get("http://sentiment-agent:8004/api/v1/context/stats").json()
if data["cache_info"]["cache_age_seconds"] < 60:
    print("Using fresh cache - should be fast")
```

2. Reduce categories to filter:
```python
# Faster: Specific category
requests.get("http://sentiment-agent:8004/api/v1/context?category=technology")

# Slower: All categories
requests.get("http://sentiment-agent:8004/api/v1/context")
```

3. Check resource utilization:
```bash
kubectl top pod sentiment-agent -n live
```

### WebSocket Connection Issues

**Problem:** Context not updating in real-time

**Solutions:**

1. Check WebSocket connection in logs:
```bash
kubectl logs sentiment-agent -n live | grep -i websocket
```

2. Verify WorldMonitor WebSocket endpoint:
```bash
# Should return 101 Switching Protocols
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://worldmonitor:8010/ws
```

3. Check for network policies:
```bash
kubectl get networkpolicies -n live
```

## Related Documentation

- [Sentiment Agent with WorldMonitor](../services/sentiment-agent-with-worldmonitor.md) - Complete service documentation
- [API Reference](../reference/api.md) - Full API documentation
- [Architecture](../reference/architecture.md) - System architecture
