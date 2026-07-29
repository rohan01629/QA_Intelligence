# QA Intelligence MCP Server — Documentation Index

**Product:** QA Intelligence MCP Server  
**Status:** Architecture complete — awaiting approval before implementation  
**Version:** 0.2.0-arch  
**Stack:** Python 3.12 · FastMCP · FastAPI (health) · uv · Azure DevOps REST · Pydantic · Structlog · Pytest  

This folder contains the **complete system architecture**. No application implementation code belongs here.

---

## Architecture Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [01-high-level-architecture.md](./01-high-level-architecture.md) | System context, principles, responsibility split |
| 2 | [02-folder-structure.md](./02-folder-structure.md) | Repository layout and module boundaries |
| 3 | [03-mcp-tool-design.md](./03-mcp-tool-design.md) | Closed set of 9 MCP tools and contracts |
| 4 | [04-component-diagram.md](./04-component-diagram.md) | Layered components and dependencies |
| 5 | [05-sequence-diagram.md](./05-sequence-diagram.md) | End-to-end and per-tool sequences |
| 6 | [06-data-flow.md](./06-data-flow.md) | Data movement and transformation |
| 7 | [07-domain-models.md](./07-domain-models.md) | Entities, value objects, QA Strategy, invariants |
| 8 | [08-repository-layer.md](./08-repository-layer.md) | Ports, ADO adapters, mapping |
| 9 | [09-service-layer.md](./09-service-layer.md) | Application services and use cases |
| 10 | [10-validation-layer.md](./10-validation-layer.md) | Format, policy, and coverage validation |
| 11 | [11-azure-devops-integration.md](./11-azure-devops-integration.md) | REST API usage, auth, work item types |
| 12 | [12-llm-interaction-flow.md](./12-llm-interaction-flow.md) | Cursor/LLM vs MCP server responsibilities |
| 13 | [13-future-scalability.md](./13-future-scalability.md) | Growth paths without breaking v1 contracts |
| 14 | [14-error-handling-strategy.md](./14-error-handling-strategy.md) | Error taxonomy, retries, tool responses |
| 15 | [15-logging-strategy.md](./15-logging-strategy.md) | Structlog fields, redaction, correlation |
| 16 | [16-testing-strategy.md](./16-testing-strategy.md) | Unit, contract, integration, golden tests |

**Overview / historical draft:** [ARCHITECTURE.md](./ARCHITECTURE.md) — superseded as the single source of truth by the numbered docs above; retained as a consolidated summary.

---

## Product Vision (reminder)

Build an Azure DevOps MCP Server that behaves like an experienced QA Engineer:

- Understand the User Story  
- Analyze existing project knowledge  
- Detect duplicate coverage  
- Identify missing scenarios  
- Generate **only** meaningful test cases  
- Never blindly generate every testing category  

---

## Closed MCP Tool Surface

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

## Implementation Gate

**Do not write application code until architecture is approved.**

Recommended build order after approval: M1 skeleton → M2 domain/validation → M3 ADO read repos → M4 read tools → M5 analysis/coverage → M6 write path → M7 contract tests → M8 hardening.
