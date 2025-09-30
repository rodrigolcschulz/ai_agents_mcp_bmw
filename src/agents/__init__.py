"""
AI Agents package for SQL query generation and MCP communication
"""

# Only import what's available to avoid dependency issues
try:
    from .mcp_agent import MCPAgent
    __all__ = ['MCPAgent']
except ImportError:
    __all__ = []
