from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from graph.models import Entity, Relationship

logger = logging.getLogger(__name__)

# Try to import neo4j, gracefully handle if not available
try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    AsyncGraphDatabase = None  # type: ignore
    logger.warning("neo4j module not available - Neo4jClient will be disabled")


class Neo4jClient:
    """Client for Neo4j graph database operations."""

    def __init__(self, uri: str, user: str, password: str):
        if not NEO4J_AVAILABLE:
            raise RuntimeError(
                "neo4j module is not available. Install it with: pip install neo4j"
            )
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        """Close the database connection."""
        await self.driver.close()

    async def create_entity(self, entity: Entity) -> None:
        """Create or update an entity node."""
        query = """
        MERGE (e:Entity {id: $entity_id})
        SET e.type = $entity_type,
            e.attributes = $attributes,
            e.valid_at = $valid_at,
            e.invalid_at = $invalid_at
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                entity_id=entity.id,
                entity_type=entity.type.value,
                attributes=entity.attributes,
                valid_at=entity.valid_at.isoformat(),
                invalid_at=entity.invalid_at.isoformat() if entity.invalid_at else None
            )
        logger.debug(f"Created entity: {entity.id}")

    async def create_relationship(self, rel: Relationship) -> None:
        """Create a relationship between entities."""
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        MERGE (source)-[r:RELATIONSHIP {type: $rel_type}]->(target)
        SET r.attributes = $attributes,
            r.valid_at = $valid_at,
            r.invalid_at = $invalid_at
        """
        async with self.driver.session() as session:
            await session.run(
                query,
                source_id=rel.source,
                target_id=rel.target,
                rel_type=rel.type.value,
                attributes=rel.attributes,
                valid_at=rel.valid_at.isoformat(),
                invalid_at=rel.invalid_at.isoformat() if rel.invalid_at else None
            )
        logger.debug(f"Created relationship: {rel.source} -> {rel.target}")

    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an entity by ID."""
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e
        """
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id)
            record = await result.single()
            if record:
                return dict(record["e"])
        return None

    async def query_related(self, entity_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Query entities related to the given entity."""
        query = """
        MATCH (e:Entity {id: $entity_id})-[*1..$depth]-(related:Entity)
        RETURN DISTINCT related
        LIMIT 100
        """
        async with self.driver.session() as session:
            result = await session.run(query, entity_id=entity_id, depth=depth)
            records = await result.data()
            return [dict(r["related"]) for r in records]

    async def clear_all(self) -> None:
        """Clear all data from the database (for testing)."""
        query = "MATCH (n) DETACH DELETE n"
        async with self.driver.session() as session:
            await session.run(query)
        logger.warning("Cleared all graph data")
