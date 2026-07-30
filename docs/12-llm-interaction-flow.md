# 12 — LLM Interaction Flow

**Product:** QA Intelligence MCP Server  

---

## 1. Design Decision (v1)

| Concern | Where it runs |
|---------|----------------|
| Orchestration of the QA workflow | Cursor Agent **or** `OrchestrationService` |
| Drafting test case title/steps/expected | Cursor LLM **and/or** `TestCaseGenerationService` |
| Fetching ADO data | MCP Server |
| Local codebase → Implementation Summary | MCP Server (`analyze_codebase` — local and/or Azure Repos) |
| QA Strategy, gaps, duplicates, coverage | MCP Server (deterministic policies + scorers) |
| Hard validation & create/link | MCP Server |

There is **no** MCP tool named `generate_test_cases`. Drafts come from the Cursor LLM (tool-driven path) or from `TestCaseGenerationService` inside orchestration. Both paths must still pass hard validation before ADO create.

---

## 2. Interaction Pattern

```text
QA Engineer
    │
    ▼
Cursor System / User Prompt
  “Generate test cases for User Story 73230.
   Use QA Intelligence MCP tools. Follow QA Strategy allow/deny lists.
   Optionally analyze_codebase(repository_path=…).
   Create only missing scenarios. Use exactly 3 fields. Steps↔Expected 1:1.
   Dry-run first; create/link only after approval.”
    │
    ▼
Cursor plans tool calls ──► MCP tools ──► structured JSON
    │
    ├── If QAStrategy.blocked → stop; present gaps to user
    ├── Optional: analyze_codebase → ImplementationSummary
    ├── Else inventory + coverage
    ├── LLM drafts TestCaseDraft[] from missing_scenarios (+ code signals)
    ├── Optional: create_test_cases(dry_run=true)
    ├── create_test_cases / link_test_cases  (only after user approval)
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
7. **Optional:** ImplementationSummary (affected files/APIs/rules/UI/flags)  

From product rules (prompt / skill / tool descriptions):

- Never invent AC when blocked  
- Never generate deny-listed categories  
- Only three fields per case  
- One action per step; one assertion per expected result  
- Prefer code-backed scenarios when Implementation Summary is present  
- Treat empty/noisy code matches as gaps, not as coverage  

---

## 4. What the LLM Must Not Do

- Call non-existent generic ADO CRUD tools  
- Blindly emit all optional categories  
- Recreate covered or duplicate intents  
- Submit mismatched step/expected counts  
- Bypass dry-run guidance without user approval for ADO writes  
- Paste application source into the MCP-TC repo  

---

## 5. Server-Side Intelligence Without LLM (v1)

AnalysisService uses:

- Keyword / pattern signals for feature type and optional categories  
- Heuristic risk scoring (keywords, AC thinness, integration signals)  

Code Intelligence uses:

- Term inference from story/bugs  
- Ranked local file search  
- Heuristic extraction of routes, validation, permissions, UI, DB, flags  

GenerationService uses templates + coverage gaps (+ optional Implementation Summary enrichment).

---

## 6. Failure Modes Affecting the LLM

| Signal | Required LLM behavior |
|--------|------------------------|
| `ADO_NOT_FOUND` | Stop; ask user for correct id |
| `blocked=true` | Present gaps; do not invent AC |
| Weak Implementation Summary | Call out implementation gap; do not invent APIs |
| Validation rejects | Fix drafts; do not force-create |

---

## Related

- [03-mcp-tool-design.md](./03-mcp-tool-design.md)  
- [09-service-layer.md](./09-service-layer.md)  
- [01-high-level-architecture.md](./01-high-level-architecture.md)  
