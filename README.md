# QA Intelligence MCP Server

Production-oriented Azure DevOps MCP Server that behaves like an experienced QA engineer: analyze user stories, detect coverage gaps and duplicates, and create only meaningful test cases.

## Stack

- Python 3.12
- FastMCP
- FastAPI (health/readiness only)
- Pydantic / pydantic-settings
- Structlog
- Pytest
- Repository pattern · Service layer · Dependency injection · Async I/O

## Documentation

Architecture lives in [`docs/`](./docs/README.md).

## Setup (once)

### 1. Install dependencies

```bash
cd Desktop\MCP-TC
python -m pip install -e ".[dev]"
```

Or with uv:

```bash
uv sync --all-extras
```

### 2. Add Azure DevOps credentials

Copy the template and fill values (never commit secrets):

```bash
copy .env.example .env
```

Required in `.env`:

```text
ADO_ORGANIZATION=your-org
ADO_PROJECT=your-project
ADO_PAT=your-pat
```

PAT needs Work Items read/write (and Test Management if using suites).

### 3. Cursor MCP is already configured

Project file: [`.cursor/mcp.json`](./.cursor/mcp.json)

Restart Cursor (or reload MCP servers). You should see **qa-intelligence** with 9 tools.

### 4. Generate test cases

In Cursor chat:

```text
Generate missing test cases for ADO User Story 73230 via QA Intelligence MCP: analyze first (stop if blocked), inventory + coverage, draft only missing scenarios with title/steps/expected_results 1:1, dry-run create, then create + link after approval.
```

## Run manually

```bash
set PYTHONPATH=src
python -m qa_intelligence.main
```

## MCP tools

| Tool | Purpose |
|------|---------|
| `get_user_story` | Fetch user story |
| `get_existing_test_cases` | Inventory linked tests |
| `search_similar_test_cases` | Project similarity search |
| `get_related_bugs` | Related bugs |
| `analyze_requirement` | QA Strategy + gaps |
| `detect_duplicate_test_cases` | Semantic duplicates |
| `generate_coverage_report` | Coverage + missing scenarios |
| `create_test_cases` | Validate + create |
| `link_test_cases` | Link cases to story |

## Development

```bash
set PYTHONPATH=src
python -m pytest
```

## License

Proprietary.
