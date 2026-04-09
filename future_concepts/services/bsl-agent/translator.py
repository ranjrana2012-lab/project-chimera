"""
BSL Translator Module

Implements English to BSL (British Sign Language) gloss notation translation.
Uses rule-based translation for now with ML enhancement planned for later.
"""

import time
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class BSLTranslator:
    """
    BSL Text-to-Gloss translator.

    Features:
    - Dictionary-based translation for common phrases
    - Rule-based translation for grammatical structures
    - Non-manual marker (NMM) generation for facial expressions and body language
    - Word-by-word fallback for unknown words
    """

    # Common phrase dictionary for BSL
    PHRASE_DICTIONARY = {
        "hello": "HELLO",
        "good morning": "GOOD MORNING",
        "please": "PLEASE",
        "thank you": "THANK YOU",
        "sorry": "SORRY",
        "yes": "YES",
        "no": "NO",
        "how are you": "HOW YOU",
        "what is your name": "NAME YOUR WHAT",
        "my name is": "NAME MY",
        "i understand": "UNDERSTAND I",
        "i don't understand": "UNDERSTAND I NOT",
        "look": "LOOK",
        "listen": "LISTEN",
        "welcome": "WELCOME",
        "goodbye": "GOODBYE",
        "good evening": "GOOD EVENING",
        "good night": "GOOD NIGHT",
        "excuse me": "EXCUSE ME",
        "help": "HELP",
        "stop": "STOP",
        "wait": "WAIT",
        "thank": "THANK",
        "you": "YOU",
        "me": "ME",
        "he": "HE",
        "she": "SHE",
        "we": "WE",
        "they": "THEY",
        "what": "WHAT",
        "where": "WHERE",
        "when": "WHEN",
        "why": "WHY",
        "who": "WHO",
        "which": "WHICH",
        "how": "HOW",
        "this": "THIS",
        "that": "THAT",
        "here": "HERE",
        "there": "THERE",
        "now": "NOW",
        "later": "LATER",
        "today": "TODAY",
        "tomorrow": "TOMORROW",
        "yesterday": "YESTERDAY",
    }

    # Non-manual markers for questions and emphasis
    NMM_MARKERS = {
        "question": ["brows-down", "head-tilt", "hold-last-sign"],
        "wh-question": ["brows-down", "head-tilt", "hold-last-sign", "eyes-wide"],
        "yes-no-question": ["brows-up", "head-tilt", "hold-last-sign"],
        "negation": ["head-shake", "brows-down"],
        "conditional": ["brows-up", "head-tilt"],
        "topic": ["brows-up", "head-nod"],
        "emphasis": ["brows-down", "eyes-wide"],
        "exclamation": ["eyes-wide", "body-lean-forward"],
    }

    def __init__(self):
        """Initialize BSL translator."""
        self.logger = logging.getLogger(__name__)

    def text_to_gloss(self, text: str) -> tuple[str, List[str], float]:
        """
        Convert English text to BSL gloss notation.

        Args:
            text: English text to translate

        Returns:
            Tuple of (gloss text, word breakdown, estimated duration in seconds)

        Example:
            >>> translator = BSLTranslator()
            >>> gloss, breakdown, duration = translator.text_to_gloss("Hello, how are you?")
            >>> print(gloss)  # "HELLO HOW YOU"
        """
        start_time = time.time()

        # Clean and normalize text
        text = text.lower().strip()
        text = text.rstrip("!?.,;:")

        # Check phrase dictionary first
        if text in self.PHRASE_DICTIONARY:
            gloss = self.PHRASE_DICTIONARY[text]
            breakdown = [gloss]
            duration = len(breakdown) * 0.5
            translation_time = time.time() - start_time

            logger.info(f"Translation from dictionary: '{text}' -> '{gloss}'")
            return gloss, breakdown, duration

        # Word-by-word translation
        words = text.split()
        gloss_words = []

        for word in words:
            # Clean word
            clean_word = word.strip(".,!?;:")

            # Check dictionary
            if clean_word in self.PHRASE_DICTIONARY:
                gloss_words.append(self.PHRASE_DICTIONARY[clean_word])
            else:
                # Finger-spelt word for unknown words
                gloss_words.append(self._finger_spell(clean_word))

        gloss = " ".join(gloss_words)
        breakdown = gloss_words
        duration = len(breakdown) * 0.5  # 0.5 seconds per sign
        translation_time = time.time() - start_time

        logger.info(
            f"Translation completed: '{text}' -> '{gloss}' "
            f"({len(breakdown)} signs, {translation_time*1000:.2f}ms)"
        )

        return gloss, breakdown, duration

    def add_non_manual_markers(self, text: str) -> List[str]:
        """
        Add non-manual markers (NMM) for facial expressions and body movements.

        Args:
            text: English text to analyze

        Returns:
            List of NMM markers to apply

        Example:
            >>> translator = BSLTranslator()
            >>> nmm = translator.add_non_manual_markers("What is your name?")
            >>> print(nmm)  # ["brows-down", "head-tilt", "hold-last-sign"]
        """
        nmm_markers = []
        text_lower = text.lower().strip()

        # Check for question words
        wh_words = ["what", "where", "when", "why", "who", "which", "how"]
        if any(text_lower.startswith(word) for word in wh_words):
            nmm_markers.extend(self.NMM_MARKERS["wh-question"])
        elif text_lower.endswith("?"):
            nmm_markers.extend(self.NMM_MARKERS["yes-no-question"])

        # Check for negation
        negation_words = ["not", "no", "never", "nothing", "nobody", "none"]
        if any(word in text_lower.split() for word in negation_words):
            nmm_markers.extend(self.NMM_MARKERS["negation"])

        # Check for conditionals
        conditional_words = ["if", "when", "unless", "provided that"]
        if any(text_lower.startswith(word) for word in conditional_words):
            nmm_markers.extend(self.NMM_MARKERS["conditional"])

        # Check for emphasis (exclamation)
        if text_lower.endswith("!"):
            nmm_markers.extend(self.NMM_MARKERS["exclamation"])

        # Remove duplicates while preserving order
        seen = set()
        unique_nmm = []
        for marker in nmm_markers:
            if marker not in seen:
                seen.add(marker)
                unique_nmm.append(marker)

        return unique_nmm

    def _finger_spell(self, word: str) -> str:
        """
        Convert a word to finger-spelling notation.

        Args:
            word: Word to finger-spell

        Returns:
            Finger-spelled notation (e.g., "FS-H-E-L-L-O")
        """
        letters = [c.upper() for c in word if c.isalpha()]
        if letters:
            return f"FS-{'-'.join(letters)}"
        return word.upper()

    def translate_with_nmm(self, text: str) -> dict:
        """
        Translate text to BSL gloss with non-manual markers.

        Args:
            text: English text to translate

        Returns:
            Dictionary with gloss, breakdown, duration, confidence, and NMM markers

        Example:
            >>> translator = BSLTranslator()
            >>> result = translator.translate_with_nmm("What is your name?")
            >>> print(result['gloss'])  # "WHAT NAME YOUR"
            >>> print(result['non_manual_markers'])  # ["brows-down", ...]
        """
        start_time = time.time()

        gloss, breakdown, duration = self.text_to_gloss(text)
        nmm_markers = self.add_non_manual_markers(text)

        translation_time = (time.time() - start_time) * 1000  # Convert to ms

        # Calculate confidence based on dictionary hits
        dict_hits = sum(1 for word in text.lower().split() if word in self.PHRASE_DICTIONARY)
        total_words = len(text.split())
        confidence = min(1.0, (dict_hits / total_words) + 0.5) if total_words > 0 else 0.5

        return {
            "gloss": gloss,
            "breakdown": breakdown,
            "duration_estimate": duration,
            "confidence": confidence,
            "non_manual_markers": nmm_markers,
            "translation_time_ms": translation_time,
        }


__all__ = ["BSLTranslator"]
