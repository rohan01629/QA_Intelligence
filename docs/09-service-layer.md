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

### TestStrategyService

| Method | Behavior |
|--------|----------|
| `build(...)` | Risk-based category plan from analysis + coverage |

### TestCaseGenerationService

| Method | Behavior |
|--------|----------|
| `generate(...)` | Draft missing cases from coverage / strategy |
| Optional input | `implementation_summary` enriches validation/API/regression scenarios |
| Default | Works without Code Intelligence (ADO + story only) |

### CodeIntelligenceService

| Method | Behavior |
|--------|----------|
| `analyze(story, repository_path?, ado_repository?, ado_branch?, …)` | Resolve source → search → impact → `ImplementationSummary` |
| Collaborators | `AdoGitRepositoryService`, `RepositorySearchService`, `ImpactAnalysisService`, `ImplementationSummaryBuilder` |
| Source precedence | `ado_repository` (or `ADO_DEFAULT_GIT_REPOSITORY`) → else local `repository_path` |
| Side effects | Read-only analysis; ADO mode shallow-clones/refreshes cache; never writes app code or ADO work items |

### AdoGitRepositoryService

| Method | Behavior |
|--------|----------|
| `ensure_local_checkout(repository, branch?, …)` | Shallow clone or fetch tip into cache; return path + commit SHA |
| Auth | PAT in clone URL; scrubbed from logs and remote URL after refresh |

### OrchestrationService

| Method | Behavior |
|--------|----------|
| `run(user_story_id, …, repository_path?, ado_repository?, ado_branch?, dry_run)` | End-to-end workflow |
| Steps | fetch → analyze → **optional code intel** → inventory → duplicates → coverage → strategy → generate → validate → publish → link |
| Skip rule | `CODE_INTELLIGENCE` skipped when no local path, ado repo, or default git repo |

---

## 3. Orchestration Rules

1. **No writes inside analysis or Code Intelligence services.**  
2. Analysis may run from id (fetch story) or from provided payload (avoid double fetch).  
3. CoverageService is pure with respect to ADO when inputs are provided; may fetch if ids-only mode is used (prefer explicit inputs from Cursor for determinism).  
4. `create_many` short-circuits ADO when `dry_run=true`.  
5. If `qa_strategy.blocked` and `override_requirement_block=false`, create returns rejected with `REQUIREMENT_BLOCKED`.  
6. Code Intelligence failures are reported on the workflow step; they must not silently invent implementation facts.  

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
