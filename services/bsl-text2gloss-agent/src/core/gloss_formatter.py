"""BSL Gloss Notation Formatter.

Handles formatting of BSL gloss notation in various formats including
HamNoSys, Stokoe, and simplified notation.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class GlossFormat(Enum):
    """Supported gloss notation formats."""
    HAMNOSYS = "hamnosys"
    STOKOE = "stokoe"
    SIMPLIFIED = "simplified"
    SIGNWRITING = "signwriting"


class GlossFormatter:
    """Formatter for BSL gloss notation.

    Converts translated text into various BSL gloss notation formats,
    adding appropriate markers for non-manual features, handshapes,
    locations, and movements.
    """

    # BSL-specific notation markers
    NON_MANUAL_MARKERS = {
        "question": ["?brows", "?face"],
        "negation": ["-neg", "head-shake"],
        "condition": ["if", "cond"],
        "topic": ["top", "topic"],
        "emphasis": ["!", "strong"],
        "possessive": ["poss"],
        "continuous": ["prog"],
    }

    HANDSHAPES = {
        "fist": "fist",
        "open": "open",
        "point": "index",
        "v": "v-shape",
        "claw": "claw",
        "flat": "flat",
        "cupped": "cup",
    }

    LOCATIONS = {
        "head": "head",
        "face": "face",
        "chest": "chest",
        "stomach": "stom",
        "neutral": "neutral",
        "dominant_hand": "dom",
        "non_dominant_hand": "non-dom",
    }

    MOVEMENTS = {
        "up": "up",
        "down": "down",
        "towards": "toward",
        "away": "away",
        "circular": "circ",
        "wave": "wave",
        "tap": "tap",
        "rub": "rub",
    }

    def __init__(self, default_format: GlossFormat = GlossFormat.HAMNOSYS):
        """Initialize the gloss formatter.

        Args:
            default_format: Default gloss notation format to use
        """
        self.default_format = default_format

    def format_gloss(
        self,
        gloss_text: str,
        format: Optional[GlossFormat] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format gloss text in specified notation format.

        Args:
            gloss_text: Raw gloss text from translation
            format: Target notation format
            metadata: Additional metadata for formatting

        Returns:
            Formatted gloss string
        """
        format = format or self.default_format

        if format == GlossFormat.SIMPLIFIED:
            return self._format_simplified(gloss_text)
        elif format == GlossFormat.HAMNOSYS:
            return self._format_hamnosys(gloss_text, metadata)
        elif format == GlossFormat.STOKOE:
            return self._format_stokoe(gloss_text, metadata)
        else:
            return self._format_simplified(gloss_text)

    def _format_simplified(self, gloss_text: str) -> str:
        """Format in simplified gloss notation.

        Simple uppercase gloss notation with minimal markers.
        Example: "HELLO HOW YOU"

        Args:
            gloss_text: Raw gloss text

        Returns:
            Formatted simplified gloss
        """
        # Convert to uppercase and clean
        gloss = gloss_text.upper().strip()
        # Remove extra whitespace
        gloss = re.sub(r'\s+', ' ', gloss)
        return gloss

    def _format_hamnosys(
        self,
        gloss_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format in HamNoSys notation.

        HamNoSys is a comprehensive notation system for sign languages.
        Example: "^forearmback^handback armclose palmup finger2..."

        Args:
            gloss_text: Raw gloss text
            metadata: Additional sign parameters

        Returns:
            Formatted HamNoSys string
        """
        # Start with simplified base
        base_gloss = self._format_simplified(gloss_text)

        # Add HamNoSys-specific markers
        parts = []

        # Add handshape markers if provided
        if metadata and "handshape" in metadata:
            parts.append(f"handshape:{metadata['handshape']}")

        # Add location markers
        if metadata and "location" in metadata:
            parts.append(f"location:{metadata['location']}")

        # Add movement markers
        if metadata and "movement" in metadata:
            parts.append(f"movement:{metadata['movement']}")

        # Combine with base gloss
        if parts:
            hamnosys = f"^{' ^'.join(parts)} {base_gloss}"
        else:
            hamnosys = f"^{base_gloss}"

        return hamnosys

    def _format_stokoe(
        self,
        gloss_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format in Stokoe notation.

        Stokoe notation uses specific symbols for handshape, location, movement.
        Example: "(H:V)(L:chin)(M:contact)"

        Args:
            gloss_text: Raw gloss text
            metadata: Sign parameters

        Returns:
            Formatted Stokoe notation
        """
        base_gloss = self._format_simplified(gloss_text)

        # Stokoe uses specific notation structure
        # This is a simplified version
        parts = []

        if metadata:
            if "handshape" in metadata:
                h_symbol = self._stokoe_handshape(metadata["handshape"])
                parts.append(f"(H:{h_symbol})")
            if "location" in metadata:
                l_symbol = self._stokoe_location(metadata["location"])
                parts.append(f"(L:{l_symbol})")
            if "movement" in metadata:
                m_symbol = self._stokoe_movement(metadata["movement"])
                parts.append(f"(M:{m_symbol})")

        if parts:
            stokoe = f"{''.join(parts)} {base_gloss}"
        else:
            stokoe = base_gloss

        return stokoe

    def _stokoe_handshape(self, handshape: str) -> str:
        """Convert handshape to Stokoe symbol."""
        mapping = {
            "fist": "o",
            "open": "b",
            "index": "1",
            "v-shape": "v",
            "claw": "c",
        }
        return mapping.get(handshape.lower(), "b")

    def _stokoe_location(self, location: str) -> str:
        """Convert location to Stokoe symbol."""
        mapping = {
            "head": "h",
            "face": "f",
            "chest": "c",
            "neutral": "n",
        }
        return mapping.get(location.lower(), "n")

    def _stokoe_movement(self, movement: str) -> str:
        """Convert movement to Stokoe symbol."""
        mapping = {
            "up": "u",
            "down": "d",
            "toward": ">",
            "away": "<",
            "circular": "@",
        }
        return mapping.get(movement.lower(), "-")

    def add_non_manual_markers(
        self,
        gloss: str,
        markers: List[str]
    ) -> str:
        """Add non-manual markers to gloss notation.

        Args:
            gloss: Base gloss text
            markers: List of non-manual marker names

        Returns:
            Gloss with non-manual markers added
        """
        result = gloss

        for marker in markers:
            if marker in self.NON_MANUAL_MARKERS:
                for sym in self.NON_MANUAL_MARKERS[marker]:
                    result = f"{sym} {result}"

        return result

    def create_breakdown(
        self,
        gloss_text: str,
        source_text: str,
        confidence: float = 0.85
    ) -> List[Dict[str, Any]]:
        """Create detailed sign breakdown from gloss and source.

        Args:
            gloss_text: Translated gloss text
            source_text: Original English text
            confidence: Base confidence score

        Returns:
            List of sign breakdown dictionaries
        """
        gloss_words = gloss_text.split()
        source_words = source_text.split()

        breakdown = []
        min_len = min(len(gloss_words), len(source_words))

        for i in range(min_len):
            breakdown.append({
                "gloss": gloss_words[i],
                "english_source": source_words[i],
                "handshape": self._infer_handshape(gloss_words[i]),
                "location": self._infer_location(gloss_words[i]),
                "movement": self._infer_movement(gloss_words[i]),
                "non_manual": None,
                "confidence": confidence
            })

        # Handle remaining gloss words
        for i in range(min_len, len(gloss_words)):
            breakdown.append({
                "gloss": gloss_words[i],
                "english_source": "",
                "handshape": "open",
                "location": "neutral",
                "movement": "none",
                "non_manual": None,
                "confidence": confidence * 0.9
            })

        return breakdown

    def _infer_handshape(self, gloss: str) -> str:
        """Infer likely handshape from gloss.

        Args:
            gloss: Gloss word

        Returns:
            Likely handshape
        """
        gloss_lower = gloss.lower()

        # Simple inference based on common patterns
        if any(word in gloss_lower for word in ["point", "you", "i"]):
            return "index finger"
        elif any(word in gloss_lower for word in ["two", "v"]):
            return "v-shape"
        elif any(word in gloss_lower for word in ["grab", "hold"]):
            return "fist"
        else:
            return "open hand"

    def _infer_location(self, gloss: str) -> str:
        """Infer likely location from gloss.

        Args:
            gloss: Gloss word

        Returns:
            Likely location
        """
        gloss_lower = gloss.lower()

        if any(word in gloss_lower for word in ["think", "know", "understand"]):
            return "head"
        elif any(word in gloss_lower for word in ["feel", "emotion"]):
            return "chest"
        else:
            return "neutral space"

    def _infer_movement(self, gloss: str) -> str:
        """Infer likely movement from gloss.

        Args:
            gloss: Gloss word

        Returns:
            Likely movement
        """
        gloss_lower = gloss.lower()

        if any(word in gloss_lower for word in ["give", "take", "come"]):
            return "toward body"
        elif any(word in gloss_lower for word in ["go", "leave"]):
            return "away from body"
        else:
            return "minimal"

    def normalize_text(self, text: str) -> str:
        """Normalize input text for translation.

        Args:
            text: Raw input text

        Returns:
            Normalized text
        """
        # Convert to lowercase for processing
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Handle contractions
        contractions = {
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
        }

        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)

        return text
