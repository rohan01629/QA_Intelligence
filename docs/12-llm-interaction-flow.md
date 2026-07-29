# 12 — LLM Interaction Flow

**Product:** QA Intelligence MCP Server  

---

## 1. Design Decision (v1)

| Concern | Where it runs |
|---------|----------------|
| Orchestration of the 15-step workflow | Cursor Agent (LLM + tool calling) |
| Drafting test case title/steps/expected | Cursor LLM |
| Fetching ADO data | MCP Server |
| QA Strategy, gaps, duplicates, coverage | MCP Server (deterministic policies + scorers) |
| Hard validation & create/link | MCP Server |

**There is no `generate_test_cases` MCP tool.** Generation is intentionally client-side so the server remains deterministic, auditable, and unit-testable without an LLM dependency in v1.

---

## 2. Interaction Pattern

```text
QA Engineer
    │
    ▼
Cursor System / User Prompt
  “Generate test cases for User Story 73230.
   Use QA Intelligence MCP tools. Follow QA Strategy allow/deny lists.
   Create only missing scenarios. Use exactly 3 fields. Steps↔Expected 1:1.”
    │
    ▼
Cursor plans tool calls ──► MCP tools ──► structured JSON
    │
    ├── If QAStrategy.blocked → stop; present gaps to user
    ├── Else inventory + coverage
    ├── LLM drafts TestCaseDraft[] from missing_scenarios only
    ├── Optional: create_test_cases(dry_run=true)
    ├── create_test_cases / link_test_cases
    └── Summarize for QA Engineer
```

---

## 3. What the LLM Must Receive

From MCP (structured):

1. UserStory (title, description, AC)  
2. QAStrategy (required / not required / reason / estimates)  
3. Requirement gaps (if any)  
4. Existing + similar tests + bugs  
5. Duplicate clusters  
6. CoverageReport.missing_scenarios + generation_directive  

From product rules (prompt / skill / tool descriptions):

- Never invent AC when blocked  
- Never generate deny-listed categories  
- Only three fields per case  
- One action per step; one assertion per expected result  

---

## 4. What the LLM Must Not Do

- Call non-existent generic ADO CRUD tools  
- Blindly emit all optional categories  
- Recreate covered or duplicate intents  
- Submit mismatched step/expected counts  
- Bypass dry-run guidance in production runbooks without Test Lead approval when blocked  

---

## 5. Server-Side “Intelligence” Without LLM (v1)

AnalysisService uses:

- Keyword / pattern signals for feature type and optional categories  
- Heuristic risk scoring (keywords, AC thinness, integration signals)  
- Gap detectors (missing error handling language, conflicting AC markers, empty AC)  
- Estimate heuristics (AC count × category weight × risk factor), then finalized by coverage math  

This keeps CI deterministic. Optional future: LLM adjudicator behind a port (see scalability).

---

## 6. Prompt / Tool Description Strategy

| Artifact | Owner | Purpose |
|----------|-------|---------|
| MCP tool docstrings / schemas | Server | Teach Cursor how to call tools correctly |
| `prompts/analysis_guidance.py` | Server | Short directive strings embedded in analysis/coverage responses |
| Cursor rule / skill (optional) | Client workspace | Enforce workflow order and format |

Guidance fragments returned in tool payloads help steer the LLM without a second model call on the server.

---

## 7. Failure Collaboration

| MCP signal | LLM behavior |
|------------|--------------|
| `blocked=true` | Present gaps; do not draft cases |
| `generation_directive=gap_fill_only` | Draft only missing |
| `VALIDATION_*` on create | Fix drafts; retry failed items only |
| `ADO_NOT_FOUND` | Stop; ask user for correct id |

---

## 8. Future Option (not v1)

Server-side generation tool (`generate_missing_test_cases`) calling an LLM provider:

- Same Validation Layer  
- Same QA Strategy allow/deny  
- Feature-flagged; default off  

Does not remove Cursor orchestration; it becomes an alternative drafter behind a port `TestCaseDrafter`.

---

## Related

- [01-high-level-architecture.md](./01-high-level-architecture.md)  
- [05-sequence-diagram.md](./05-sequence-diagram.md)  
- [13-future-scalability.md](./13-future-scalability.md)  
