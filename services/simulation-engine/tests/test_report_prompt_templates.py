"""Unit tests for reporting prompt templates."""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporting.prompt_templates import PromptTemplates


class TestPromptTemplates:
    """Test PromptTemplates with safe context access."""

    def test_executive_summary_with_complete_context(self):
        """Test executive summary prompt with complete context."""
        templates = PromptTemplates()
        context = {
            'topic': 'Test Topic',
            'simulation_id': 'sim123',
            'total_rounds': 5,
            'total_actions': 20,
            'recent_actions': [
                {'agent': 'agent1', 'action': 'post', 'content': 'Test content'}
            ],
            'entities': ['entity1', 'entity2']
        }

        prompt = templates._executive_summary_prompt(context)

        assert 'Test Topic' in prompt
        assert 'sim123' in prompt
        assert '5' in prompt
        assert '20' in prompt
        assert 'agent1' in prompt

    def test_executive_summary_with_missing_context(self):
        """Test executive summary prompt with missing context (KeyError safety)."""
        templates = PromptTemplates()
        context = {}  # Empty context

        prompt = templates._executive_summary_prompt(context)

        # Should use defaults instead of raising KeyError
        assert 'Unknown Topic' in prompt
        assert 'Unknown' in prompt
        assert '0' in prompt  # total_rounds and total_actions

    def test_key_findings_with_complete_context(self):
        """Test key findings prompt with complete context."""
        templates = PromptTemplates()
        context = {
            'topic': 'Test Topic',
            'recent_actions': [
                {'agent': 'agent1', 'action': 'post', 'content': 'Test content'}
            ],
            'entities': ['entity1', 'entity2', 'entity3']
        }

        prompt = templates._key_findings_prompt(context)

        assert 'Test Topic' in prompt
        assert 'agent1' in prompt
        assert 'entity1' in prompt

    def test_key_findings_with_missing_context(self):
        """Test key findings prompt with missing context."""
        templates = PromptTemplates()
        context = {}  # Empty context

        prompt = templates._key_findings_prompt(context)

        # Should use defaults instead of raising KeyError
        assert 'Unknown Topic' in prompt

    def test_recommendations_with_complete_context(self):
        """Test recommendations prompt with complete context."""
        templates = PromptTemplates()
        context = {
            'topic': 'Test Topic'
        }

        prompt = templates._recommendations_prompt(context)

        assert 'Test Topic' in prompt
        assert 'recommendations' in prompt.lower()

    def test_recommendations_with_missing_context(self):
        """Test recommendations prompt with missing context."""
        templates = PromptTemplates()
        context = {}  # Empty context

        prompt = templates._recommendations_prompt(context)

        # Should use defaults instead of raising KeyError
        assert 'Unknown Topic' in prompt

    def test_format_actions_with_safe_actions(self):
        """Test formatting actions with safe content."""
        templates = PromptTemplates()
        actions = [
            {'agent': 'agent1', 'action': 'post', 'content': 'Safe content'},
            {'agent': 'agent2', 'action': 'reply', 'content': 'Another safe content'}
        ]

        formatted = templates._format_actions(actions)

        assert 'agent1' in formatted
        assert 'agent2' in formatted
        assert 'Safe content' in formatted
        assert 'post' in formatted
        assert 'reply' in formatted

    def test_format_actions_with_xss_attempt(self):
        """Test that actions are sanitized to prevent XSS."""
        templates = PromptTemplates()
        actions = [
            {
                'agent': 'attacker',
                'action': 'post',
                'content': '<script>alert("XSS")</script>'
            }
        ]

        formatted = templates._format_actions(actions)

        # Should be HTML escaped
        assert '<script>' not in formatted
        assert '&lt;script&gt;' in formatted
        assert 'attacker' in formatted

    def test_format_actions_with_empty_actions(self):
        """Test formatting with no actions."""
        templates = PromptTemplates()
        formatted = templates._format_actions([])

        assert formatted == "No actions available."

    def test_format_actions_with_missing_fields(self):
        """Test formatting actions with missing fields."""
        templates = PromptTemplates()
        actions = [
            {'agent': 'agent1'},  # Missing action and content
            {'action': 'post'},  # Missing agent and content
            {}  # Empty dict
        ]

        formatted = templates._format_actions(actions)

        assert 'agent1' in formatted
        assert 'Unknown' in formatted
        assert 'unknown' in formatted

    def test_format_actions_limits_to_five(self):
        """Test that only 5 actions are formatted."""
        templates = PromptTemplates()
        actions = [
            {'agent': f'agent{i}', 'action': 'post', 'content': f'Content {i}'}
            for i in range(10)
        ]

        formatted = templates._format_actions(actions)

        # Should only include first 5
        assert 'agent0' in formatted
        assert 'agent4' in formatted
        assert 'agent5' not in formatted
        assert 'agent9' not in formatted

    def test_default_prompt_with_complete_context(self):
        """Test default prompt with complete context."""
        templates = PromptTemplates()
        context = {'topic': 'Test Topic'}

        prompt = templates._default_prompt(context)

        assert 'Test Topic' in prompt

    def test_default_prompt_with_missing_context(self):
        """Test default prompt with missing context."""
        templates = PromptTemplates()
        context = {}  # Empty context

        prompt = templates._default_prompt(context)

        # Should use defaults instead of raising KeyError
        assert 'Unknown Topic' in prompt

    def test_get_prompt_delegation(self):
        """Test that get_prompt correctly delegates to specific methods."""
        templates = PromptTemplates()
        context = {
            'topic': 'Test',
            'simulation_id': 'sim1',
            'total_rounds': 1,
            'total_actions': 1,
            'recent_actions': [],
            'entities': []
        }

        # Test each section type
        exec_prompt = templates.get_prompt('executive_summary', context)
        assert 'Executive Summary' in exec_prompt or 'executive summary' in exec_prompt.lower()

        findings_prompt = templates.get_prompt('key_findings', context)
        assert 'key findings' in findings_prompt.lower()

        rec_prompt = templates.get_prompt('recommendations', context)
        assert 'recommendations' in rec_prompt.lower()

        # Test unknown section type
        default_prompt = templates.get_prompt('unknown_section', context)
        assert 'Test' in default_prompt
