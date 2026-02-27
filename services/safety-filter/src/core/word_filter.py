"""Word list filtering for content safety.

This module provides profanity and offensive word filtering using
configurable word lists and pattern matching.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
import json


class WordFilter:
    """Word list-based content filter for profanity and offensive content.

    This filter uses configurable word lists and patterns to detect
    profanity, slurs, and other offensive content.
    """

    def __init__(
        self,
        word_list_path: Optional[Path] = None,
        custom_patterns: Optional[Dict[str, List[str]]] = None
    ):
        """Initialize the word filter.

        Args:
            word_list_path: Path to word list configuration file
            custom_patterns: Optional custom patterns dictionary
        """
        self.word_list_path = word_list_path
        self.custom_patterns = custom_patterns or {}

        # Word lists organized by category and severity
        self.word_lists: Dict[str, Dict[str, Set[str]]] = {}

        # Compiled regex patterns
        self.compiled_patterns: Dict[str, List[re.Pattern]] = {}

        # Initialize word lists
        self._initialize_word_lists()

    def _initialize_word_lists(self):
        """Initialize word lists from file or defaults."""
        # Try to load from file
        if self.word_list_path and self.word_list_path.exists():
            try:
                with open(self.word_list_path, 'r') as f:
                    data = json.load(f)
                    self.word_lists = data.get("word_lists", {})
                    self._compile_all_patterns()
                return
            except Exception as e:
                print(f"Warning: Could not load word list from {self.word_list_path}: {e}")

        # Default word lists
        self.word_lists = {
            "profanity": {
                "mild": {"damn", "hell", "crap", "sucks"},
                "medium": {"ass", "bitch", "bastard", "piss"},
                "severe": {"fuck", "shit", "bullshit"}
            },
            "slurs": {
                "severe": set()  # Would be populated with actual slurs
            },
            "sexual": {
                "mild": {"sexy", "hot"},
                "medium": set(),
                "severe": set()
            },
            "violence": {
                "mild": {"hit", "punch", "kick"},
                "medium": {"kill", "murder", "assault"},
                "severe": {"torture", "massacre", "genocide"}
            }
        }

        # Merge custom patterns
        for category, patterns in self.custom_patterns.items():
            if category not in self.word_lists:
                self.word_lists[category] = {"medium": set()}
            if "custom" not in self.word_lists[category]:
                self.word_lists[category]["custom"] = set()
            self.word_lists[category]["custom"].update(patterns)

        self._compile_all_patterns()

    def _compile_all_patterns(self):
        """Compile regex patterns for all word lists."""
        self.compiled_patterns = {}

        for category, severity_levels in self.word_lists.items():
            self.compiled_patterns[category] = []
            for severity, words in severity_levels.items():
                if words:
                    # Create pattern that matches words with common obfuscations
                    # This handles things like f*ck, f.u.c.k, etc.
                    word_pattern = self._create_word_pattern(words)
                    self.compiled_patterns[category].append(word_pattern)

    def _create_word_pattern(self, words: Set[str]) -> re.Pattern:
        """Create a regex pattern that matches words with common obfuscations.

        Args:
            words: Set of words to create pattern for

        Returns:
            Compiled regex pattern
        """
        # Sort words by length (longest first) for proper matching
        sorted_words = sorted(words, key=len, reverse=True)

        # Escape special regex characters
        escaped_words = [re.escape(w) for w in sorted_words]

        # Create pattern that allows for:
        # - Letter substitution (f*ck -> [f@]ck)
        # - Separator insertion (b.a.s.t.a.r.d)
        # But not too permissive to avoid false positives
        pattern_parts = []
        for word in escaped_words:
            # Allow optional non-letter characters between letters
            flexible_pattern = ''.join([
                f'{char}[^a-zA-Z]*' if i < len(word) - 1 else char
                for i, char in enumerate(word)
            ])
            pattern_parts.append(flexible_pattern)

        full_pattern = r'\b(' + '|'.join(pattern_parts) + r')\b'
        return re.compile(full_pattern, re.IGNORECASE)

    async def check(
        self,
        content: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check content against word lists.

        Args:
            content: Text content to check
            categories: List of categories to check (default: all)

        Returns:
            Dictionary with check results including matches, severity,
            and recommended action
        """
        if categories is None:
            categories = list(self.word_lists.keys())

        results = {
            "flagged": False,
            "action": "allow",
            "matches": [],
            "category_results": {},
            "highest_severity": None
        }

        severity_order = {"mild": 1, "medium": 2, "severe": 3, "custom": 4}
        max_severity = 0

        for category in categories:
            if category not in self.word_lists:
                continue

            category_result = {
                "matches": [],
                "highest_severity": None,
                "severity_level": 0
            }

            for pattern in self.compiled_patterns.get(category, []):
                matches = pattern.findall(content)
                if matches:
                    for match in matches:
                        match_info = {
                            "category": category,
                            "text": match,
                            "position": content.lower().find(match.lower())
                        }
                        results["matches"].append(match_info)
                        category_result["matches"].append(match_info)

                        # Determine severity
                        for severity in ["severe", "custom", "medium", "mild"]:
                            if match.lower() in [w.lower() for w in self.word_lists[category].get(severity, set())]:
                                if severity_order[severity] > category_result["severity_level"]:
                                    category_result["severity_level"] = severity_order[severity]
                                    category_result["highest_severity"] = severity
                                if severity_order[severity] > max_severity:
                                    max_severity = severity_order[severity]
                                    results["highest_severity"] = severity
                                break

            results["category_results"][category] = category_result

        # Determine action based on severity
        if max_severity >= severity_order.get("severe", 3):
            results["action"] = "block"
            results["flagged"] = True
        elif max_severity >= severity_order.get("medium", 2):
            results["action"] = "flag"
            results["flagged"] = True
        elif max_severity >= severity_order.get("mild", 1):
            results["action"] = "warn"
            results["flagged"] = True

        return results

    async def get_match_positions(
        self,
        content: str,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get positions of all matches in content.

        Args:
            content: Text content to search
            categories: Categories to check (default: all)

        Returns:
            List of match info dictionaries with positions
        """
        result = await self.check(content, categories)
        return result["matches"]

    async def get_matched_terms(
        self,
        content: str,
        categories: Optional[List[str]] = None
    ) -> Set[str]:
        """Get set of all matched terms.

        Args:
            content: Text content to search
            categories: Categories to check (default: all)

        Returns:
            Set of matched term strings
        """
        matches = await self.get_match_positions(content, categories)
        return {m["text"].lower() for m in matches}

    async def filter_content(
        self,
        content: str,
        filter_char: str = "*",
        categories: Optional[List[str]] = None
    ) -> str:
        """Filter content by replacing matched words with filter character.

        Args:
            content: Text content to filter
            filter_char: Character to replace filtered words with
            categories: Categories to filter (default: all)

        Returns:
            Filtered content string
        """
        matches = await self.get_match_positions(content, categories)

        # Sort matches by position (reverse order to avoid offset issues)
        matches_sorted = sorted(matches, key=lambda m: m["position"], reverse=True)

        filtered_content = content
        for match in matches_sorted:
            pos = match["position"]
            text = match["text"]
            # Find actual occurrence in content (case-sensitive)
            actual_pos = filtered_content.find(text, pos, pos + len(text) + 10)
            if actual_pos != -1:
                end_pos = actual_pos + len(text)
                filtered_content = (
                    filtered_content[:actual_pos] +
                    filter_char * len(text) +
                    filtered_content[end_pos:]
                )

        return filtered_content

    def add_custom_words(self, category: str, words: List[str], severity: str = "medium"):
        """Add custom words to a category.

        Args:
            category: Category to add words to
            words: List of words to add
            severity: Severity level for the words
        """
        if category not in self.word_lists:
            self.word_lists[category] = {}
        if severity not in self.word_lists[category]:
            self.word_lists[category][severity] = set()

        self.word_lists[category][severity].update(words)
        self._compile_all_patterns()

    def remove_words(self, category: str, words: List[str]):
        """Remove words from a category.

        Args:
            category: Category to remove words from
            words: List of words to remove
        """
        if category in self.word_lists:
            for severity_levels in self.word_lists[category].values():
                severity_levels.difference_update(words)
            self._compile_all_patterns()

    def save_word_list(self, path: Optional[Path] = None):
        """Save current word lists to file.

        Args:
            path: Path to save to (default: original word_list_path)
        """
        save_path = path or self.word_list_path
        if not save_path:
            raise ValueError("No save path specified")

        # Convert sets to lists for JSON serialization
        serializable_lists = {}
        for category, severity_levels in self.word_lists.items():
            serializable_lists[category] = {
                severity: list(words)
                for severity, words in severity_levels.items()
            }

        data = {"word_lists": serializable_lists}

        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
