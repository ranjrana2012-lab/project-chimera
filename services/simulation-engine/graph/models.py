from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    POLICY = "policy"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    KNOWS = "knows"
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    PARTICIPATED_IN = "participated_in"
    RELATED_TO = "related_to"
    INFLUENCES = "influences"


class Entity(BaseModel):
    """Represents an entity in the knowledge graph."""
    id: str
    type: EntityType
    attributes: Dict[str, Any]
    valid_at: datetime
    invalid_at: Optional[datetime] = None


class Relationship(BaseModel):
    """Represents a relationship between entities."""
    source: str
    target: str
    type: RelationType
    attributes: Dict[str, Any]
    valid_at: datetime
    invalid_at: Optional[datetime] = None


class Fact(BaseModel):
    """Represents a temporal fact."""
    subject: str
    predicate: str
    object: str
    confidence: float
    valid_at: datetime
    invalid_at: Optional[datetime] = None
