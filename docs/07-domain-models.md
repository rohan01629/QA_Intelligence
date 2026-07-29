# 07 — Domain Models

**Product:** QA Intelligence MCP Server  

---

## 1. Ubiquitous Language

| Term | Meaning |
|------|---------|
| User Story | Requirement work item under analysis |
| QA Strategy | Decision record: what to test, skip, and estimate |
| Test Case Draft | Pre-persist case with exactly three fields |
| Missing scenario | Intent not covered by existing/similar/bug coverage |
| Duplicate | Same business intent/workflow/AC mapping/expected outcome |
| Blocking gap | Incomplete requirement that forbids generation |

---

## 2. Enumerations

```text
FeatureType:
  backend_api | ui | api | workflow | data | integration | reporting | other

RiskLevel:
  low | medium | high | critical

RequirementGapType:
  missing_validation
  ambiguous_ac
  missing_expected_behavior
  missing_error_handling
  conflicting_requirements
  other

GapSeverity:
  info | warning | blocking

TestCategory (Always):
  positive | negative | edge | validation | regression

TestCategory (Optional):
  boundary | ui | api | database | integration | security |
  accessibility | performance | compatibility | permission |
  localization | business_rules | state_transition | recovery |
  concurrency | configuration | feature_flags | notifications |
  reporting | file_upload | logging | audit

GenerationDirective:
  fresh_suite | gap_fill_only | blocked

DuplicateBasis:
  intent | workflow | ac_mapping | expected_result
```

Display labels (examples): `backend_api` → "Backend API"; `edge` → "Edge Cases".

---

## 3. Core Entities

### UserStory

```text
UserStory
  id: int
  title: str
  description: str
  acceptance_criteria: list[str]
  state: str
  area_path: str
  iteration_path: str
  tags: list[str]
```

### TestStep / ExpectedResult

```text
TestStep
  order: int          # 1..N
  action: str         # exactly one user action

ExpectedResult
  order: int          # 1..N matching TestStep.order
  assertion: str      # validates only that step
```

### TestCaseDraft (MCP write contract)

```text
TestCaseDraft
  title: str
  steps: list[TestStep] | list[str]
  expected_results: list[ExpectedResult] | list[str]
  # extra = forbid
```

### TestCaseSummary (read model)

```text
TestCaseSummary
  id: int
  title: str
  steps_preview: str | list[str]
  expected_preview: str | list[str]
  state: str
  link_type: str | None
```

### BugSummary

```text
BugSummary
  id: int
  title: str
  state: str
  severity: str | None
  repro_steps_preview: str | None
```

---

## 4. QA Strategy (first-class)

```text
QAStrategy
  feature_type: FeatureType
  risk: RiskLevel
  testing_required: list[TestCategory]
  testing_not_required: list[CategoryExclusion]
  reason: str
  estimates: CoverageEstimates
  blocked: bool

CategoryExclusion
  category: TestCategory
  reason: str

CoverageEstimates
  estimated_new_test_cases: int
  estimated_existing_coverage: int
  estimated_duplicate_scenarios: int
  preliminary: bool
```

### Canonical presentation

```text
QA Strategy

Feature Type:
Backend API

Risk:
High

Testing Required:
✓ Positive
✓ Negative
✓ Edge Cases
✓ Validation
✓ API
✓ Integration
✓ Regression

Testing Not Required:
✗ UI
✗ Accessibility
✗ Database
✗ Performance

Reason:
This user story modifies only backend API behavior without UI or database changes.

Estimated New Test Cases:
18

Estimated Existing Coverage:
32

Estimated Duplicate Scenarios:
14
```

---

## 5. Analysis & Coverage Models

```text
RequirementGap
  type: RequirementGapType
  severity: GapSeverity
  description: str
  evidence: str

RequirementAnalysis
  user_story_id: int
  business_rules: list[str]
  dependencies: list[str]
  modules: list[str]
  validation_rules: list[str]
  data_flow_notes: str | None
  regression_impact: str | None
  requirement_gaps: list[RequirementGap]
  qa_strategy: QAStrategy
  blocked: bool

ScenarioRef
  key: str
  title: str
  category: TestCategory | None
  source: existing | similar | bug | missing | draft
  related_ids: list[int]

DuplicateCluster
  canonical: ScenarioRef
  duplicates: list[ScenarioRef]
  similarity: float
  basis: DuplicateBasis

CoverageReport
  user_story_id: int
  covered_scenarios: list[ScenarioRef]
  duplicate_scenarios: list[ScenarioRef]
  bug_covered_scenarios: list[ScenarioRef]
  missing_scenarios: list[ScenarioRef]
  qa_strategy_final: QAStrategy
  generation_directive: GenerationDirective
```

---

## 6. Write Results

```text
CreateResult
  index: int
  status: created | validated_only | rejected
  id: int | None
  validation_errors: list[str]
  warnings: list[str]

LinkResult
  test_case_id: int
  status: linked | skipped | failed
  message: str | None
```

---

## 7. Invariants

1. For every TestCaseDraft: `len(steps) == len(expected_results)` with matching order 1..N.  
2. MCP draft payload allows **only** title, steps, expected_results (`extra=forbid`).  
3. `testing_required ∩ testing_not_required = ∅`.  
4. Always-categories ⊆ `testing_required` unless `blocked`.  
5. Optional categories in Required need evidence; exclusions need reasons.  
6. If any gap severity is `blocking` → `blocked=true` and new-case estimate = 0.  
7. Generation must honor Required allow-list and Not Required deny-list.  
8. Do not invent acceptance criteria to clear gaps.

---

## Related

- [10-validation-layer.md](./10-validation-layer.md)  
- [03-mcp-tool-design.md](./03-mcp-tool-design.md)  
