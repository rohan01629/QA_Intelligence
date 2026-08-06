# QA Intelligence MCP Server

Production-oriented Azure DevOps MCP Server that behaves like an experienced QA engineer: analyze user stories, optionally ground them in a local application codebase, detect coverage gaps and duplicates, and create only meaningful test cases.

## Stack

- Python 3.12+
- FastMCP
- FastAPI (health/readiness only)
- Pydantic / pydantic-settings
- Structlog
- Pytest
- Repository pattern · Service layer · Dependency injection · Async I/O

## Documentation

Architecture lives in [`docs/`](./docs/README.md). Start with [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

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

## Generation volume (Rule 11)

| Setting | Default | Meaning |
|---------|---------|---------|
| `MIN_GENERATED_TEST_CASES` | 25 | Typical / short fresh suite target |
| `TARGET_COMPLEX_TEST_CASES` | 50 | Only when story is complex |
| `MAX_GENERATED_TEST_CASES` | 60 | Hard cap per generation pass |

**Complex** means high/critical risk, 3+ AC items, 4+ `Scenario N:` markers, long AC text, or 8+ native uncovered scenarios — not volume-seed padding.

Local Code Intelligence roots (story picks best match via `CODE_INTEL_LOCAL_REPOSITORY_PATHS`):

- `D:\Live_Plus_UAT`
- `C:\Users\WalkingTree.LAPTOP-UNM23JON\Desktop\Minifrac\fracpro-agile`

**Rule 12:** If the US feature is **not implemented**, analyze related/previous code and **ask before generating**. Related-based TCs are optional (`allow_related_implementation=true` after user approval). If neither the feature nor related code exists, do not generate.

**Rule 13 mix:** After generation, classify ~**30%** Regression and ~**10%** Critical by impact/importance/risk (not random slotting); report by TC number, not in titles.

| Guard | Default |
|-------|---------|
| `ADO_WRITES_ENABLED` | `false` — create/link refuse real writes |
| `create_test_cases` / `link_test_cases` | `dry_run=true` |
| `OrchestrationService` | `dry_run=true`, `publish=false` |
| Code Intelligence Git | **clone/fetch only** — never push; push URL disabled in cache |

To publish for real (only after your approval): set `ADO_WRITES_ENABLED=true`, then call create/link with `dry_run=false`. Prefer a PAT with **Code Read** (not Code Write) and Work Items write only when you intentionally publish.

### 3. Cursor MCP is already configured

Project file: [`.cursor/mcp.json`](./.cursor/mcp.json)

Restart Cursor (or reload MCP servers). You should see **qa-intelligence** with **10** tools.

### 4. Generate test cases

In Cursor chat (ADO-only):

```text
Generate missing test cases for ADO User Story 73230 via QA Intelligence MCP: analyze first (stop if blocked), inventory + coverage, draft only missing scenarios with title/steps/expected_results 1:1, dry-run create, then create + link after approval.
```

Implementation-aware via Azure Repos (latest branch — no local pull required):

```text
Generate missing test cases for ADO User Story 73230 via QA Intelligence MCP.
Call analyze_codebase with ado_repository=<Azure Repo name> and ado_branch=main
(or rely on ADO_DEFAULT_GIT_REPOSITORY in .env).
Use Implementation Summary + QA Strategy; draft only missing scenarios.
Dry-run create; create + link only after my approval.
```

Or local WIP path:

```text
Generate missing test cases for ADO User Story 73230 via QA Intelligence MCP.
Call analyze_codebase with repository_path pointing at the application codebase.
Use Implementation Summary + QA Strategy; draft only missing scenarios.
Dry-run create; create + link after approval.
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
| `analyze_codebase` | Local repo → Implementation Summary |
| `detect_duplicate_test_cases` | Semantic duplicates |
| `generate_coverage_report` | Coverage + missing scenarios |
| `create_test_cases` | Validate + create |
| `link_test_cases` | Link cases to story |

## Code Intelligence

Optional path — provide at least one source:

| Source | How | When to use |
|--------|-----|-------------|
| **Local** | `repository_path=D:\Live_Plus_UAT` | Uncommitted WIP on your machine |
| **Azure Repos** | `ado_repository=YourRepo` + optional `ado_branch` | Latest shared branch without manual pull |

```text
analyze_codebase(
  user_story_id=73230,
  ado_repository="LivePlus",
  ado_branch="main"
)
```

Defaults (optional in `.env`):

```text
ADO_DEFAULT_GIT_REPOSITORY=LivePlus
ADO_DEFAULT_GIT_BRANCH=main
```

PAT needs **Code (Read)** in addition to Work Items. Checkouts are shallow-cloned into a local cache (`~/.cache/qa_intelligence/ado_git` or `CODE_INTEL_CACHE_DIR`). If both local and ADO are set, **Azure Repos wins**.

## Development

```bash
set PYTHONPATH=src
python -m pytest
```

## License

Proprietary.
