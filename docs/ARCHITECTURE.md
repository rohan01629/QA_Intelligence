# QA Intelligence MCP Server — Architecture Summary

**Status:** Implemented (v0.1.0)  
**Version:** 0.1.0  

This file is a **consolidated summary** of the running system. Detailed design lives in the numbered documents listed in [README.md](./README.md).

---

## System in one paragraph

Cursor (or the in-process `OrchestrationService`) drives a QA workflow. The MCP server (FastMCP + services + domain) fetches Azure DevOps data, emits a **QA Strategy**, optionally runs **Code Intelligence** against a local application repository, detects duplicates and coverage gaps, hard-validates test cases (exactly three fields; steps ↔ expected results 1:1), and creates/links only meaningful Test Cases. Exactly **ten** MCP tools; no generic ADO CRUD. Code Intelligence is additive: omit `repository_path` and behavior matches the ADO-only path.

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

## Closed tool surface (10)

1. `get_user_story`  
2. `get_existing_test_cases`  
3. `search_similar_test_cases`  
4. `get_related_bugs`  
5. `analyze_requirement`  
6. `analyze_codebase` — optional Code Intelligence (local `repository_path`)  
7. `detect_duplicate_test_cases`  
8. `generate_coverage_report`  
9. `create_test_cases`  
10. `link_test_cases`  

---

## Code Intelligence (additive)

Provide a source via local path and/or Azure Repos:

1. **Azure Repos** (`ado_repository` + optional `ado_branch` / `ado_project`, or `.env` defaults) → shallow clone/refresh into cache → analyze tip of branch.  
2. **Local** (`repository_path`) → analyze files on disk (includes WIP).  
3. If both are set, **Azure Repos wins** (shared “latest”); use local-only for uncommitted work.  

Then:

1. `RepositorySearchService` infers search terms from the story (and bugs) and ranks source files.  
2. `ImpactAnalysisService` extracts APIs, validation rules, permissions, UI, DB, flags, integrations.  
3. `ImplementationSummaryBuilder` produces an `ImplementationSummary` (includes `source_kind`, repo/branch/commit when ADO).  
4. `TestCaseGenerationService` may enrich missing scenarios from that summary.  

If analysis finds weak or no matches, treat the summary as a signal of **implementation gaps** vs the story — do not invent coverage from empty results.

PAT for ADO Git requires **Code Read**. Git must be installed on PATH.

---

## Key architectural decisions (v1)

| ID | Decision |
|----|----------|
| D1 | Cursor LLM and/or `TestCaseGenerationService` draft cases; MCP validates/creates |
| D2 | FastAPI = health/readiness only |
| D3 | ADO auth = PAT via AuthProvider port |
| D4 | Create = per-item results + dry_run |
| D5 | Duplicates = deterministic semantic scorer; embeddings later behind same port |
| D6 | Blocking gaps block generation; explicit override for Test Leads |
| D7 | Optional default Test Plan/Suite; else WI + story link |
| D8 | Code Intelligence is optional; local path and/or Azure Repos (`ado_repository`) |
| D9 | When both sources set, Azure Repos wins; local-only for WIP |
| D10 | Azure Repos access is **read-only** (clone/fetch; never push) |
| D11 | ADO work-item writes require `ADO_WRITES_ENABLED=true` + non-dry-run after approval |

---

## QA Strategy (golden example)

- Feature Type: Backend API · Risk: High  
- Required: Positive, Negative, Edge, Validation, API, Integration, Regression  
- Not required: UI, Accessibility, Database, Performance  
- Reason: backend API behavior only — no UI/DB changes  
- Estimates: 18 new · 32 existing · 14 duplicates  

---

## Implementation status

| Area | Status |
|------|--------|
| Domain models, policies, validators | Done |
| ADO client, repos, DI | Done |
| 10 MCP tools wired to services | Done |
| OrchestrationService workflow | Done |
| Code Intelligence engine | Done (optional path) |
| Unit + contract tests | Done |
