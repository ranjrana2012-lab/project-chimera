"""Tests for prompt factory"""

from prompt_factory import PromptFactory, VisualStyle, CameraMotion
import pytest


def test_build_prompt_corporate():
    """Test building corporate briefing prompt"""

    prompt = PromptFactory.build_prompt(
        narrative="Market analysis showing growth",
        style=VisualStyle.CORPORATE_BRIEFING,
        camera_motion=CameraMotion.DOLLY_IN,
        duration=15
    )

    assert "corporate" in prompt.lower()
    assert "dolly_in" in prompt.lower()
    assert "15 seconds" in prompt
    assert "Market analysis showing growth" in prompt


def test_enhance_prompt_with_resolution():
    """Test prompt enhancement for 4K resolution"""

    base = "Test prompt"
    enhanced = PromptFactory.enhance_prompt_for_video(
        base,
        {"resolution": "3840x2160", "generate_audio": True}
    )

    assert "4K" in enhanced
    assert "ultra-high definition" in enhanced
    assert "Synchronized audio" in enhanced


def test_create_briefing_prompt():
    """Test creating executive briefing prompt"""

    prompt = PromptFactory.create_briefing_prompt(
        topic="Acme Corp Q3 Performance",
        sentiment_summary="Overall sentiment is positive with 75% favorable mentions",
        key_insights=["Revenue up 15%", "Market share expanded"],
        duration=15
    )

    assert "EXECUTIVE BRIEFING: Acme Corp Q3 Performance" in prompt
    assert "Revenue up 15%" in prompt
    assert "15 seconds" in prompt
    assert "Overall sentiment is positive" in prompt


def test_build_prompt_documentary():
    """Test building documentary style prompt"""

    prompt = PromptFactory.build_prompt(
        narrative="Environmental conservation efforts",
        style=VisualStyle.DOCUMENTARY,
        camera_motion=CameraMotion.STATIC,
        duration=20
    )

    assert "documentary" in prompt.lower()
    assert "cinematic" in prompt.lower()
    assert "Environmental conservation efforts" in prompt
    assert "20 seconds" in prompt


def test_build_prompt_social_media():
    """Test building social media style prompt"""

    prompt = PromptFactory.build_prompt(
        narrative="Viral product launch announcement",
        style=VisualStyle.SOCIAL_MEDIA,
        camera_motion=CameraMotion.DOLLY_IN,
        duration=8
    )

    assert "social media" in prompt.lower()
    assert "vibrant" in prompt.lower()
    assert "Viral product launch announcement" in prompt
    assert "dolly_in" in prompt.lower()


def test_build_prompt_news_report():
    """Test building news report style prompt"""

    prompt = PromptFactory.build_prompt(
        narrative="Breaking market update",
        style=VisualStyle.NEWS_REPORT,
        camera_motion=CameraMotion.STATIC,
        duration=12
    )

    assert "news report" in prompt.lower()
    assert "journalistic" in prompt.lower()
    assert "Breaking market update" in prompt
    assert "12 seconds" in prompt


def test_build_prompt_analytical():
    """Test building analytical style prompt"""

    prompt = PromptFactory.build_prompt(
        narrative="Quarterly performance metrics",
        style=VisualStyle.ANALYTICAL,
        camera_motion=CameraMotion.PAN_RIGHT,
        duration=18
    )

    assert "analytical" in prompt.lower()
    assert "data visualization" in prompt.lower()
    assert "Quarterly performance metrics" in prompt
    assert "pan_right" in prompt.lower()


def test_enhance_prompt_with_camera_motion():
    """Test prompt enhancement with camera motion"""

    base = "Test prompt"
    enhanced = PromptFactory.enhance_prompt_for_video(
        base,
        {"camera_motion": "dolly_in", "generate_audio": False}
    )

    assert "Camera movement: dolly_in" in enhanced
    assert "Synchronized audio" not in enhanced


def test_enhance_prompt_with_continuity():
    """Test prompt enhancement with scene continuity"""

    base = "Test prompt"
    enhanced = PromptFactory.enhance_prompt_for_video(
        base,
        {"previous_scene": "Executive office introduction"}
    )

    assert "Continuity from previous scene" in enhanced
    assert "Executive office introduction" in enhanced


def test_enhance_prompt_no_enhancements():
    """Test prompt enhancement with no enhancements"""

    base = "Test prompt"
    enhanced = PromptFactory.enhance_prompt_for_video(
        base,
        {}
    )

    assert enhanced == base


def test_build_prompt_with_custom_elements():
    """Test building prompt with custom elements"""

    prompt = PromptFactory.build_prompt(
        narrative="Custom narrative",
        style=VisualStyle.CORPORATE_BRIEFING,
        camera_motion=CameraMotion.STATIC,
        duration=10,
        custom_elements={
            "brand_colors": "blue and gold",
            "logo_position": "top right",
            "music_style": "inspirational"
        }
    )

    assert "BRAND_COLORS: blue and gold" in prompt
    assert "LOGO_POSITION: top right" in prompt
    assert "MUSIC_STYLE: inspirational" in prompt


def test_camera_motion_enum():
    """Test camera motion enum values"""

    assert CameraMotion.STATIC == "static"
    assert CameraMotion.PAN_LEFT == "pan_left"
    assert CameraMotion.PAN_RIGHT == "pan_right"
    assert CameraMotion.DOLLY_IN == "dolly_in"
    assert CameraMotion.DOLLY_OUT == "dolly_out"
    assert CameraMotion.TRACK_LEFT == "track_left"
    assert CameraMotion.TRACK_RIGHT == "track_right"


def test_visual_style_enum():
    """Test visual style enum values"""

    assert VisualStyle.CORPORATE_BRIEFING == "corporate_briefing"
    assert VisualStyle.DOCUMENTARY == "documentary"
    assert VisualStyle.SOCIAL_MEDIA == "social_media"
    assert VisualStyle.NEWS_REPORT == "news_report"
    assert VisualStyle.ANALYTICAL == "analytical"


def test_create_briefing_prompt_multiple_insights():
    """Test briefing prompt with multiple insights"""

    prompt = PromptFactory.create_briefing_prompt(
        topic="Annual Results",
        sentiment_summary="Strong positive sentiment",
        key_insights=[
            "Revenue increased by 25%",
            "Customer satisfaction at 94%",
            "Market position strengthened",
            "New product line launched"
        ],
        duration=20
    )

    assert "Revenue increased by 25%" in prompt
    assert "Customer satisfaction at 94%" in prompt
    assert "Market position strengthened" in prompt
    assert "New product line launched" in prompt
    assert "20 seconds" in prompt


def test_prompt_factory_class_methods():
    """Test that PromptFactory has all required methods"""

    assert hasattr(PromptFactory, 'build_prompt')
    assert hasattr(PromptFactory, 'enhance_prompt_for_video')
    assert hasattr(PromptFactory, 'create_briefing_prompt')
    assert callable(getattr(PromptFactory, 'build_prompt'))
    assert callable(getattr(PromptFactory, 'enhance_prompt_for_video'))
    assert callable(getattr(PromptFactory, 'create_briefing_prompt'))


def test_prompt_templates_exist():
    """Test that all visual style templates exist"""

    from prompt_factory import PROMPT_TEMPLATES

    assert VisualStyle.CORPORATE_BRIEFING in PROMPT_TEMPLATES
    assert VisualStyle.DOCUMENTARY in PROMPT_TEMPLATES
    assert VisualStyle.SOCIAL_MEDIA in PROMPT_TEMPLATES
    assert VisualStyle.NEWS_REPORT in PROMPT_TEMPLATES
    assert VisualStyle.ANALYTICAL in PROMPT_TEMPLATES

    # Verify templates are not empty
    for style, template in PROMPT_TEMPLATES.items():
        assert len(template) > 0, f"Template for {style} is empty"
        assert "Style:" in template or "Setting:" in template


def test_build_prompt_duration_validation():
    """Test that build_prompt validates duration bounds"""

    # Test duration too low
    with pytest.raises(ValueError, match="Duration must be between 6 and 20 seconds"):
        PromptFactory.build_prompt(
            narrative="Test narrative",
            style=VisualStyle.CORPORATE_BRIEFING,
            camera_motion=CameraMotion.STATIC,
            duration=5
        )

    # Test duration too high
    with pytest.raises(ValueError, match="Duration must be between 6 and 20 seconds"):
        PromptFactory.build_prompt(
            narrative="Test narrative",
            style=VisualStyle.CORPORATE_BRIEFING,
            camera_motion=CameraMotion.STATIC,
            duration=21
        )

    # Test boundary values - these should work
    PromptFactory.build_prompt(
        narrative="Test narrative",
        style=VisualStyle.CORPORATE_BRIEFING,
        camera_motion=CameraMotion.STATIC,
        duration=6
    )

    PromptFactory.build_prompt(
        narrative="Test narrative",
        style=VisualStyle.CORPORATE_BRIEFING,
        camera_motion=CameraMotion.STATIC,
        duration=20
    )


def test_create_briefing_prompt_duration_validation():
    """Test that create_briefing_prompt validates duration bounds"""

    # Test duration too low
    with pytest.raises(ValueError, match="Duration must be between 6 and 20 seconds"):
        PromptFactory.create_briefing_prompt(
            topic="Test Topic",
            sentiment_summary="Test sentiment",
            key_insights=["Insight 1"],
            duration=5
        )

    # Test duration too high
    with pytest.raises(ValueError, match="Duration must be between 6 and 20 seconds"):
        PromptFactory.create_briefing_prompt(
            topic="Test Topic",
            sentiment_summary="Test sentiment",
            key_insights=["Insight 1"],
            duration=25
        )