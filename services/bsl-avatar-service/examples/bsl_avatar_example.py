#!/usr/bin/env python3
"""
BSL Avatar Service Example Usage

Demonstrates how to use the British Sign Language avatar service.
"""

import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bsl_avatar_service import (
    BSLAvatarService,
    BSLTranslator,
    BSLGesture,
    SignSequence
)


def create_sample_gesture_library():
    """Create a sample BSL gesture library."""
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
                "eyebrows": "raised",
                "body_lean": "slight_forward"
            }
        ),
        "thank": BSLGesture(
            id="thank",
            word="thank",
            part_of_speech="verb",
            handshape="flat_hand",
            orientation="palm_up",
            location="chest",
            movement="circular_motion",
            non_manual_features={
                "facial_expression": "grateful",
                "eyebrows": "relaxed",
                "body_lean": "slight_forward"
            }
        ),
        "please": BSLGesture(
            id="please",
            word="please",
            part_of_speech="verb",
            handshape="flat_hand",
            orientation="palm_up",
            location="chest",
            movement="circular_motion",
            non_manual_features={
                "facial_expression": "pleading",
                "eyebrows": "raised",
                "body_lean": "slight_forward"
            }
        ),
        "yes": BSLGesture(
            id="yes",
            word="yes",
            part_of_speech="affirmation",
            handshape="fist",
            orientation="palm_out",
            location="head",
            movement="nod",
            non_manual_features={
                "facial_expression": "confirming",
                "eyebrows": "relaxed",
                "body_lean": "none"
            }
        ),
        "no": BSLGesture(
            id="no",
            word="no",
            part_of_speech="negation",
            handshape="index_finger",
            orientation="palm_out",
            location="nose",
            movement="shake",
            non_manual_features={
                "facial_expression": "negating",
                "eyebrows": "furrowed",
                "body_lean": "slight_back"
            }
        ),
        "name": BSLGesture(
            id="name",
            word="name",
            part_of_speech="noun",
            handshape="index_finger",
            orientation="palm_out",
            location="shoulder",
            movement="tap_twice",
            non_manual_features={
                "facial_expression": "neutral",
                "eyebrows": "relaxed",
                "body_lean": "none"
            }
        ),
        "what": BSLGesture(
            id="what",
            word="what",
            part_of_speech="pronoun",
            handshape="flat_hand",
            orientation="palm_up",
            location="chest",
            movement="shake",
            non_manual_features={
                "facial_expression": "questioning",
                "eyebrows": "raised",
                "body_lean": "slight_forward"
            }
        ),
        "your": BSLGesture(
            id="your",
            word="your",
            part_of_speech="pronoun",
            handshape="flat_hand",
            orientation="palm_out",
            location="chest",
            movement="circle",
            non_manual_features={
                "facial_expression": "neutral",
                "eyebrows": "relaxed",
                "body_lean": "none"
            }
        ),
        "my": BSLGesture(
            id="my",
            word="my",
            part_of_speech="pronoun",
            handshape="flat_hand",
            orientation="palm_in",
            location="chest",
            movement="tap",
            non_manual_features={
                "facial_expression": "neutral",
                "eyebrows": "relaxed",
                "body_lean": "none"
            }
        ),
        "welcome": BSLGesture(
            id="welcome",
            word="welcome",
            part_of_speech="interjection",
            handshape="open_hand",
            orientation="palm_up",
            location="side",
            movement="sweep_in",
            non_manual_features={
                "facial_expression": "friendly",
                "eyebrows": "raised",
                "body_lean": "slight_forward"
            }
        )
    }
    return library


def example_basic_translation(service):
    """Example: Basic text-to-sign translation."""
    print("\n=== Example: Basic Translation ===")

    texts = [
        "hello",
        "thank you",
        "hello thank you",
        "yes no"
    ]

    for text in texts:
        print(f"\nTranslating: '{text}'")
        sequence = service.translator.translate(text)
        print(f"Gestures: {len(sequence.gestures)}")
        for i, gesture in enumerate(sequence.gestures):
            print(f"  {i+1}. {gesture.word} ({gesture.part_of_speech})")
            print(f"     Timing: {sequence.timing_ms[i]}ms")


def example_question_translation(service):
    """Example: Translating questions."""
    print("\n=== Example: Question Translation ===")

    questions = [
        "what is your name?",
        "hello?",
        "thank you?"
    ]

    for text in questions:
        print(f"\nTranslating: '{text}'")
        sequence = service.translator.translate(text)
        print(f"Gestures: {len(sequence.gestures)}")
        for i, gesture in enumerate(sequence.gestures):
            features = sequence.non_manual_features[i]
            print(f"  {i+1}. {gesture.word}")
            print(f"     Expression: {features.get('facial_expression', 'neutral')}")
            print(f"     Eyebrows: {features.get('eyebrows', 'relaxed')}")


def example_fingerspelling(service):
    """Example: Fingerspelling for unknown words."""
    print("\n=== Example: Fingerspelling ===")

    texts = [
        "hello ABC thank",
        "my name is XYZ",
        "welcome QWERTY"
    ]

    for text in texts:
        print(f"\nTranslating: '{text}'")
        sequence = service.translator.translate(text)
        print(f"Gestures: {len(sequence.gestures)}")
        for i, gesture in enumerate(sequence.gestures):
            if gesture.handshape == "fingerspelling":
                print(f"  {i+1}. {gesture.word} (FINGERSPELLING)")
                print(f"     Timing: {sequence.timing_ms[i]}ms (faster)")
            else:
                print(f"  {i+1}. {gesture.word} (known gesture)")


async def example_rendering(service):
    """Example: Rendering sign sequences."""
    print("\n=== Example: Avatar Rendering ===")

    texts = [
        "hello",
        "thank you",
        "what is your name?"
    ]

    for text in texts:
        print(f"\nTranslating and rendering: '{text}'")
        await service.translate_and_render(text)
        print("Rendering complete!")


def example_service_status(service):
    """Example: Checking service status."""
    print("\n=== Example: Service Status ===")

    status = service.get_status()
    print(f"State: {status['state']}")
    print(f"Gesture Library Size: {status['gesture_library_size']}")
    print(f"Current Sign Sequence: {status['current_sign_sequence']}")


def example_gesture_details():
    """Example: Inspecting gesture details."""
    print("\n=== Example: Gesture Details ===")

    library = create_sample_gesture_library()
    gesture = library["hello"]

    print(f"Gesture: {gesture.word}")
    print(f"  ID: {gesture.id}")
    print(f"  Part of Speech: {gesture.part_of_speech}")
    print(f"  Handshape: {gesture.handshape}")
    print(f"  Orientation: {gesture.orientation}")
    print(f"  Location: {gesture.location}")
    print(f"  Movement: {gesture.movement}")
    print(f"  Non-Manual Features:")
    for key, value in gesture.non_manual_features.items():
        print(f"    {key}: {value}")


async def example_complete_conversation(service):
    """Example: Complete BSL conversation."""
    print("\n=== Example: Complete Conversation ===")

    conversation = [
        "hello",
        "what is your name?",
        "my name is John",
        "thank you",
        "welcome"
    ]

    print("BSL Avatar Conversation:")
    print("-" * 40)

    for text in conversation:
        print(f"\nInput: {text}")
        await service.translate_and_render(text)
        print("✓ Rendered")

    print("\n" + "-" * 40)
    print("Conversation complete!")


def main():
    """Main example function."""
    print("=" * 60)
    print("BSL Avatar Service Example Usage")
    print("=" * 60)

    # Create gesture library
    library = create_sample_gesture_library()
    print(f"\nCreated gesture library: {len(library)} signs")

    # Create service
    service = BSLAvatarService(library)
    print("Created BSL Avatar Service")

    # Run synchronous examples
    example_basic_translation(service)
    example_question_translation(service)
    example_fingerspelling(service)
    example_service_status(service)
    example_gesture_details()

    # Run async examples
    print("\n" + "=" * 60)
    print("Async Rendering Examples")
    print("=" * 60)

    asyncio.run(example_rendering(service))
    asyncio.run(example_complete_conversation(service))

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
