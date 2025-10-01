"""
AI Agents package for Natural Language SQL query generation
"""

# Only import what's available to avoid dependency issues
try:
    from .mcp_agent import NaturalLanguageSQLAgent
    __all__ = ['NaturalLanguageSQLAgent']
except ImportError:
    __all__ = []
