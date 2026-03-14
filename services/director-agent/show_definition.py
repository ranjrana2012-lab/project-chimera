"""
Show Definition Schema for Project Chimera

Defines the data models and validation for show definitions in YAML format.
Supports scenes, agent actions, timing, transitions, and audience adaptations.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import yaml


class AgentType(str, Enum):
    """Available agent types for show automation."""
    BSL = "bsl"
    CAPTIONING = "captioning"
    LIGHTING = "lighting"
    SOUND = "sound"
    MUSIC = "music"
    SENTIMENT = "sentiment"
    SCENESPEAK = "scenespeak"


class ActionType(str, Enum):
    """Types of actions that can be performed."""
    TRANSLATE = "translate"
    TRANSCRIBE = "transcribe"
    SET_LIGHTING = "set_lighting"
    PLAY_AUDIO = "play_audio"
    PLAY_MUSIC = "play_music"
    ANALYZE_SENTIMENT = "analyze_sentiment"
    GENERATE_DIALOGUE = "generate_dialogue"
    WAIT = "wait"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class Mood(str, Enum):
    """Lighting/sound mood presets."""
    DRAMATIC = "dramatic"
    CALM = "calm"
    TENSE = "tense"
    JOYFUL = "joyful"
    MYSTERIOUS = "mysterious"
    ROMANTIC = "romantic"


class AgentAction(BaseModel):
    """Base action model for agent interactions."""

    agent: AgentType
    action: ActionType
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    retry_count: int = Field(default=0, ge=0, le=5)
    continue_on_failure: bool = False

    @field_validator('parameters')
    def validate_parameters(cls, v, info):
        """Validate action parameters based on action type."""
        action_type = info.data.get('action')
        agent = info.data.get('agent')

        if action_type == ActionType.TRANSLATE and agent == AgentType.BSL:
            # BSL translation needs text
            if 'text' not in v:
                raise ValueError("BSL translate action requires 'text' parameter")

        elif action_type == ActionType.SET_LIGHTING:
            # Lighting needs scene or mood
            if 'scene' not in v and 'mood' not in v:
                raise ValueError("Lighting action requires 'scene' or 'mood' parameter")

        elif action_type == ActionType.PLAY_AUDIO:
            # Audio needs file_path
            if 'file_path' not in v:
                raise ValueError("Audio action requires 'file_path' parameter")

        elif action_type == ActionType.GENERATE_DIALOGUE:
            # Dialogue needs prompt
            if 'prompt' not in v:
                raise ValueError("Dialogue generation requires 'prompt' parameter")

        return v


class WaitAction(BaseModel):
    """Wait/delay action."""

    action: ActionType = ActionType.WAIT
    duration_ms: int = Field(..., ge=0, le=300000)
    description: Optional[str] = None


class ParallelActions(BaseModel):
    """Execute multiple actions in parallel."""

    action: ActionType = ActionType.PARALLEL
    actions: List[Union[AgentAction, 'ParallelActions', 'ConditionalAction']]
    description: Optional[str] = None
    wait_for_all: bool = True


class ConditionalAction(BaseModel):
    """Conditional execution based on audience sentiment or show state."""

    action: ActionType = ActionType.CONDITIONAL
    condition: Dict[str, Any] = Field(..., description="Condition expression")
    then_actions: List[Union[AgentAction, ParallelActions, 'ConditionalAction']]
    else_actions: Optional[List[Union[AgentAction, ParallelActions, 'ConditionalAction']]] = None
    description: Optional[str] = None


# Allow recursive models
ParallelActions.model_rebuild()
ConditionalAction.model_rebuild()


class Transition(BaseModel):
    """Scene transition configuration."""

    type: str = Field(..., description="Transition type: cut, fade, dissolve")
    duration_ms: int = Field(default=1000, ge=0, le=10000)
    lighting_transition: Optional[Dict[str, Any]] = None
    audio_fade: bool = False


class Scene(BaseModel):
    """A single scene in the show."""

    id: str = Field(..., description="Unique scene identifier")
    title: str = Field(..., description="Scene title")
    description: Optional[str] = None
    duration_ms: Optional[int] = Field(None, ge=0, description="Expected scene duration")

    # Scene actions (executed sequentially by default)
    actions: List[Union[AgentAction, WaitAction, ParallelActions, ConditionalAction]]

    # Scene metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Transition to next scene
    transition: Optional[Transition] = None

    # Audience adaptation
    adapt_to_sentiment: bool = False
    sentiment_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "positive": 0.7,
            "negative": 0.3
        }
    )


class ShowMetadata(BaseModel):
    """Show metadata and configuration."""

    title: str
    author: Optional[str] = None
    version: str = "1.0"
    description: Optional[str] = None
    estimated_duration_ms: Optional[int] = None
    tags: List[str] = Field(default_factory=list)

    # Safety settings
    require_human_approval: bool = True
    emergency_stop_enabled: bool = True
    max_scene_duration_ms: int = Field(default=600000, ge=0, description="Max 10 minutes per scene")

    # Audience adaptation settings
    enable_sentiment_adaptation: bool = False
    sentiment_check_interval_ms: int = Field(default=5000, ge=1000, le=60000)


class ShowDefinition(BaseModel):
    """Complete show definition."""

    metadata: ShowMetadata
    scenes: List[Scene]

    @field_validator('scenes')
    def validate_scenes(cls, v):
        """Validate scene sequence and references."""
        if not v:
            raise ValueError("Show must have at least one scene")

        scene_ids = [scene.id for scene in v]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique")

        return v


def load_show_definition(yaml_content: str) -> ShowDefinition:
    """
    Load show definition from YAML content.

    Args:
        yaml_content: YAML string containing show definition

    Returns:
        ShowDefinition object

    Raises:
        yaml.YAMLError: If YAML parsing fails
        ValidationError: If schema validation fails
    """
    data = yaml.safe_load(yaml_content)
    return ShowDefinition(**data)


def load_show_definition_from_file(file_path: str) -> ShowDefinition:
    """
    Load show definition from YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        ShowDefinition object
    """
    with open(file_path, 'r') as f:
        yaml_content = f.read()
    return load_show_definition(yaml_content)


def save_show_definition(show: ShowDefinition, file_path: str) -> None:
    """
    Save show definition to YAML file.

    Args:
        show: ShowDefinition to save
        file_path: Output file path
    """
    with open(file_path, 'w') as f:
        yaml.dump(show.model_dump(), f, default_flow_style=False, sort_keys=False)


__all__ = [
    "AgentType",
    "ActionType",
    "Mood",
    "AgentAction",
    "WaitAction",
    "ParallelActions",
    "ConditionalAction",
    "Transition",
    "Scene",
    "ShowMetadata",
    "ShowDefinition",
    "load_show_definition",
    "load_show_definition_from_file",
    "save_show_definition",
]
