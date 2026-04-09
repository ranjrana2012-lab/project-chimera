# BSL Avatar Service

Project Chimera Phase 2 - British Sign Language (BSL) avatar generation service for live theatrical performances.

## Overview

The BSL Avatar Service provides real-time British Sign Language translation and avatar rendering for live theatrical performances. It translates English text to BSL sign sequences and generates avatar animations with non-manual features (facial expressions, body language).

## Features

- **Text-to-Sign Translation**: Convert English text to BSL sign sequences
- **Gesture Library**: Comprehensive BSL gesture database
- **Linguistic Features**: Part-of-speech analysis and grammatical structure
- **Non-Manual Features**: Facial expressions, eyebrow position, body lean
- **Fingerspelling Fallback**: Automatic fingerspelling for unknown words
- **Question Detection**: Automatic facial expression adjustments for questions
- **Avatar Rendering**: Generate avatar animation commands

## Installation

```bash
# Install dependencies
pip install -e .[bsl]

# Or install with all Phase 2 dependencies
pip install -e .[all]
```

## Quick Start

```python
from bsl_avatar_service import BSLAvatarService, BSLGesture

# Create gesture library
library = {
    "hello": BSLGesture(
        id="hello",
        word="hello",
        part_of_speech="interjection",
        handshape="open_hand",
        orientation="palm_out",
        location="forehead",
        movement="wave",
        non_manual_features={
            "facial_expression": "friendly",
            "eyebrows": "raised"
        }
    ),
    # Add more gestures...
}

# Create service
service = BSLAvatarService(library)

# Translate and render
import asyncio
asyncio.run(service.translate_and_render("hello thank you"))
```

## Usage Examples

See `examples/bsl_avatar_example.py` for comprehensive usage examples including:
- Basic translation
- Question handling
- Fingerspelling fallback
- Complete conversations

Run the example:
```bash
cd services/bsl-avatar-service
python examples/bsl_avatar_example.py
```

## Testing

```bash
# Run all tests
pytest tests/test_bsl_avatar_service.py -v

# Run with coverage
pytest tests/test_bsl_avatar_service.py --cov=bsl_avatar_service --cov-report=html

# Run specific test
pytest tests/test_bsl_avatar_service.py::TestBSLTranslator::test_fingerspelling_fallback -v
```

## API Reference

### BSLAvatarService

Main service for BSL avatar generation.

**Parameters:**
- `gesture_library` (dict): Dictionary of word -> BSLGesture mappings

**Methods:**
- `translate_and_render(text)`: Translate text and render as avatar animation
- `get_status()`: Get service status

### BSLTranslator

Translates English text to BSL sign sequences.

**Parameters:**
- `gesture_library` (dict): Dictionary of word -> BSLGesture mappings

**Methods:**
- `translate(text)`: Translate English text to SignSequence

### BSLAvatarRenderer

Generates avatar animation commands from sign sequences.

**Methods:**
- `render_sign_sequence(sign_sequence)`: Render a sign sequence as animation

### BSLGesture

Represents a BSL sign/gesture.

**Attributes:**
- `id` (str): Gesture identifier
- `word` (str): English word
- `part_of_speech` (str): Noun, verb, adjective, etc.
- `handshape` (str): Hand configuration
- `orientation` (str): Palm orientation
- `location` (str): Signing location
- `movement` (str): Movement pattern
- `non_manual_features` (dict): Facial expressions, body language

### SignSequence

Represents a sequence of signs forming a phrase.

**Attributes:**
- `gestures` (list): List of BSLGesture objects
- `timing_ms` (list): Duration of each gesture in milliseconds
- `non_manual_features` (list): Facial expressions for each gesture

## BSL Linguistic Features

### Grammar and Structure

BSL has different grammar from English:

**Example:**
- English: "What is your name?"
- BSL: "YOUR NAME WHAT?" (topic-comment structure)

The translator handles basic structural differences.

### Non-Manual Features

BSL uses non-manual features for grammatical information:

| Feature | Purpose | Values |
|---------|---------|--------|
| Facial Expression | Emotion, grammar | friendly, questioning, negating |
| Eyebrows | Grammar markers | raised, furrowed, relaxed |
| Body Lean | Emphasis, topic | slight_forward, slight_back, none |

### Fingerspelling

Unknown words are automatically fingerspelled:
- Uses fingerspelling handshape
- Faster timing (500ms vs 1000ms per sign)
- Maintains conversation flow

## Gesture Library Structure

### Required Fields

Every gesture must have:
- **id**: Unique identifier
- **word**: English word (lowercase)
- **part_of_speech**: Grammatical category
- **handshape**: Hand configuration
- **orientation**: Palm orientation
- **location**: Signing location
- **movement**: Movement pattern
- **non_manual_features**: Facial/body features

### Part of Speech Categories

- **interjection**: Hello, thank you, etc.
- **verb**: Action words
- **noun**: Objects, concepts
- **pronoun**: I, you, my, your, etc.
- **adjective**: Descriptive words
- **question**: What, where, when, etc.

### Handshape Examples

- **open_hand**: Fingers extended, thumb extended
- **flat_hand**: Fingers together, flat palm
- **index_finger**: Pointing hand
- **fist**: Closed fist
- **fingerspelling**: Manual alphabet

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bsl_avatar_service --cov-report=term-missing
```

### Code Formatting

```bash
# Format code
black bsl_avatar_service.py

# Check linting
ruff check bsl_avatar_service.py

# Type checking
mypy bsl_avatar_service.py
```

### Building Gesture Library

To expand the gesture library:

1. **Research**: Consult BSL dictionaries and resources
2. **Document**: Document each gesture with all required fields
3. **Test**: Add tests for new gestures
4. **Validate**: Test with BSL users if possible

## Hardware Requirements

### Rendering

Avatar rendering requires:
- Unity WebGL or similar rendering engine
- 3D avatar model with rigging
- Animation system for gestures
- Facial animation system

### Performance

For real-time performance:
- Low-latency rendering pipeline
- Optimized gesture database
- Efficient animation blending

## BSL Partnership

This service is designed to work with BSL research partners. For production use, we recommend:

1. **Academic Partnership**: Work with BSL linguistics departments
2. **Community Partnership**: Consult with Deaf community members
3. **Professional Services**: License commercial gesture libraries

See `docs/phase2/BSL_PARTNERSHIP_GUIDELINES.md` for details.

## Cultural Considerations

### BSL vs English

BSL is a distinct language with its own grammar:
- Different word order
- Grammatical facial expressions
- Spatial referencing
- Role-shifting

### Regional Variations

BSL has regional variations:
- Signs may vary by region
- Consult local BSL users
- Document regional variations used

### Appropriateness

Important cultural considerations:
- BSL belongs to Deaf community
- Respect Deaf culture
- Consult with BSL users
- Acknowledge limitations

## Limitations

### Current Implementation

This is a **skeleton implementation** for Phase 2 technical foundation:
- No actual avatar rendering (placeholder)
- Limited gesture library (sample gestures only)
- No grammatical structure processing
- No spatial referencing

### Future Development

Phase 2 will address:
- Full gesture library (2,000+ signs)
- Real avatar rendering
- Grammatical processing
- Spatial referencing
- Role-shifting
- Speed variations

## Troubleshooting

### Translation Issues

If words aren't translating:
1. Check word is in gesture library (lowercase)
2. Verify gesture library is loaded
3. Check for typos in input text
4. Fingerspelling will be used for unknown words

### Rendering Issues

If avatar doesn't render:
1. Check renderer is connected
2. Verify animation commands are being sent
3. Check avatar model is loaded
4. Review console for error messages

## Best Practices

### Gesture Library

1. **Standardize**: Use consistent terminology
2. **Document**: Document all variations
3. **Test**: Test with BSL users
4. **Update**: Keep library current

### Translation

1. **Simplify**: Use simple, clear language
2. **Punctuation**: Use question marks for questions
3. **Spacing**: Use proper spacing between words
4. **Context**: Consider context for meaning

## Resources

### BSL Resources

- [British Sign Language (BSL) Dictionary](https://www.signbsl.com/)
- [Sign Community](https://www.signcommunity.org.uk/)
- [British Deaf Association](https://bda.org.uk/)

### Technical Resources

- [Mediapipe Hand Tracking](https://google.github.io/mediapipe/)
- [Unity Animation](https://docs.unity3d.com/Manual/AnimationSection.html)
- [WebGL Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add gestures with proper documentation
4. Add tests for new gestures
5. Ensure all tests pass
6. Submit a pull request

**Important**: When adding BSL gestures:
- Consult BSL resources
- Document sources
- Consider regional variations
- Test with BSL users if possible

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/ranjrana2012-lab/project-chimera
- Issues: https://github.com/ranjrana2012-lab/project-chimera/issues

## Project Chimera

This service is part of Project Chimera, an AI-powered adaptive live theatre framework.

For more information:
- Documentation: https://github.com/ranjrana2012-lab/project-chimera/docs
- Phase 2 Plan: See `docs/PHASE_2_IMPLEMENTATION_PLAN.md`
- BSL Guidelines: See `docs/phase2/BSL_PARTNERSHIP_GUIDELINES.md`
