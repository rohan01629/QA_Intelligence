# 10 — Validation Layer

**Product:** QA Intelligence MCP Server  

---

## 1. Purpose

The validation layer is the **quality gate** that protects Azure DevOps from low-quality or malformed test cases and protects the product promise: *only meaningful, well-structured cases*.

Validation is domain-owned, invoked by services (especially `TestCaseService.create_many`), and exposed via tool errors/warnings.

---

## 2. Layers of Validation

| Layer | When | Severity |
|-------|------|----------|
| Schema (Pydantic) | Tool input parse | Hard fail request or item |
| Format invariants | Before create | Hard reject item |
| Duplicate batch | Before create | Hard reject item/pair (configurable) |
| Category allow-list | Before create (optional check) | Hard reject if category metadata present and denied |
| Requirement block | Before create | Hard reject unless override |
| Soft heuristics | Before create | Warning only |

---

## 3. Hard Reject Rules (mandatory)

Reject generated / submitted output if:

1. **Step count ≠ Expected Result count**  
2. **Blank Test Title**  
3. **Empty Steps**  
4. **Empty Expected Results**  
5. **Extra fields** beyond title / steps / expected_results (`extra=forbid`)  
6. **Intra-batch duplicates** when `reject_duplicates=true` (default)  
7. **Requirement blocked** when override is false  

Parity rule (product mandate):

```text
N Test Steps  →  exactly N Expected Results
Never 4 steps with 3 expected results
```

Each step = one user action. Each expected result validates only that step.

---

## 4. Soft Warnings (non-blocking)

- Multi-action step language ("and then", stacked imperatives)  
- Vague expected results ("works correctly", "as expected", "successfully" alone)  
- Missing mapping hint to an acceptance criterion  
- Draft count far from `estimated_new_test_cases` (budget variance)

Warnings travel in `warnings[]`; they do not by themselves block create.

---

## 5. Category / Strategy Validation

| Check | Rule |
|-------|------|
| Allow-list | If drafts are tagged with category (internal/extended metadata only — not part of 3-field public contract), category must be in `testing_required` |
| Deny-list | Must not create for `testing_not_required` |
| Public contract | External MCP draft remains 3 fields only; category guidance lives in CoverageReport for the LLM |

v1 recommendation: enforce category discipline primarily via **CoverageReport + Cursor instructions**; optional server-side category tag can be added later without changing the three-field user-facing format.

---

## 6. Validator Components (planned)

```text
TestCaseFormatValidator
  - title non-blank
  - steps non-empty
  - expected non-empty
  - len(steps) == len(expected_results)
  - order integrity if structured steps

StrictDraftModel (Pydantic)
  - extra = forbid

BatchDuplicateValidator
  - uses DuplicateService / SimilarityScorer on drafts

RequirementBlockGuard
  - respects QAStrategy.blocked + override flag

StepQualityHeuristics
  - emits warnings
```

---

## 7. Error Codes

| Code | Condition |
|------|-----------|
| `VALIDATION_STEP_MISMATCH` | counts differ |
| `VALIDATION_BLANK_TITLE` | empty title |
| `VALIDATION_EMPTY_STEPS` | no steps |
| `VALIDATION_EMPTY_EXPECTED` | no expected results |
| `VALIDATION_EXTRA_FIELDS` | unknown keys |
| `VALIDATION_DUPLICATE_BATCH` | semantic dupes in batch |
| `REQUIREMENT_BLOCKED` | gaps block generation |

---

## Related

- [07-domain-models.md](./07-domain-models.md)  
- [03-mcp-tool-design.md](./03-mcp-tool-design.md)  
- [14-error-handling-strategy.md](./14-error-handling-strategy.md)  
