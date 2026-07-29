"""FastMCP transport package."""

from __future__ import annotations

from qa_intelligence.mcp.server import create_mcp_server, mcp, register_tools

__all__ = [
    "create_mcp_server",
    "mcp",
    "register_tools",
]
