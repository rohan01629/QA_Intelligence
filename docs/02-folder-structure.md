# 02 — Folder Structure

**Product:** QA Intelligence MCP Server  

---

## 1. Design Intent

The layout enforces:

- Thin MCP adapters  
- Fat, testable services and domain  
- ADO details isolated behind repository ports  
- Optional Code Intelligence over a **local** application tree (read-only)  
- Docs versioned with the product  

This tree matches the **implemented** package under `src/qa_intelligence/`.

---

## 2. Implemented Tree

```text
MCP-TC/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── .cursor/
│   └── mcp.json                       # Cursor MCP server registration
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   └── 01…16-*.md
├── src/
│   └── qa_intelligence/
│       ├── __init__.py
│       ├── main.py                    # process entry (MCP bootstrap)
│       ├── api/
│       │   └── health.py              # FastAPI health/ready only
│       ├── mcp/
│       │   ├── server.py              # FastMCP app + registration
│       │   ├── runtime.py             # DI container accessor
│       │   ├── responses.py / parsers.py
│       │   ├── tools/                 # one module per tool (thin)
│       │   │   ├── get_user_story.py
│       │   │   ├── get_existing_test_cases.py
│       │   │   ├── search_similar_test_cases.py
│       │   │   ├── get_related_bugs.py
│       │   │   ├── analyze_requirement.py
│       │   │   ├── analyze_codebase.py
│       │   │   ├── detect_duplicate_test_cases.py
│       │   │   ├── generate_coverage_report.py
│       │   │   ├── create_test_cases.py
│       │   │   └── link_test_cases.py
│       │   └── schemas/
│       ├── domain/
│       │   ├── models/                # incl. code_intelligence.py, orchestration.py
│       │   ├── enums.py
│       │   ├── similarity.py
│       │   ├── policies/              # category, risk, gap, product_rules, …
│       │   └── validation/            # format + duplicate guard
│       ├── services/
│       │   ├── story_service.py
│       │   ├── test_case_service.py
│       │   ├── bug_service.py
│       │   ├── requirement_analysis_service.py
│       │   ├── duplicate_detection_service.py
│       │   ├── coverage_analysis_service.py
│       │   ├── test_strategy_service.py
│       │   ├── test_case_generation_service.py
│       │   ├── linking_service.py
│       │   ├── orchestration_service.py
│       │   ├── code_intelligence_service.py
│       │   ├── ado_git_repository_service.py
│       │   ├── repository_search_service.py
│       │   ├── impact_analysis_service.py
│       │   └── implementation_summary_builder.py
│       ├── repositories/
│       │   ├── protocols.py
│       │   ├── user_story_repository.py
│       │   ├── test_case_repository.py
│       │   └── bug_repository.py
│       ├── infrastructure/
│       │   ├── ado/                   # client, auth, mappers
│       │   ├── config.py
│       │   ├── logging.py
│       │   ├── di.py
│       │   └── errors.py
│       └── prompts/
│           └── analysis_guidance.py
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── fixtures/
```

---

## 3. Module Boundaries

| Path | May depend on | Must not depend on |
|------|---------------|--------------------|
| `mcp/tools` | services, mcp/schemas | ADO client directly |
| `services` | domain, repository protocols, local FS (Code Intel only) | FastMCP, FastAPI |
| `domain` | stdlib, pydantic | services, repos, MCP, ADO |
| `repositories` | domain, infrastructure/ado | mcp, services (circular) |
| `infrastructure` | config, external libs | domain business policies |
| `api/health` | config, di readiness checks | domain write paths |

Code Intelligence services read the filesystem under `repository_path` only; they never write to the application repo or to ADO.

---

## 4. Package Naming

- Distribution / import root: `qa_intelligence`  
- Workspace directory: `MCP-TC` (local); GitHub remote may use `QA_Intelligence`  

---

## 5. Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata, deps, pytest |
| `.env.example` | Documented env keys; no secrets |
| `.env` | Local secrets (gitignored) |
| `.cursor/mcp.json` | Cursor MCP launch (`python -m qa_intelligence.main`) |

Optional Code Intelligence defaults: `ADO_DEFAULT_GIT_REPOSITORY`, `ADO_DEFAULT_GIT_BRANCH`, `CODE_INTEL_CACHE_DIR`.

---

## Related

- [04-component-diagram.md](./04-component-diagram.md)  
- [08-repository-layer.md](./08-repository-layer.md)  
- [09-service-layer.md](./09-service-layer.md)  
