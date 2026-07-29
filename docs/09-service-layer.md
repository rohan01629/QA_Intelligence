# 09 — Service Layer

**Product:** QA Intelligence MCP Server  

---

## 1. Purpose

Services implement **application use cases**. They orchestrate domain policies, validators, and repositories. They are the primary unit of unit-testing for business behavior.

MCP tools are thin facades over services.

---

## 2. Services

### StoryService

| Method | Behavior |
|--------|----------|
| `get_user_story(id)` | Load via WorkItemRepository; normalize AC list |

### TestCaseService

| Method | Behavior |
|--------|----------|
| `list_existing(user_story_id)` | Linked/suite inventory |
| `create_many(drafts, dry_run, flags)` | Validate → optional create; per-item results |
| Responsibilities | Enforce format validation; optional batch duplicate reject |

### BugService

| Method | Behavior |
|--------|----------|
| `list_related(user_story_id)` | Related bugs for regression coverage signals |

### AnalysisService

| Method | Behavior |
|--------|----------|
| `analyze(story \| id)` | Feature type, risk, rules, gaps, **QAStrategy** |
| Uses | CategoryPolicy, GapPolicy, RiskPolicy |
| Does not | Call LLM in v1; uses deterministic signals + structured rules |
| Estimates | Preliminary heuristics when inventory absent |

### DuplicateService

| Method | Behavior |
|--------|----------|
| `detect(candidates, existing)` | Cluster via SimilarityScorer |
| Output | DuplicateCluster[] with basis explanations |

### CoverageService

| Method | Behavior |
|--------|----------|
| `generate_report(...)` | Merge existing, similar, bugs, duplicates, strategy |
| Output | CoverageReport with finalized estimates + directive |
| Rules | fresh_suite / gap_fill_only / blocked |

### LinkingService

| Method | Behavior |
|--------|----------|
| `link(user_story_id, test_case_ids, dry_run)` | Create relations; optional suite add |

---

## 3. Orchestration Rules

1. **No writes inside analysis services.**  
2. Analysis may run from id (fetch story) or from provided payload (avoid double fetch).  
3. CoverageService is pure with respect to ADO when inputs are provided; may fetch if ids-only mode is used (prefer explicit inputs from Cursor for determinism).  
4. `create_many` short-circuits ADO when `dry_run=true`.  
5. If `qa_strategy.blocked` and `override_requirement_block=false`, create returns rejected with `REQUIREMENT_BLOCKED`.  

---

## 4. Transactionality

Azure DevOps does not offer multi-WI ACID transactions.

**Strategy:**

- Per-item create  
- Link as a separate explicit step  
- Partial success is allowed and reported  
- Cursor can retry failed ids without recreating successes (idempotent link recommended)

---

## 5. Dependency Direction

```text
MCP Tool → Service → (Domain Policy | Validator | Repository Port | Scorer)
```

Services must not import FastMCP or FastAPI.

---

## Related

- [03-mcp-tool-design.md](./03-mcp-tool-design.md)  
- [10-validation-layer.md](./10-validation-layer.md)  
- [12-llm-interaction-flow.md](./12-llm-interaction-flow.md)  
