"""Reporting module for Chimera Simulation Engine.

This module provides structured reporting capabilities including:
- ForumEngine: Multi-agent debate system for consensus building
- ReACTReportAgent: Comprehensive report generation using ReACT pattern
- Report generation with confidence scoring
"""

from .models import (
    Argument, DebateResult,
    SimulationAction, SimulationRound, SimulationTrace,
    ReportSection, Report
)
from .forum_engine import ForumEngine
from .react_agent import ReACTReportAgent

__all__ = [
    'Argument', 'DebateResult',
    'SimulationAction', 'SimulationRound', 'SimulationTrace',
    'ReportSection', 'Report',
    'ForumEngine', 'ReACTReportAgent'
]
