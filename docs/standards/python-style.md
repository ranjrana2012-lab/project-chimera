# Python Code Style Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-27

## Formatting

- Use `black` for code formatting
- Use `isort` for import sorting
- Line length: 100 characters

## Type Hints

All public functions MUST have type hints:

```python
def generate_dialogue(context: str, sentiment: float) -> dict:
    pass
```

## Docstrings

Use Google style docstrings:

```python
def generate_dialogue(context: str, sentiment: float) -> dict:
    """Generate dialogue for the given context.

    Args:
        context: Scene description
        sentiment: Sentiment value (-1.0 to 1.0)

    Returns:
        Dictionary with 'dialogue' and 'metadata' keys
    """
    pass
```

## Imports

Order: 1) stdlib, 2) third-party, 3) local

```python
import os
from datetime import datetime

import redis
import torch

from services.openclaw.src.core import skill_registry
```
