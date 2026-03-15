import random
from typing import List
import logging

from agents.profile import (
    AgentProfile,
    MBTIType,
    PoliticalLeaning,
    Demographics,
    BehavioralProfile
)

logger = logging.getLogger(__name__)


class PersonaGenerator:
    """Generate diverse agent personas for simulation."""

    MBTI_TYPES = list(MBTIType)
    POLITICAL_LEANINGS = list(PoliticalLeaning)

    OCCUPATIONS = [
        "teacher", "engineer", "doctor", "artist", "business_owner",
        "student", "retiree", "manager", "scientist", "writer"
    ]

    LOCATIONS = ["urban", "suburban", "rural"]

    EDUCATION_LEVELS = ["high_school", "bachelor", "master", "phd"]

    def __init__(self, seed: int = None):
        """Initialize generator with optional seed for reproducibility."""
        self.rng = random.Random(seed)

    async def generate_population(
        self,
        count: int,
        diversity_config: dict = None
    ) -> List[AgentProfile]:
        """Generate N diverse agent profiles."""
        logger.info(f"Generating {count} agent personas")

        profiles = []

        mbti_distribution = self._distribute_types(count, self.MBTI_TYPES)
        political_distribution = self._distribute_types(count, self.POLITICAL_LEANINGS)

        for i in range(count):
            mbti = mbti_distribution[i]
            political = political_distribution[i]

            profile = AgentProfile(
                id=f"agent_{i:04d}",
                mbti=mbti,
                demographics=self._generate_demographics(),
                behavioral=self._generate_behavioral(mbti),
                political_leaning=political,
                information_sources=self._generate_info_sources(),
                memory_capacity=self.rng.randint(50, 200)
            )
            profiles.append(profile)

        logger.info(f"Generated {len(profiles)} diverse personas")
        return profiles

    def _distribute_types(self, count: int, types: List) -> List:
        """Distribute types evenly across population."""
        result = []
        per_type = max(1, count // len(types))

        for _ in range(count):
            type_index = (len(result) // per_type) % len(types)
            result.append(types[type_index])

        self.rng.shuffle(result)
        return result

    def _generate_demographics(self) -> Demographics:
        """Generate random demographic attributes."""
        return Demographics(
            age=self.rng.randint(18, 75),
            gender=self.rng.choice(["male", "female", "non_binary", "prefer_not_to_say"]),
            education=self.rng.choice(self.EDUCATION_LEVELS),
            occupation=self.rng.choice(self.OCCUPATIONS),
            location=self.rng.choice(self.LOCATIONS),
            income_level=self.rng.choice(["low", "medium", "high", "very_high"])
        )

    def _generate_behavioral(self, mbti: MBTIType) -> BehavioralProfile:
        """Generate behavioral traits influenced by MBTI."""
        is_introvert = mbti.value[0] == 'I'
        is_intuitive = mbti.value[1] == 'N'
        is_thinking = mbti.value[2] == 'T'
        is_judging = mbti.value[3] == 'J'

        return BehavioralProfile(
            openness=0.7 if is_intuitive else 0.4,
            conscientiousness=0.8 if is_judging else 0.5,
            extraversion=0.3 if is_introvert else 0.7,
            agreeableness=0.6 if not is_thinking else 0.4,
            neuroticism=self.rng.uniform(0.2, 0.7)
        )

    def _generate_info_sources(self) -> List[str]:
        """Generate information source preferences."""
        all_sources = [
            "twitter", "reddit", "news_website", "social_media",
            "podcasts", "youtube", "traditional_media", "forums"
        ]
        count = self.rng.randint(2, 4)
        return self.rng.sample(all_sources, count)
