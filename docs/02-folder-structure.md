# 02 — Folder Structure

**Product:** QA Intelligence MCP Server  

---

## 1. Design Intent

The layout enforces:

- Thin MCP adapters  
- Fat, testable services and domain  
- ADO details isolated behind repository ports  
- Docs and ADRs versioned with the product  

No implementation code is present yet; this is the **target** structure after Module M1+.

---

## 2. Target Tree

```text
qa-intelligence-mcp/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── README.md                          # Documentation index
│   ├── 01-high-level-architecture.md
│   ├── 02-folder-structure.md             # this file
│   ├── 03-mcp-tool-design.md
│   ├── 04-component-diagram.md
│   ├── 05-sequence-diagram.md
│   ├── 06-data-flow.md
│   ├── 07-domain-models.md
│   ├── 08-repository-layer.md
│   ├── 09-service-layer.md
│   ├── 10-validation-layer.md
│   ├── 11-azure-devops-integration.md
│   ├── 12-llm-interaction-flow.md
│   ├── 13-future-scalability.md
│   ├── 14-error-handling-strategy.md
│   ├── 15-logging-strategy.md
│   ├── 16-testing-strategy.md
│   ├── ARCHITECTURE.md                    # consolidated summary
│   └── ADRs/                              # architecture decision records
│       └── .gitkeep
├── src/
│   └── qa_intelligence/
│       ├── __init__.py
│       ├── main.py                        # process entry (MCP bootstrap)
│       ├── api/
│       │   └── health.py                  # FastAPI health/ready only
│       ├── mcp/
│       │   ├── server.py                  # FastMCP app + registration
│       │   ├── tools/                     # one module per tool (thin)
│       │   │   ├── get_user_story.py
│       │   │   ├── get_existing_test_cases.py
│       │   │   ├── search_similar_test_cases.py
│       │   │   ├── get_related_bugs.py
│       │   │   ├── analyze_requirement.py
│       │   │   ├── detect_duplicate_test_cases.py
│       │   │   ├── generate_coverage_report.py
│       │   │   ├── create_test_cases.py
│       │   │   └── link_test_cases.py
│       │   └── schemas/                   # MCP request/response DTOs
│       ├── domain/
│       │   ├── models/
│       │   ├── enums.py
│       │   ├── policies/                  # category applicability, risk
│       │   └── validation/                # format & invariant validators
│       ├── services/
│       │   ├── story_service.py
│       │   ├── test_case_service.py
│       │   ├── bug_service.py
│       │   ├── analysis_service.py
│       │   ├── duplicate_service.py
│       │   ├── coverage_service.py
│       │   └── linking_service.py
│       ├── repositories/
│       │   ├── protocols.py               # ports
│       │   ├── ado_work_item_repository.py
│       │   ├── ado_test_case_repository.py
│       │   └── ado_query_repository.py
│       ├── infrastructure/
│       │   ├── ado/
│       │   │   ├── client.py
│       │   │   ├── auth.py
│       │   │   └── mappers.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   ├── di.py
│       │   └── errors.py
│       └── prompts/                       # optional guidance fragments for tool outputs
│           └── analysis_guidance.py
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    ├── golden/
    └── fixtures/
```

---

## 3. Module Boundaries

| Path | May depend on | Must not depend on |
|------|---------------|--------------------|
| `mcp/tools` | services, mcp/schemas | ADO client directly |
| `services` | domain, repository protocols | FastMCP, FastAPI |
| `domain` | stdlib, pydantic | services, repos, MCP, ADO |
| `repositories` | domain, infrastructure/ado | mcp, services (circular) |
| `infrastructure` | config, external libs | domain business policies |
| `api/health` | config, di readiness checks | domain write paths |

---

## 4. Package Naming

- Distribution / import root: `qa_intelligence`  
- Project directory name may remain `MCP-TC` or rename to `qa-intelligence-mcp` at scaffold time (ADR).  

---

## 5. Configuration Files (planned)

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv, deps, pytest, ruff/mypy tool config |
| `.env.example` | Documented env keys; no secrets |
| `docs/ADRs/*` | One decision per file (auth, duplicate scorer, suite placement) |

---

## Related

- [04-component-diagram.md](./04-component-diagram.md)  
- [08-repository-layer.md](./08-repository-layer.md)  
- [09-service-layer.md](./09-service-layer.md)  
