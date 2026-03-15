from typing import List, Dict, Any
import logging
from datetime import datetime

from graph.models import Entity, Relationship, EntityType
from graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds knowledge graph from seed documents using GraphRAG-inspired extraction."""

    def __init__(self, client: Neo4jClient):
        self.client = client

    async def build_from_documents(self, documents: List[str]) -> Dict[str, int]:
        """Extract entities and relationships from documents."""
        entity_count = 0
        relationship_count = 0

        for doc_id, document in enumerate(documents):
            logger.info(f"Processing document {doc_id + 1}/{len(documents)}")

            entities = await self._extract_entities_simple(document)
            relationships = await self._extract_relationships_simple(entities)

            for entity in entities:
                await self.client.create_entity(entity)
                entity_count += 1

            for rel in relationships:
                await self.client.create_relationship(rel)
                relationship_count += 1

        return {"entities": entity_count, "relationships": relationship_count}

    async def _extract_entities_simple(self, document: str) -> List[Entity]:
        """Simple entity extraction for Phase 0."""
        import re

        entities = []
        now = datetime.utcnow()

        words = re.findall(r'\b[A-Z][a-z]+\b', document)
        unique_words = list(set(words[:20]))

        for i, word in enumerate(unique_words):
            entities.append(Entity(
                id=f"entity_{i}",
                type=EntityType.CONCEPT,
                attributes={"name": word, "source": "simple_extraction"},
                valid_at=now
            ))

        return entities

    async def _extract_relationships_simple(self, entities: List[Entity]) -> List[Relationship]:
        """Simple relationship extraction for Phase 0."""
        relationships = []
        now = datetime.utcnow()

        for i in range(len(entities) - 1):
            relationships.append(Relationship(
                source=entities[i].id,
                target=entities[i + 1].id,
                type="related_to",
                attributes={"source": "simple_extraction"},
                valid_at=now
            ))

        return relationships
