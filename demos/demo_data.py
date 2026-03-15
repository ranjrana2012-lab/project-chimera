"""Demo data for Visual Intelligence Reports"""

DEMO_SCENARIOS = {
    "tech_brand_sentiment": {
        "topic": "TechGiant Inc. Q1 Brand Sentiment Analysis",
        "timeframe": "30d",
        "style": "corporate_briefing",
        "duration": 90,
        "description": "Executive briefing on TechGiant brand sentiment"
    },
    "market_trend_analysis": {
        "topic": "AI Chip Market Trends - Q1 2026",
        "timeframe": "90d",
        "style": "analytical",
        "duration": 120,
        "description": "Comprehensive market trend analysis video"
    }
}


DEMO_SENTIMENT_DATA = {
    "tech_brand_sentiment": {
        "overall_sentiment": 0.72,
        "sentiment_trend": "improving",
        "mention_count": 5420,
        "sentiment_distribution": {
            "positive": 0.58,
            "neutral": 0.31,
            "negative": 0.11
        },
        "key_insights": [
            "22% increase in positive sentiment YoY",
            "Strong engagement on product announcement posts",
            "Influencer mentions driving positive sentiment",
            "Low negative sentiment compared to competitors"
        ],
        "trend_analysis": {
            "direction": "improving",
            "velocity": 0.08,
            "inflection_points": [
                "Product launch - March 15",
                "CEO interview - March 22"
            ]
        }
    }
}
