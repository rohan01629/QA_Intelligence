# 03 — MCP Tool Design

**Product:** QA Intelligence MCP Server  

---

## 1. Design Principles

1. **Closed surface** — exactly nine tools; no generic ADO CRUD.  
2. **Thin handlers** — parse → service → serialize `ToolResponse`.  
3. **Reads are side-effect free**; writes are explicit.  
4. **Dry-run** on write tools for safe preview.  
5. **Structured errors** with stable codes (see [14-error-handling-strategy.md](./14-error-handling-strategy.md)).  
6. Every response includes `correlation_id`.  

---

## 2. Common Response Envelope

```text
ToolResponse[T]
  ok: bool
  correlation_id: str
  data: T | None
  error: ErrorBody | None
  warnings: list[str]        # soft signals; never replace hard errors
```

```text
ErrorBody
  code: str
  message: str
  details: dict | None
```

---

## 3. Tool Catalog

| Tool | Kind | Side effect | Primary consumer need |
|------|------|-------------|------------------------|
| `get_user_story` | Read | None | Title, description, AC |
| `get_existing_test_cases` | Read | None | Linked / related tests |
| `search_similar_test_cases` | Read | None | Project-wide similar coverage |
| `get_related_bugs` | Read | None | Bug-covered regression signals |
| `analyze_requirement` | Analyze | None | QA Strategy + gaps |
| `detect_duplicate_test_cases` | Analyze | None | Semantic duplicate clusters |
| `generate_coverage_report` | Analyze | None | Missing scenarios + final estimates |
| `create_test_cases` | Write | Creates work items | Validated create |
| `link_test_cases` | Write | Creates relations | Story ↔ test links |

---

## 4. Per-Tool Contracts

### 4.1 `get_user_story`

**Input**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `work_item_id` | int | Yes | Azure DevOps work item ID |

**Output `data`:** `UserStory`  
(id, title, description, acceptance_criteria[], state, area_path, iteration_path, tags[])

**Errors:** `ADO_NOT_FOUND`, `ADO_AUTH_FAILED`, `ADO_UNAVAILABLE`

---

### 4.2 `get_existing_test_cases`

**Input:** `user_story_id: int`  

**Output `data`:** `TestCaseSummary[]`  
(id, title, steps_preview, expected_preview, state, link_type)

**Semantics:** Tests linked to the story and/or configured suite association.

---

### 4.3 `search_similar_test_cases`

**Input**

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `query` | str | — | Derived from title/AC/modules |
| `area_path` | str? | None | Scope search |
| `top` | int | 25 | Max 50 |

**Output `data`:** `SimilarTestCase[]`  
(id, title, similarity_score, match_signals[])

---

### 4.4 `get_related_bugs`

**Input:** `user_story_id: int`  

**Output `data`:** `BugSummary[]`  
(id, title, state, severity, repro_steps_preview)

**Semantics:** Related via work-item links and/or area + tag heuristics (documented in ADO integration).

---

### 4.5 `analyze_requirement`

**Input:** `user_story_id: int` **or** embedded `UserStory` payload  

**Output `data`:** `RequirementAnalysis`

Includes:

- Business rules, dependencies, modules, validation rules, data flow notes, regression impact  
- `requirement_gaps[]`  
- **`qa_strategy: QAStrategy`** (authoritative category allow/deny list)  
- `blocked: bool`  

**QA Strategy presentation shape (required):**

```text
Feature Type / Risk
Testing Required (✓)
Testing Not Required (✗) + reasons
Reason (narrative)
Estimated New / Existing / Duplicates  (preliminary if inventory not loaded)
```

If blocked → Cursor must surface gaps; must not invent AC.

---

### 4.6 `detect_duplicate_test_cases`

**Input**

| Field | Type | Notes |
|-------|------|-------|
| `candidates` | drafts or summaries | Proposed or existing set A |
| `existing` | summaries | Set B (inventory + similar) |

**Output `data`:** `DuplicateCluster[]`  
(canonical, duplicates[], similarity, basis ∈ {intent, workflow, ac_mapping, expected_result})

Duplicates are **semantic**, not exact string matches.

---

### 4.7 `generate_coverage_report`

**Input:** story id + analysis snapshot + existing + similar + bugs (+ optional drafts)  

**Output `data`:** `CoverageReport`

- `covered_scenarios[]`  
- `duplicate_scenarios[]`  
- `bug_covered_scenarios[]`  
- `missing_scenarios[]`  
- `qa_strategy_final: QAStrategy` (estimates finalized)  
- `generation_directive`: `fresh_suite` | `gap_fill_only` | `blocked`  

**Rules**

- No existing tests → `fresh_suite` (still only Required categories)  
- Existing tests → `gap_fill_only`  
- Blocking gaps → `blocked`  

---

### 4.8 `create_test_cases`

**Input**

| Field | Type | Default |
|-------|------|---------|
| `test_cases` | `TestCaseDraft[]` | — |
| `dry_run` | bool | false |
| `reject_duplicates` | bool | true |
| `override_requirement_block` | bool | false |

**Each draft — ONLY three fields:**

```text
title: str
steps: list[str] | list[TestStep]
expected_results: list[str] | list[ExpectedResult]
```

**Hard validation before ADO write** — see [10-validation-layer.md](./10-validation-layer.md).

**Output `data`:** `CreateResult[]` (per-item: status, id?, validation_errors[], warnings[])

**Recommendation:** per-item success/failure (not all-or-nothing batch).

---

### 4.9 `link_test_cases`

**Input:** `user_story_id: int`, `test_case_ids: list[int]`, `dry_run?: bool`  

**Output `data`:** `LinkResult[]`  

Creates relations (e.g. Tests / Tested By — exact link type in ADO integration doc).

---

## 5. Tool Ordering Guidance (for Cursor)

Recommended order matches the product workflow. After `analyze_requirement`, inventory tools (`get_existing_test_cases`, `search_similar_test_cases`, `get_related_bugs`) may run **in parallel**. Analysis tools that need inventory run after. Writes run last.

---

## 6. Explicitly Out of Scope

Do **not** implement tools for:

- Generic work item CRUD  
- Updating work items  
- Uploading attachments  
- Adding comments  
- Deleting test cases  

---

## Related

- [07-domain-models.md](./07-domain-models.md)  
- [10-validation-layer.md](./10-validation-layer.md)  
- [12-llm-interaction-flow.md](./12-llm-interaction-flow.md)  
