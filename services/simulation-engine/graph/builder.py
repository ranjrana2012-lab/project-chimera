from typing import List, Dict, Any
import logging
from datetime import datetime, timezone

from graph.models import Entity, Relationship, EntityType
from graph.llm_extractor import LLMExtractor

logger = logging.getLogger(__name__)

# Neo4j client import - may fail if neo4j not installed
try:
    from graph.neo4j_client import Neo4jClient
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    Neo4jClient = None  # type: ignore
    logger.warning("Neo4j client not available - GraphBuilder will work in limited mode")


class GraphBuilder:
    """Builds knowledge graph from seed documents using GraphRAG-inspired extraction."""

    def __init__(self, client: Any, use_llm_extraction: bool = True):
        """
        Initialize the graph builder.

        Args:
            client: Neo4j client for graph storage (or mock for testing)
            use_llm_extraction: Whether to use LLM-based extraction (default: True)
        """
        if not NEO4J_AVAILABLE and client is not None:
            logger.warning("Neo4j not available - GraphBuilder running in limited mode")

        self.client = client
        self.use_llm_extraction = use_llm_extraction
        self.llm_extractor = LLMExtractor() if use_llm_extraction else None

    async def build_from_documents(self, documents: List[str]) -> Dict[str, int]:
        """Extract entities and relationships from documents."""
        entity_count = 0
        relationship_count = 0

        for doc_id, document in enumerate(documents):
            logger.info(f"Processing document {doc_id + 1}/{len(documents)}")

            # Use LLM-based extraction if enabled, otherwise use simple extraction
            if self.use_llm_extraction and self.llm_extractor:
                entities = await self._extract_entities_llm(document)
                relationships = await self._extract_relationships_llm(entities)
            else:
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
        now = datetime.now(timezone.utc)

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
        now = datetime.now(timezone.utc)

        for i in range(len(entities) - 1):
            relationships.append(Relationship(
                source=entities[i].id,
                target=entities[i + 1].id,
                type="related_to",
                attributes={"source": "simple_extraction"},
                valid_at=now
            ))

        return relationships

    async def _extract_entities_llm(self, document: str) -> List[Entity]:
        """
        LLM-based entity extraction with fallback to simple extraction.

        Args:
            document: Text document to extract entities from

        Returns:
            List of extracted Entity objects
        """
        try:
            if self.llm_extractor:
                entities = await self.llm_extractor.extract_entities(document)
                if entities:
                    logger.info(f"LLM extracted {len(entities)} entities")
                    return entities
                else:
                    logger.warning("LLM extraction returned no entities, using fallback")
                    return await self._extract_entities_simple(document)
            else:
                return await self._extract_entities_simple(document)
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}, falling back to simple extraction")
            return await self._extract_entities_simple(document)

    async def _extract_relationships_llm(self, entities: List[Entity]) -> List[Relationship]:
        """
        Extract relationships between entities using context from entities.

        For Phase 1, this is a simplified version that creates basic relationships.
        Future phases will use LLM for more sophisticated relationship extraction.

        Args:
            entities: List of entities to create relationships between

        Returns:
            List of Relationship objects
        """
        relationships = []
        now = datetime.now(timezone.utc)

        # Create simple sequential relationships
        # In future phases, this will be enhanced with LLM-based relationship extraction
        for i in range(len(entities) - 1):
            relationships.append(Relationship(
                source=entities[i].id,
                target=entities[i + 1].id,
                type="related_to",
                attributes={"source": "llm_extraction"},
                valid_at=now
            ))

        logger.info(f"Created {len(relationships)} basic relationships")
        return relationships
