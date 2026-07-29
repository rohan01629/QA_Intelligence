# QA Intelligence MCP Server — Architecture Summary

**Status:** Architecture documentation complete — awaiting approval before implementation  
**Version:** 0.2.0-arch  

This file is a **consolidated summary**. The authoritative, detailed design lives in the numbered documents listed in [README.md](./README.md).

---

## System in one paragraph

Cursor orchestrates a 15-step QA workflow. The MCP server (FastMCP + services + domain) fetches Azure DevOps data, emits a **QA Strategy**, detects duplicates and coverage gaps, hard-validates test cases (exactly three fields; steps ↔ expected results 1:1), and creates/links only meaningful Test Cases. The LLM drafts; the server decides scope and enforces quality. Exactly **nine** MCP tools; no generic ADO CRUD.

---

## Document map

| # | Topic | Doc |
|---|-------|-----|
| 1 | High-Level Architecture | [01-high-level-architecture.md](./01-high-level-architecture.md) |
| 2 | Folder Structure | [02-folder-structure.md](./02-folder-structure.md) |
| 3 | MCP Tool Design | [03-mcp-tool-design.md](./03-mcp-tool-design.md) |
| 4 | Component Diagram | [04-component-diagram.md](./04-component-diagram.md) |
| 5 | Sequence Diagram | [05-sequence-diagram.md](./05-sequence-diagram.md) |
| 6 | Data Flow | [06-data-flow.md](./06-data-flow.md) |
| 7 | Domain Models | [07-domain-models.md](./07-domain-models.md) |
| 8 | Repository Layer | [08-repository-layer.md](./08-repository-layer.md) |
| 9 | Service Layer | [09-service-layer.md](./09-service-layer.md) |
| 10 | Validation Layer | [10-validation-layer.md](./10-validation-layer.md) |
| 11 | Azure DevOps Integration | [11-azure-devops-integration.md](./11-azure-devops-integration.md) |
| 12 | LLM Interaction Flow | [12-llm-interaction-flow.md](./12-llm-interaction-flow.md) |
| 13 | Future Scalability | [13-future-scalability.md](./13-future-scalability.md) |
| 14 | Error Handling Strategy | [14-error-handling-strategy.md](./14-error-handling-strategy.md) |
| 15 | Logging Strategy | [15-logging-strategy.md](./15-logging-strategy.md) |
| 16 | Testing Strategy | [16-testing-strategy.md](./16-testing-strategy.md) |

---

## Closed tool surface

1. `get_user_story`  
2. `get_existing_test_cases`  
3. `search_similar_test_cases`  
4. `get_related_bugs`  
5. `analyze_requirement`  
6. `detect_duplicate_test_cases`  
7. `generate_coverage_report`  
8. `create_test_cases`  
9. `link_test_cases`  

---

## Key architectural decisions (v1)

| ID | Decision |
|----|----------|
| D1 | Cursor LLM drafts test cases; MCP validates/creates (no generate tool) |
| D2 | FastAPI = health/readiness only |
| D3 | ADO auth = PAT via AuthProvider port |
| D4 | Create = per-item results + dry_run |
| D5 | Duplicates = deterministic semantic scorer; embeddings later behind same port |
| D6 | Blocking gaps block generation; explicit override for Test Leads |
| D7 | Optional default Test Plan/Suite; else WI + story link |

---

## QA Strategy (golden example)

- Feature Type: Backend API · Risk: High  
- Required: Positive, Negative, Edge, Validation, API, Integration, Regression  
- Not required: UI, Accessibility, Database, Performance  
- Reason: backend API behavior only — no UI/DB changes  
- Estimates: 18 new · 32 existing · 14 duplicates  

---

## Implementation gate

**No application code until architecture approval.**

Post-approval module order: M1 skeleton → M2 domain/validation → M3 ADO read repos → M4 read tools → M5 analysis/coverage → M6 write path → M7 contracts/runbook → M8 hardening.
