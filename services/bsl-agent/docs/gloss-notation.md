# BSL Gloss Notation Standards

**Version:** 1.0.0
**Date:** 2026-03-03
**Service:** BSL Text2Gloss Agent (Port 8003)

---

## Overview

This document defines the gloss notation standards used by the BSL Text2Gloss Agent for converting English text to British Sign Language (BSL) gloss notation.

---

## What is Gloss Notation?

Gloss notation is a written representation of sign language that captures:
- **Handshapes:** How the hands are formed
- **Location:** Where signs are made (head, body, space)
- **Movement:** How signs move and transition
- **Facial Expressions:** Non-manual markers that change meaning
- **Orientation:** Palm and finger orientation

---

## BSL SignSpell Standard

The BSL SignSpell system uses the following notation format:

```
SIGN-HANDSHAPE[location]movement
```

### Examples:

| English | BSL Gloss | Meaning |
|---------|-----------|---------|
| Hello | HELLO[right] | Wave hand on right side |
| Yes | YES[head]nod | Head nod with yes sign |
| No | NO[head]shake | Head shake with no sign |
| Thank you | THANK-YOU[chest]outward | Sign from chest moving outward |

---

## Grammar Rules

### 1. Finger Spelling

Individual letters are finger-spelt using the pattern:

```
FS-A FS-B FS-C...
```

Example: "CAT" → `FS-C FS-A FS-T`

### 2. Numbers

Numbers have specific signs (not finger-spelt):

```
ONE, TWO, THREE... TEN
```

For larger numbers:
```
25 = TWENTY-FIVE
100 = ONE-HUNDRED
```

### 3. Directional Signs

Signs that include directionality use notation:

```
MOVE[left]  # Move toward left
MOVE[right] # Move toward right
MOVE[to-him] # Move toward person referred to
```

### 4. Body Anchors

Common body anchor notation:

```
[head]     # Head/face area
[chest]    # Chest/sternum
[forehead] # Forehead
[hand]     # Non-dominant hand
[space]    # Neutral space in front of signer
```

### 5. Movement Notation

Movement types are encoded in gloss:

```
→movement       # Straight line movement
↗movement       # Arc movement
↺movement       # Circular movement
↓movement       # Downward movement
↑movement       # Upward movement
↔movement       # Wrist rotation
```

---

## Sentence Structure

BSL grammar differs from English grammar. The gloss notation reflects this:

### Time-Topic-Comment Structure

**English:** "Yesterday I went to the cinema."
**BSL Gloss:** `YESTERDAY CINEMA I GO`

### Question Formation

**English:** "Do you like coffee?"
**BSL Gloss:** `COFFEE YOU LIKE WHAT` (with facial expression)

### Negation

**English:** "I don't understand."
**BSL Gloss:** `UNDERSTAND I NOT` (with headshake and negative facial expression)

---

## Non-Manual Markers

Facial expressions and body language are encoded in gloss:

| Marker | Notation | Meaning |
|--------|----------|---------|
| Question | `?` or `q` | Eyebrows raised, lean forward |
| Conditional | `cond` | Eyebrows raised, head tilted |
| Negation | `neg` | Headshake, frowned |
| Topic | `top` | Raised eyebrows, slight lean forward |
| Emphasis | `!` or `e` | Stronger facial expression, larger sign |

---

## Proper Nouns

Names and places are typically finger-spelt:

```
FS-A FS-L FS-I FS-X (ALICE)
FS-L FS-O FS-N FS-D FS-O FS-N (LONDON)
```

---

## Regional Variations

BSL has regional variations. The gloss notation includes region tags:

```
WORD[region=northern]
WORD[region=scottish]
WORD[region=london]
```

---

## Technical Implementation

### Data Structure

```python
@dataclass
class BSLGloss:
    text: str              # Original English text
    gloss: str             # BSL gloss notation
    gloss_format: str      # "singspell" | "hamnosys"
    duration: float        # Estimated signing duration (seconds)
    breakdown: List[str]   # Individual signs in sequence
    non_manual_markers: List[str]  # Facial expressions
    region: Optional[str]  # Regional variation
```

### Example Transformation

**Input:**
```python
{
    "text": "Hello, how are you?",
    "language": "en"
}
```

**Output:**
```python
{
    "text": "Hello, how are you?",
    "gloss": "HELLO[right]wave HOW YOU ?q",
    "gloss_format": "singspell",
    "duration": 3.2,
    "breakdown": ["HELLO[right]", "HOW", "YOU", "?q"],
    "non_manual_markers": ["q"],
    "region": null
}
```

---

## Gloss Frequency Dictionary

Common English phrases to BSL gloss mappings:

| English | BSL Gloss | Notes |
|---------|-----------|-------|
| Good morning | GOOD-MORNING[space] | Standard greeting |
| Please | PLEASE[chest] | Politeness marker |
| Sorry | SORRY[space] | Apology |
| Thank you | THANK-YOU[chest] | Gratitude |
| Look | LOOK[head-point] | Attention getter |
| Listen | LISTEN[ears] | Request attention |

---

## Machine Translation Integration

The BSL Agent can integrate with machine translation services:

1. **Statistical MT:** For common phrases
2. **Rule-Based:** For grammatical structure
3. **Neural MT:** For complex sentences (future)

Fallback chain:
```
Dictionary lookup → Rule-based translation → Neural MT → Gloss template
```

---

**Status:** ✅ Gloss Notation Standard Defined
**Next:** Implement BSL Translation Service
