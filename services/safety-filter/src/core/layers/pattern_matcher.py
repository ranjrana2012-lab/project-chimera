"""Pattern matching layer for safety filtering"""

import re
from typing import Dict, Any, List


class PatternMatcher:
    def __init__(self):
        self.patterns = {
            "profanity": [
                r"\b(fuck|shit|damn|hell)\b",
                # Add more patterns as needed
            ],
            "hate_speech": [
                r"\b(hate|kill)\s+\w+(?:because|due to|for)\s+(?:race|gender|religion)",
                # Add more patterns as needed
            ],
            "explicit_content": [
                r"\b(naked|nude|explicit)\b",
                # Add more patterns as needed
            ],
        }
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns."""
        self.compiled = {}
        for category, patterns in self.patterns.items():
            self.compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]

    async def check(self, content: str) -> Dict[str, Any]:
        """Check content against patterns."""
        matches = []
        action = "allow"

        for category, patterns in self.compiled.items():
            for pattern in patterns:
                if pattern.search(content):
                    matches.append({
                        "category": category,
                        "match": pattern.search(content).group(),
                    })
                    if category in ["hate_speech", "explicit_content"]:
                        action = "block"
                    elif action != "block":
                        action = "flag"

        return {
            "action": action,
            "matches": matches,
        }
