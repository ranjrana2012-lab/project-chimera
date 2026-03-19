# services/nemoclaw-orchestrator/policy/filters.py
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class InputSanitizer:
    """Sanitizes input data to remove harmful content"""

    def __init__(self, max_length: int = 5000):
        self.max_length = max_length
        # Simple profanity list (expand in production)
        # Match both explicit words and words with wildcard substitutions
        self.profanity_pattern = re.compile(
            r'\b(f\*+(?:ck|ing?)?|f[*]{3,}ing|s\*+t|s\*+t|d\*+n|[a@]ss|a\*\*|b\*+tch|fuck|shit|damn|ass|bitch)\b',
            re.IGNORECASE
        )

    async def sanitize(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        result = {}

        for key, value in input_data.items():
            if isinstance(value, str):
                # Remove profanity
                sanitized = self.profanity_pattern.sub('***', value)
                # Truncate if too long (account for "..." suffix)
                if len(sanitized) > self.max_length:
                    sanitized = sanitized[:self.max_length - 3] + "..."
                result[key] = sanitized
            elif isinstance(value, dict):
                result[key] = await self.sanitize(value)
            elif isinstance(value, list):
                result[key] = [
                    await self.sanitize(item) if isinstance(item, (dict, str))
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

class OutputFilter:
    """Filters agent output to remove sensitive information"""

    def __init__(self):
        # PII patterns (expand in production)
        self.phone_pattern = re.compile(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        )
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.ssn_pattern = re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        )

    async def filter(
        self,
        response: Dict[str, Any],
        agent: str
    ) -> Dict[str, Any]:
        """Filter output data"""
        result = {}

        for key, value in response.items():
            if isinstance(value, str):
                # Remove PII
                filtered = self.phone_pattern.sub('[PHONE]', value)
                filtered = self.email_pattern.sub('[EMAIL]', filtered)
                filtered = self.ssn_pattern.sub('[SSN]', filtered)
                result[key] = filtered
            elif isinstance(value, dict):
                result[key] = await self.filter(value, agent)
            elif isinstance(value, list):
                result[key] = [
                    await self.filter(item, agent) if isinstance(item, (dict, str))
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result
