"""Reporting module for Chimera Simulation Engine.

This module provides structured reporting capabilities including:
- ForumEngine: Multi-agent debate system for consensus building
- Report generation with confidence scoring
"""

from .models import Argument, DebateResult
from .forum_engine import ForumEngine

__all__ = ['Argument', 'DebateResult', 'ForumEngine']
