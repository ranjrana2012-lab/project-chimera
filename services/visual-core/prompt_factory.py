"""Prompt engineering templates and factory for LTX-2 video generation"""

from typing import Dict, Any, Optional, List
from enum import Enum
from models import CameraMotion, Resolution


class VisualStyle(str, Enum):
    """Visual style templates for video generation"""
    CORPORATE_BRIEFING = "corporate_briefing"
    DOCUMENTARY = "documentary"
    SOCIAL_MEDIA = "social_media"
    NEWS_REPORT = "news_report"
    ANALYTICAL = "analytical"


PROMPT_TEMPLATES = {
    VisualStyle.CORPORATE_BRIEFING: """
Professional corporate video briefing. Clean, modern aesthetic.
Setting: Well-lit modern office or executive boardroom.
Style: Business professional, calm, authoritative.
Camera: Steady, controlled movements. Mostly static with slow dollies.
Colors: Blue, gray, white corporate palette.
Text overlays: Clean sans-serif fonts, minimal.
Mood: Confident, trustworthy, professional.
Audio: Clear, measured narration with subtle ambient music.
""",

    VisualStyle.DOCUMENTARY: """
Documentary-style visual storytelling.
Setting: Dynamic environments, real-world locations.
Style: Cinematic, observational, authentic.
Camera: Handheld feel, natural movement, environmental shots.
Colors: Naturalistic, slightly desaturated.
Text overlays: Documentary-style lower thirds.
Mood: Informative, engaging, human.
Audio: Narrator with environmental ambience.
""",

    VisualStyle.SOCIAL_MEDIA: """
Social media content visualization.
Setting: Digital interfaces, social feeds, comment threads.
Style: Fast-paced, energetic, modern.
Camera: Quick cuts, zooms, dynamic transitions.
Colors: Vibrant, platform-appropriate branding.
Text overlays: Social media UI elements, emojis.
Mood: Engaging, shareable, viral.
Audio: Upbeat, contemporary, social-friendly.
""",

    VisualStyle.NEWS_REPORT: """
Breaking news report style.
Setting: News studio, on-location reporting.
Style: Journalistic, urgent, credible.
Camera: Professional broadcast quality, static to slow movement.
Colors: News network branding (red, blue, white).
Text overlays: Breaking news banners, tickers.
Mood: Urgent, informative, authoritative.
Audio: News anchor delivery with urgency.
""",

    VisualStyle.ANALYTICAL: """
Data visualization and analysis presentation.
Setting: Abstract data environments, clean backgrounds.
Style: Precise, technical, informative.
Camera: Smooth pans across data visualizations.
Colors: Analytical palette with data-driven accent colors.
Text overlays: Charts, graphs, key metrics.
Mood: Objective, analytical, insightful.
Audio: Clear explanation with ambient underscore.
"""
}


class PromptFactory:
    """Factory for creating LTX-2 video prompts"""

    @staticmethod
    def build_prompt(
        narrative: str,
        style: VisualStyle,
        camera_motion: CameraMotion,
        duration: int,
        custom_elements: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build complete LTX-2 prompt from components.

        Args:
            narrative: The story or scene description to generate
            style: Visual style template to use (e.g., CORPORATE_BRIEFING, DOCUMENTARY)
            camera_motion: Camera movement pattern (e.g., STATIC, PAN_LEFT, DOLLY_IN)
            duration: Video duration in seconds (must be between 6 and 20)
            custom_elements: Optional dictionary of custom prompt elements to include

        Returns:
            Complete LTX-2 prompt string ready for generation

        Raises:
            ValueError: If duration is outside valid range (6-20 seconds)
        """
        # Validate duration is within LTXVideoRequest bounds
        if not 6 <= duration <= 20:
            raise ValueError(f"Duration must be between 6 and 20 seconds, got {duration}")

        # Get base style template
        style_template = PROMPT_TEMPLATES.get(style, "")

        # Build scene-specific prompt
        scene_prompt = f"""{style_template}

SCENE: {narrative}

DURATION: {duration} seconds
CAMERA: {camera_motion.value}
"""

        # Add custom elements if provided
        if custom_elements:
            for key, value in custom_elements.items():
                scene_prompt += f"{key.upper()}: {value}\n"

        return scene_prompt.strip()

    @staticmethod
    def enhance_prompt_for_video(
        base_prompt: str,
        video_context: Dict[str, Any]
    ) -> str:
        """Enhance prompt with video-specific context.

        Args:
            base_prompt: The base prompt to enhance
            video_context: Dictionary containing video generation parameters:
                - resolution: Video resolution (e.g., "1920x1080", "3840x2160")
                - generate_audio: Whether to generate synchronized audio
                - camera_motion: Camera movement pattern
                - previous_scene: Description of previous scene for continuity

        Returns:
            Enhanced prompt string with technical specifications
        """
        enhancements = []

        # Add resolution context using Resolution enum for type safety
        if video_context.get("resolution") in [Resolution.FOUR_K.value, Resolution.UHD.value]:
            enhancements.append("4K ultra-high definition, maximum detail")

        # Add audio context
        if video_context.get("generate_audio"):
            enhancements.append("Synchronized audio included - visuals and audio must match perfectly")

        # Add motion context
        if video_context.get("camera_motion"):
            enhancements.append(f"Camera movement: {video_context['camera_motion']}")

        # Add continuity context
        if video_context.get("previous_scene"):
            enhancements.append(f"Continuity from previous scene: {video_context['previous_scene']}")

        if enhancements:
            return f"{base_prompt}\n\nTECHNICAL: {'; '.join(enhancements)}."

        return base_prompt

    @staticmethod
    def create_briefing_prompt(
        topic: str,
        sentiment_summary: str,
        key_insights: List[str],
        duration: int
    ) -> str:
        """Create prompt for executive briefing video.

        Args:
            topic: The main topic or subject of the briefing
            sentiment_summary: Summary of sentiment analysis results
            key_insights: List of key insights to present
            duration: Video duration in seconds (must be between 6 and 20)

        Returns:
            Complete prompt string formatted for executive briefing video

        Raises:
            ValueError: If duration is outside valid range (6-20 seconds)
        """
        # Validate duration
        if not 6 <= duration <= 20:
            raise ValueError(f"Duration must be between 6 and 20 seconds, got {duration}")

        insights_text = "\n".join([f"- {insight}" for insight in key_insights])

        prompt = f"""{PROMPT_TEMPLATES[VisualStyle.CORPORATE_BRIEFING]}

EXECUTIVE BRIEFING: {topic}

SENTIMENT ANALYSIS:
{sentiment_summary}

KEY INSIGHTS:
{insights_text}

DURATION: {duration} seconds

This is an executive briefing video. Maintain professional, authoritative tone throughout.
Focus on clarity, data-driven insights, and actionable recommendations.
"""

        return prompt.strip()