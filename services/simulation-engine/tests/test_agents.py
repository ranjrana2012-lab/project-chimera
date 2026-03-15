import pytest
from agents.persona import PersonaGenerator
from agents.profile import MBTIType, PoliticalLeaning


@pytest.mark.asyncio
async def test_generate_population():
    """Test generating a population of agents."""
    generator = PersonaGenerator(seed=42)

    profiles = await generator.generate_population(count=10)

    assert len(profiles) == 10

    mbti_types = set(p.mbti for p in profiles)
    political_types = set(p.political_leaning for p in profiles)

    assert len(mbti_types) > 1
    assert len(political_types) > 1


@pytest.mark.asyncio
async def test_agent_profile_completeness():
    """Test that generated profiles have all required fields."""
    generator = PersonaGenerator()

    profiles = await generator.generate_population(count=5)

    for profile in profiles:
        assert profile.id.startswith("agent_")
        assert profile.mbti in MBTIType
        assert profile.political_leaning in PoliticalLeaning
        assert 18 <= profile.demographics.age <= 75
        assert 0 <= profile.behavioral.openness <= 1
        assert len(profile.information_sources) >= 2
        assert 50 <= profile.memory_capacity <= 200


@pytest.mark.asyncio
async def test_reproducibility_with_seed():
    """Test that same seed produces same results."""
    generator1 = PersonaGenerator(seed=123)
    generator2 = PersonaGenerator(seed=123)

    profiles1 = await generator1.generate_population(count=10)
    profiles2 = await generator2.generate_population(count=10)

    assert len(profiles1) == len(profiles2)

    for p1, p2 in zip(profiles1, profiles2):
        assert p1.mbti == p2.mbti
        assert p1.demographics.age == p2.demographics.age
