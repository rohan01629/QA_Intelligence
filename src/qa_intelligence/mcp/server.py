"""FastMCP application construction and tool registration."""

from __future__ import annotations

from fastmcp import FastMCP

from qa_intelligence.mcp.tools import TOOL_HANDLERS

SERVER_NAME = "qa-intelligence"
SERVER_INSTRUCTIONS = (
    "QA Intelligence MCP Server for Azure DevOps. "
    "Use these tools to fetch a user story, analyze requirements into a QA Strategy, "
    "optionally analyze application source with analyze_codebase "
    "(local repository_path and/or ado_repository + ado_branch from Azure Repos — READ ONLY), "
    "inventory existing tests and bugs, detect coverage gaps and duplicates, "
    "then draft meaningful missing test cases. "
    "SAFETY: Never push to Azure Repos. Never create/link work items unless the user "
    "explicitly approves AND ADO_WRITES_ENABLED=true; default create/link to dry_run=true. "
    "Never generate optional categories without evidence. "
    "Test cases must contain only title, steps, and expected_results "
    "with matching step/expected counts. "
    "Credentials: set ADO_ORGANIZATION, ADO_PROJECT, ADO_PAT in .env "
    "(Code Read for clones; Work Items write only if publishes are enabled)."
)


def create_mcp_server() -> FastMCP:
    """Create the FastMCP server and register the closed tool surface."""
    mcp_app = FastMCP(
        name=SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
    )
    register_tools(mcp_app)
    return mcp_app


def register_tools(mcp_app: FastMCP) -> None:
    """Register all QA Intelligence tools on the given FastMCP instance."""
    for handler in TOOL_HANDLERS:
        mcp_app.tool(handler, name=handler.__name__)


# Module-level server instance for `fastmcp run` / entrypoints.
mcp = create_mcp_server()
