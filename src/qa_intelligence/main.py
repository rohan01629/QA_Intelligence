"""Process entry point for the QA Intelligence MCP Server."""

from __future__ import annotations

import os

from qa_intelligence.infrastructure.logging import configure_logging
from qa_intelligence.mcp.server import create_mcp_server


def main() -> None:
    """Bootstrap and run the FastMCP server (stdio by default)."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(log_level)

    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
    mcp = create_mcp_server()

    # FastMCP.run accepts transport name; default stdio for Cursor MCP.
    if transport in {"sse", "http"}:
        mcp.run(transport=transport)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
