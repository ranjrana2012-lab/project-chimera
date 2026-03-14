"""Educational Platform Service Integrations.

Integration layer for connecting with existing Project Chimera agents:
- BSL Agent for sign language content
- Captioning Agent for transcription
- Sentiment Agent for engagement analysis
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import settings
from models import (
    AccessibilityNeeds, StudentProfile, LearningSession,
    ContentRecommendation, ContentType
)

logger = logging.getLogger(__name__)


class BSLAgentIntegration:
    """Integration with BSL Agent for sign language content."""

    def __init__(self, base_url: str = None):
        """Initialize BSL agent integration."""
        self.base_url = base_url or settings.bsl_agent_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.available_animations = self._get_available_animations()

    async def _get_available_animations(self) -> List[str]:
        """Get list of available BSL animations."""
        try:
            response = await self.client.get(f"{self.base_url}/health/ready")
            if response.status_code == 200:
                # BSL agent has 107+ animations
                return [
                    # Common phrases
                    "hello", "good_morning", "please", "thank_you", "sorry",
                    "yes", "no", "how_are_you", "what_is_your_name", "my_name_is",
                    "i_understand", "i_dont_understand", "look", "listen",
                    "welcome", "goodbye", "good_evening", "good_night", "excuse_me",
                    "help", "stop", "wait",

                    # Alphabet (A-Z)
                    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
                    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",

                    # Numbers
                    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",

                    # Emotions
                    "happy", "sad", "angry", "surprised", "scared", "confused",
                    "excited", "bored", "tired", "worried"
                ]
        except Exception as e:
            logger.warning(f"Failed to get available animations: {e}")
            return []

    async def translate_text_to_bsl(self, text: str, include_nmm: bool = True) -> Optional[Dict[str, Any]]:
        """
        Translate text to BSL gloss notation.

        Args:
            text: English text to translate
            include_nmm: Include non-manual markers (facial expressions)

        Returns:
            Translation result with gloss and metadata
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/translate",
                json={
                    "text": text,
                    "include_nmm": include_nmm
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"BSL translation failed: {e}")
            return None

    async def generate_bsl_animation(
        self,
        gloss: str,
        session_id: str,
        include_nmm: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate BSL animation data for educational content.

        Args:
            gloss: BSL gloss notation
            session_id: Student session ID
            include_nmm: Include non-manual markers

        Returns:
            Animation data for avatar rendering
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/avatar/generate",
                json={
                    "gloss": gloss,
                    "session_id": session_id,
                    "include_nmm": include_nmm
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"BSL animation generation failed: {e}")
            return None

    async def get_avatar_info(self) -> Optional[Dict[str, Any]]:
        """Get BSL avatar renderer information."""
        try:
            response = await self.client.get(f"{self.base_url}/api/avatar/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get avatar info: {e}")
            return None

    async def set_facial_expression(self, expression: str, intensity: float = 1.0) -> bool:
        """
        Set avatar facial expression for educational content.

        Args:
            expression: Expression name (happy, sad, surprised, etc.)
            intensity: Intensity 0.0-1.0

        Returns:
            Success status
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/avatar/expression",
                json={
                    "expression": expression,
                    "intensity": intensity
                }
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except Exception as e:
            logger.error(f"Failed to set facial expression: {e}")
            return False

    async def text_to_bsl_animation(self, text: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Complete pipeline: text -> translation -> animation.

        Args:
            text: English text to convert
            session_id: Student session ID

        Returns:
            Animation data or None
        """
        # First translate to BSL gloss
        translation = await self.translate_text_to_bsl(text)
        if not translation:
            return None

        # Then generate animation
        animation = await self.generate_bsl_animation(
            gloss=translation["gloss"],
            session_id=session_id,
            include_nmm=True
        )

        return animation

    def is_animation_available(self, text: str) -> bool:
        """Check if BSL animation is available for given text."""
        # Simple check - in production would be more sophisticated
        text_lower = text.lower().strip()
        return text_lower in self.available_animations

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class CaptioningAgentIntegration:
    """Integration with Captioning Agent for transcription."""

    def __init__(self, base_url: str = None):
        """Initialize captioning agent integration."""
        self.base_url = base_url or settings.captioning_agent_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Transcribe audio to text for educational content.

        Args:
            audio_data: Audio file data
            language: Language code

        Returns:
            Transcription result with text, confidence, and timing
        """
        try:
            files = {"audio": ("audio.wav", audio_data, "audio/wav")}
            data = {"language": language}

            response = await self.client.post(
                f"{self.base_url}/api/v1/transcribe",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return None

    async def detect_language(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect language of educational content.

        Args:
            text: Text to analyze

        Returns:
            Language detection result
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/detect-language",
                json={"text": text}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None

    async def create_captioning_session(self, session_id: str) -> Optional[str]:
        """
        Create a WebSocket session for real-time captioning.

        Args:
            session_id: Unique session identifier

        Returns:
            WebSocket URL or None
        """
        # Return WebSocket URL for real-time captioning
        return f"ws://{self.base_url.replace('http://', '')}/api/v1/stream?session={session_id}"

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class SentimentAgentIntegration:
    """Integration with Sentiment Agent for engagement analysis."""

    def __init__(self, base_url: str = None):
        """Initialize sentiment agent integration."""
        self.base_url = base_url or settings.sentiment_agent_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of student feedback or responses.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result with score and label
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/analyze",
                json={"text": text}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return None

    async def analyze_batch_sentiment(self, texts: List[str]) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            Batch sentiment analysis results
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/analyze-batch",
                json={"texts": texts}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Batch sentiment analysis failed: {e}")
            return None

    async def get_sentiment_trend(self, window: str = "5m") -> Optional[Dict[str, Any]]:
        """
        Get sentiment trend over time for classroom monitoring.

        Args:
            window: Time window (1m, 5m, 15m, 1h)

        Returns:
            Sentiment trend data
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/trend",
                params={"window": window}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get sentiment trend: {e}")
            return None

    async def get_emotion_aggregates(self) -> Optional[Dict[str, Any]]:
        """
        Get aggregated emotion breakdown for classroom.

        Returns:
            Emotion aggregate data
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/emotions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get emotion aggregates: {e}")
            return None

    async def analyze_student_engagement(
        self,
        session: LearningSession
    ) -> Dict[str, float]:
        """
        Analyze student engagement from session data.

        Args:
            session: Learning session with interaction events

        Returns:
            Engagement metrics
        """
        try:
            # Analyze sentiment from interaction events
            if session.interaction_events:
                texts = [
                    event.get("text", "")
                    for event in session.interaction_events
                    if event.get("text")
                ]

                if texts:
                    batch_result = await self.analyze_batch_sentiment(texts)
                    if batch_result and batch_result.get("results"):
                        # Calculate average sentiment
                        sentiments = [r.get("score", 0) for r in batch_result["results"]]
                        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

                        return {
                            "sentiment_score": avg_sentiment,
                            "engagement_score": session.engagement_score,
                            "frustration_level": self._calculate_frustration(batch_result["results"])
                        }
            return {
                "sentiment_score": 0.0,
                "engagement_score": session.engagement_score,
                "frustration_level": 0.0
            }
        except Exception as e:
            logger.error(f"Failed to analyze student engagement: {e}")
            return {
                "sentiment_score": 0.0,
                "engagement_score": 0.5,
                "frustration_level": 0.0
            }

    def _calculate_frustration(self, sentiment_results: List[Dict]) -> float:
        """Calculate frustration level from sentiment results."""
        if not sentiment_results:
            return 0.0

        negative_count = sum(1 for r in sentiment_results if r.get("label") == "negative")
        return negative_count / len(sentiment_results)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class EducationalContentIntegrator:
    """Main integrator for educational content with accessibility features."""

    def __init__(self):
        """Initialize all integrations."""
        self.bsl = BSLAgentIntegration()
        self.captioning = CaptioningAgentIntegration()
        self.sentiment = SentimentAgentIntegration()

    async def enhance_content_with_accessibility(
        self,
        content: str,
        student: StudentProfile,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Enhance educational content with accessibility features.

        Args:
            content: Original educational content
            student: Student profile with accessibility needs
            session_id: Learning session ID

        Returns:
            Enhanced content with accessibility features
        """
        enhanced = {
            "original_content": content,
            "accessibility_features": []
        }

        # Add BSL if needed
        if student.accessibility_needs.requires_bsl:
            bsl_animation = await self.bsl.text_to_bsl_animation(content, session_id)
            if bsl_animation:
                enhanced["bsl_animation"] = bsl_animation
                enhanced["accessibility_features"].append("bsl")

        # Add captions if needed (or if enabled by default)
        if student.accessibility_needs.requires_captions:
            # In real implementation, would generate captions
            enhanced["captions_available"] = True
            enhanced["accessibility_features"].append("captions")

        return enhanced

    async def generate_personalized_recommendations(
        self,
        student: StudentProfile,
        recent_sessions: List[LearningSession]
    ) -> List[ContentRecommendation]:
        """
        Generate personalized content recommendations.

        Args:
            student: Student profile
            recent_sessions: Recent learning sessions

        Returns:
            List of personalized recommendations
        """
        recommendations = []

        # Analyze engagement and sentiment
        if recent_sessions:
            engagement_scores = [s.engagement_score for s in recent_sessions]
            avg_engagement = sum(engagement_scores) / len(engagement_scores)

            # Analyze sentiment from sessions
            all_sentiments = []
            for session in recent_sessions:
                engagement_data = await self.sentiment.analyze_student_engagement(session)
                all_sentiments.append(engagement_data.get("sentiment_score", 0))

            avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0

            # Generate recommendation based on engagement
            if avg_engagement < 0.4:
                # Low engagement - recommend interactive content
                recommendations.append(ContentRecommendation(
                    student_id=student.id,
                    reason="Low engagement detected - recommend interactive content",
                    confidence_score=0.7,
                    based_on_data=["engagement_scores"],
                    recommended_content_types=[ContentType.INTERACTIVE, ContentType.VIDEO],
                    accessibility_match=True,
                    alternative_formats_available=True
                ))
            elif avg_engagement > 0.7:
                # High engagement - recommend advanced content
                recommendations.append(ContentRecommendation(
                    student_id=student.id,
                    reason="High engagement - ready for more challenging content",
                    confidence_score=0.8,
                    based_on_data=["engagement_scores", "performance"],
                    recommended_content_types=[ContentType.ASSESSMENT, ContentType.PROJECT],
                    accessibility_match=True,
                    alternative_formats_available=True
                ))

        return recommendations

    async def monitor_classroom_sentiment(self, course_id: str) -> Dict[str, Any]:
        """
        Monitor overall classroom sentiment for educators.

        Args:
            course_id: Course identifier

        Returns:
            Classroom sentiment overview
        """
        try:
            # Get sentiment trend
            trend = await self.sentiment.get_sentiment_trend(window="15m")

            # Get emotion aggregates
            emotions = await self.sentiment.get_emotion_aggregates()

            return {
                "course_id": course_id,
                "sentiment_trend": trend,
                "emotion_breakdown": emotions,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to monitor classroom sentiment: {e}")
            return {
                "course_id": course_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def close_all(self):
        """Close all integration clients."""
        await self.bsl.close()
        await self.captioning.close()
        await self.sentiment.close()


# Global integrator instance
_integrator_instance = None

def get_content_integrator() -> EducationalContentIntegrator:
    """Get global content integrator instance."""
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = EducationalContentIntegrator()
    return _integrator_instance
