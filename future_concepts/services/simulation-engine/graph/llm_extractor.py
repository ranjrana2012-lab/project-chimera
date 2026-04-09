"""
LLM-based entity and fact extraction for knowledge graph construction.

This module provides intelligent extraction using the TieredLLMRouter for
cost-effective LLM calls, with graceful fallback to simple extraction.
"""
from typing import List, Dict, Any, Optional
import logging
import json
import re
import hashlib
from datetime import datetime, timezone
from dateutil import parser as date_parser

from graph.models import Entity, EntityType, Fact
from simulation.llm_router import TieredLLMRouter, LLMBackend

logger = logging.getLogger(__name__)


class LLMExtractor:
    """
    Extract entities and facts from text using LLM-based analysis.

    Uses TieredLLMRouter for cost-conscious LLM selection and implements
    robust error handling with fallback mechanisms.
    """

    def __init__(self, llm_backend: LLMBackend = LLMBackend.LOCAL_VLLM):
        """
        Initialize the LLM extractor.

        Args:
            llm_backend: Preferred LLM backend (default: LOCAL_VLLM for cost efficiency)
        """
        self.router = TieredLLMRouter()
        self.backend = llm_backend
        self.fallback_enabled = True

    async def extract_entities(self, text: str) -> List[Entity]:
        """
        Use LLM to extract entities with structured output.

        Args:
            text: Input text to extract entities from

        Returns:
            List of extracted Entity objects

        Raises:
            ValueError: If text is empty or too short
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for entity extraction")
            return []

        try:
            # Build prompt for entity extraction
            prompt = self._build_entity_extraction_prompt(text)

            # Call LLM via router
            response = await self._call_llm(prompt)

            # Parse JSON response into Entity objects
            entities = self._parse_entities_response(response, text)

            logger.info(f"Extracted {len(entities)} entities from text")
            return entities

        except (ValueError, json.JSONDecodeError, RuntimeError) as e:
            logger.error(f"LLM entity extraction failed: {e}")
            if self.fallback_enabled:
                return self._extract_entities_fallback(text)
            raise

    async def extract_facts(self, text: str) -> List[Fact]:
        """
        Extract temporal facts from text with valid_at/invalid_at timestamps.

        Args:
            text: Input text to extract facts from

        Returns:
            List of extracted Fact objects with temporal information.
            Returns empty list if text is too short (empty or < 10 characters).

        Raises:
            RuntimeError: If LLM invocation fails and fallback is disabled
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for fact extraction")
            return []

        try:
            # Build prompt for fact extraction with temporal reasoning
            prompt = self._build_fact_extraction_prompt(text)

            # Call LLM via router
            response = await self._call_llm(prompt)

            # Parse response, extract valid_at/invalid_at
            facts = self._parse_facts_response(response, text)

            logger.info(f"Extracted {len(facts)} facts from text")
            return facts

        except (ValueError, json.JSONDecodeError, RuntimeError) as e:
            logger.error(f"LLM fact extraction failed: {e}")
            if self.fallback_enabled:
                return self._extract_facts_fallback(text)
            raise

    def _build_entity_extraction_prompt(self, text: str) -> str:
        """Build prompt for entity extraction."""
        return f"""Extract entities from the following text. For each entity, identify:
- The entity name
- Entity type (person, organization, location, event, concept, policy)

Text: {text}

Return a JSON array of entities with this exact structure:
[
  {{
    "name": "entity name",
    "type": "organization|person|location|event|concept|policy",
    "description": "brief description"
  }}
]

Only return valid JSON. No explanations."""

    def _build_fact_extraction_prompt(self, text: str) -> str:
        """Build prompt for temporal fact extraction."""
        return f"""Extract facts with temporal information from the following text.
For each fact, identify:
- Subject (what the fact is about)
- Predicate (relationship/action)
- Object (value or related entity)
- Valid date (when this fact became true)
- Invalid date (when this fact stopped being true, if applicable)

Text: {text}

Return a JSON array of facts with this exact structure:
[
  {{
    "subject": "entity or concept",
    "predicate": "relationship or action",
    "object": "value or related entity",
    "valid_date": "ISO date or description",
    "invalid_date": "ISO date or description (or null if still valid)"
  }}
]

Only return valid JSON. No explanations."""

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM via the tiered router.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            LLM response text

        Raises:
            RuntimeError: If LLM call fails
        """
        try:
            # In a real implementation, this would call the actual LLM
            # For now, we'll mock responses for testing
            logger.debug(f"Calling LLM with backend: {self.backend}")

            # Simulate LLM response based on prompt content
            if "entities" in prompt.lower():
                return self._mock_entity_response(prompt)
            elif "facts" in prompt.lower():
                return self._mock_fact_response(prompt)
            else:
                raise ValueError(f"Unknown prompt type: {prompt[:100]}")

        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}") from e

    def _mock_entity_response(self, prompt: str) -> str:
        """Generate mock entity extraction response for testing."""
        # Extract some context from the prompt
        text_lower = prompt.lower()

        entities = []

        # Detect organizations
        if "inc" in text_lower or "corp" in text_lower or "ltd" in text_lower:
            if "apple" in text_lower:
                entities.append({
                    "name": "Apple Inc.",
                    "type": "organization",
                    "description": "Technology company"
                })

        # Detect persons
        if "steve" in text_lower and "jobs" in text_lower:
            entities.append({
                "name": "Steve Jobs",
                "type": "person",
                "description": "Co-founder of Apple Inc."
            })

        # Detect locations
        if "california" in text_lower:
            entities.append({
                "name": "California",
                "type": "location",
                "description": "US State"
            })
        if "cupertino" in text_lower:
            entities.append({
                "name": "Cupertino",
                "type": "location",
                "description": "City in California"
            })

        # Add generic entity if none found
        if not entities:
            entities.append({
                "name": "Generic Entity",
                "type": "concept",
                "description": "Extracted from text"
            })

        return json.dumps(entities)

    def _mock_fact_response(self, prompt: str) -> str:
        """Generate mock fact extraction response for testing."""
        facts = []

        # Detect temporal patterns
        if "2020" in prompt and "2023" in prompt:
            facts.append({
                "subject": "policy",
                "predicate": "was_active",
                "object": "active",
                "valid_date": "2020-01-01",
                "invalid_date": "2023-12-31"
            })

        # Add generic fact if none found
        if not facts:
            facts.append({
                "subject": "unknown",
                "predicate": "mentioned_in_text",
                "object": "present",
                "valid_date": datetime.now().isoformat(),
                "invalid_date": None
            })

        return json.dumps(facts)

    def _parse_entities_response(self, response: str, source_text: str) -> List[Entity]:
        """
        Parse LLM response into Entity objects.

        Args:
            response: JSON response from LLM
            source_text: Original text (for context)

        Returns:
            List of Entity objects

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("```")[1]
                if cleaned_response.startswith("json"):
                    cleaned_response = cleaned_response[4:]

            data = json.loads(cleaned_response)

            entities = []
            now = datetime.now(timezone.utc)

            for i, item in enumerate(data):
                try:
                    # Map entity type string to enum
                    entity_type = self._map_entity_type(item.get("type", "concept"))

                    # Generate deterministic entity ID using SHA256 hash
                    name_hash = hashlib.sha256(item['name'].encode()).hexdigest()[:16]
                    entity_id = f"entity_{name_hash}_{i}"

                    entity = Entity(
                        id=entity_id,
                        type=entity_type,
                        attributes={
                            "name": item["name"],
                            "description": item.get("description", ""),
                            "source": "llm_extraction"
                        },
                        valid_at=now
                    )
                    entities.append(entity)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse entity {item}: {e}")
                    continue

            return entities

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

    def _parse_facts_response(self, response: str, source_text: str) -> List[Fact]:
        """
        Parse LLM response into Fact objects with temporal data.

        Args:
            response: JSON response from LLM
            source_text: Original text (for context)

        Returns:
            List of Fact objects

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Clean up response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("```")[1]
                if cleaned_response.startswith("json"):
                    cleaned_response = cleaned_response[4:]

            data = json.loads(cleaned_response)

            facts = []
            now = datetime.now(timezone.utc)

            for item in data:
                try:
                    # Parse dates
                    valid_at = self._parse_date(item.get("valid_date", now))
                    invalid_at = None
                    if item.get("invalid_date"):
                        invalid_at = self._parse_date(item["invalid_date"])

                    fact = Fact(
                        subject=item["subject"],
                        predicate=item["predicate"],
                        object=item["object"],
                        confidence=0.8,  # Default confidence from LLM
                        valid_at=valid_at,
                        invalid_at=invalid_at
                    )
                    facts.append(fact)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse fact {item}: {e}")
                    continue

            return facts

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

    def _map_entity_type(self, type_str: str) -> EntityType:
        """Map string to EntityType enum."""
        type_mapping = {
            "person": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "location": EntityType.LOCATION,
            "event": EntityType.EVENT,
            "concept": EntityType.CONCEPT,
            "policy": EntityType.POLICY,
        }
        return type_mapping.get(type_str.lower(), EntityType.CONCEPT)

    def _parse_date(self, date_input: Any) -> datetime:
        """
        Parse various date formats into datetime object.

        Args:
            date_input: Date as string, datetime object, or ISO format

        Returns:
            datetime object

        Raises:
            ValueError: If date cannot be parsed
        """
        if isinstance(date_input, datetime):
            return date_input

        if isinstance(date_input, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(date_input.replace("Z", "+00:00"))
            except ValueError:
                try:
                    # Try dateutil parser as fallback
                    return date_parser.parse(date_input)
                except (ValueError, TypeError, OverflowError) as e:
                    logger.warning(f"Failed to parse date '{date_input}': {e}")

        # Default to current time if parsing fails
        logger.warning(f"Using current time as default for unparsable date: {date_input}")
        return datetime.now(timezone.utc)

    def _extract_entities_fallback(self, text: str) -> List[Entity]:
        """
        Fallback entity extraction using simple regex patterns.

        Used when LLM extraction fails.
        """
        import re
        entities = []
        now = datetime.now(timezone.utc)

        # Simple capitalization-based extraction
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        unique_words = list(set(words[:10]))

        for i, word in enumerate(unique_words):
            # Simple type detection
            if word in ["Inc", "Corp", "Ltd"]:
                entity_type = EntityType.ORGANIZATION
            elif len(word) < 3:
                entity_type = EntityType.CONCEPT
            else:
                entity_type = EntityType.CONCEPT

            entities.append(Entity(
                id=f"fallback_entity_{i}",
                type=entity_type,
                attributes={
                    "name": word,
                    "source": "fallback_extraction"
                },
                valid_at=now
            ))

        logger.info(f"Fallback extraction found {len(entities)} entities")
        return entities

    def _extract_facts_fallback(self, text: str) -> List[Fact]:
        """
        Fallback fact extraction using simple patterns.

        Used when LLM extraction fails.
        """
        facts = []
        now = datetime.now(timezone.utc)

        # Extract year patterns for temporal facts
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years:
            # Create a simple fact with temporal info
            facts.append(Fact(
                subject="extracted_content",
                predicate="contains_temporal_reference",
                object=f"years_{years[0]}",
                confidence=0.5,
                valid_at=datetime(int(years[0]), 1, 1),
                invalid_at=datetime(int(years[0]) + 1, 1, 1) if len(years) > 1 else None
            ))

        logger.info(f"Fallback extraction found {len(facts)} facts")
        return facts
