# 01 — High-Level Architecture

**Product:** QA Intelligence MCP Server  
**Audience:** Engineering, QA Leadership, Product  

---

## 1. Purpose

QA Intelligence is a **production-grade Azure DevOps MCP Server** that behaves like an experienced QA engineer. It is not a generic ADO CRUD wrapper and not a blind test-case generator.

Its job is to:

1. Fetch and understand a User Story  
2. Optionally analyze a **local application repository** (Code Intelligence) for implementation impact  
3. Inventory existing tests and related bugs  
4. Produce a **QA Strategy** (what to test / what not to test)  
5. Detect duplicates and coverage gaps  
6. Accept only valid, missing test cases  
7. Create and link those cases in Azure DevOps  

---

## 2. System Context

```text
┌────────────────────┐         MCP (stdio / SSE)        ┌──────────────────────────────┐
│  Cursor Agent      │◄────────────────────────────────►│  QA Intelligence MCP Server  │
│  (LLM orchestrator)│     tool call / structured JSON  │  FastMCP + Services + Domain │
└────────────────────┘                                  └───────┬──────────────┬───────┘
                                                                │              │ optional
                                                                │ HTTPS        │ local FS
                                                                │ PAT          │ repository_path
                                                                ▼              ▼
                                                 ┌──────────────────┐  ┌─────────────────────┐
                                                 │ Azure DevOps     │  │ Application codebase│
                                                 │ Work Items ·     │  │ (read-only search)  │
                                                 │ Relations ·      │  └─────────────────────┘
                                                 │ Test Plans*      │
                                                 └──────────────────┘
* Test Plans/Suites optional via configuration
```

### External actors

| Actor | Role |
|-------|------|
| Business Analyst | Reviews requirement gaps from analysis |
| QA Engineer | Primary user — asks Cursor to generate cases for a story |
| Automation Engineer | Consumes structured, executable cases |
| Test Lead | Approves strategy, may override blocked generation |

---

## 3. Responsibility Split

| Concern | Owner |
|---------|--------|
| Workflow orchestration | Cursor Agent and/or `OrchestrationService` |
| Natural-language drafting of missing test cases | Cursor LLM and/or `TestCaseGenerationService` |
| Fetching ADO data with fidelity | MCP Server |
| Local codebase search / Implementation Summary | MCP Server (Code Intelligence; optional local and/or Azure Repos) |
| QA Strategy, duplicate detection, coverage math | MCP Server |
| Hard validation (3 fields, step↔result parity) | MCP Server |
| Creating / linking Test Cases | MCP Server |
| Source of truth for work items | Azure DevOps |
| Source of truth for *how it is built* | Application codebase (when path provided) |

**Design rule:** The MCP server stays deterministic and testable. Drafts may come from the LLM or from server-side templates enriched by Code Intelligence; the server decides scope, rejects bad output, and writes safely.

---

## 4. Architectural Style

**Hexagonal (ports & adapters) + layered application core.**

| Layer | Responsibility |
|-------|----------------|
| Transport | FastMCP tool handlers (thin). FastAPI `/health`, `/ready` only |
| Application (Services) | Use-case orchestration |
| Domain | Models, QA Strategy policy, validators, invariants |
| Ports | Repository protocols, AuthProvider, SimilarityScorer |
| Adapters | Azure DevOps HTTP client, mappers, config, logging |

Cross-cutting: Dependency Injection, Structlog, correlation IDs, typed Settings (pydantic-settings).

---

## 5. Product Principles

| Principle | Architectural implication |
|-----------|---------------------------|
| Intelligence over volume | Category policy + QA Strategy before any create |
| Coverage awareness | Existing tests + bugs constrain generation |
| No assumption inflation | Blocking gaps → stop; do not invent AC |
| Strict output contract | `extra=forbid`; title / steps / expected only |
| Focused MCP surface | Exactly 10 tools; no generic CRUD |
| Code as implementation truth | Optional `analyze_codebase`; never invent from empty matches |
| Safe writes | Dry-run supported; per-item create results |
| Production discipline | Async, SOLID, repository pattern, full test pyramid |

---

## 6. Primary Workflow (conceptual)

```text
User Story ID
    → get_user_story
    → analyze_requirement          → QA Strategy (+ gaps)
    → [optional] analyze_codebase(repository_path and/or ado_repository) → Implementation Summary
    → get_existing_test_cases
    → search_similar_test_cases
    → get_related_bugs             (reads may run in parallel after analysis)
    → detect_duplicate_test_cases
    → generate_coverage_report     → final estimates + missing scenarios
    → [LLM and/or generation service drafts only missing, required categories]
    → create_test_cases            → hard validation + ADO create
    → link_test_cases              → story ↔ cases
```

---

## 7. QA Strategy (summary)

Before generation, the system emits:

- Feature Type (e.g. Backend API)  
- Risk (e.g. High)  
- Testing Required (allow-list)  
- Testing Not Required (deny-list + reasons)  
- Narrative Reason  
- Estimates: new / existing coverage / duplicates  

Example: Backend API + High → Required includes Positive, Negative, Edge, Validation, API, Integration, Regression; Not Required includes UI, Accessibility, Database, Performance when no signals exist.

See [07-domain-models.md](./07-domain-models.md).

---

## 8. Explicit Non-Goals (v1)

- Generic Azure DevOps CRUD MCP tools  
- Update / delete work items  
- Comments, attachments  
- Blind generation of all optional categories  
- Inventing acceptance criteria when requirements are incomplete  
- Server-side LLM for drafting test cases (v1 — see [12-llm-interaction-flow.md](./12-llm-interaction-flow.md))  

---

## 9. Related Documents

- [02-folder-structure.md](./02-folder-structure.md)  
- [04-component-diagram.md](./04-component-diagram.md)  
- [12-llm-interaction-flow.md](./12-llm-interaction-flow.md)  
