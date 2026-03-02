# Testing Standards

**Version:** 1.0.0

## Test Naming

```python
def test_{function}_{scenario}_{expected_result}():
    pass
```

## AAA Pattern

Arrange-Act-Assert structure:

```python
def test_generate_dialogue_with_positive_sentiment():
    # Arrange
    context = "A sunny garden"
    sentiment = 0.8

    # Act
    result = generate_dialogue(context, sentiment)

    # Assert
    assert result["dialogue"] is not None
    assert len(result["dialogue"]) > 0
```

## Coverage

Minimum coverage by service:
- OpenClaw: 85%
- SceneSpeak: 80%
- Safety: 90%
- Others: 75%
