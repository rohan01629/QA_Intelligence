# 16 — Testing Strategy

**Product:** QA Intelligence MCP Server  

---

## 1. Goals

Prove production quality **without** requiring live Azure DevOps for unit/contract suites.

Protect:

- Step ↔ expected parity rules  
- QA Strategy allow/deny behavior  
- Duplicate semantics  
- MCP tool schemas / error codes  
- ADO mapping correctness  

---

## 2. Test Pyramid

```text
            ┌──────────────┐
            │  Golden / E2E │  few (recorded fixtures)
            └───────┬───────┘
            ┌───────▼───────┐
            │  Integration  │  ADO client + repos (respx/vcr)
            └───────┬───────┘
            ┌───────▼───────┐
            │   Contract    │  MCP tool I/O + error codes
            └───────┬───────┘
            ┌───────▼───────┐
            │     Unit      │  domain, policies, validators, services
            └───────────────┘
```

**Framework:** Pytest (+ pytest-asyncio, respx/httpx mock, coverage).

---

## 3. Unit Tests

| Area | Examples |
|------|----------|
| Validators | mismatch counts, blank title, empty steps, extra fields |
| CategoryPolicy | Backend API → API+Integration on; UI/A11y/DB/Perf off with reasons |
| GapPolicy | empty AC → blocking |
| DuplicateService | “Verify Login” ≈ “Verify successful authentication” |
| CoverageService | fresh_suite vs gap_fill_only vs blocked |
| Mappers | steps↔expected preserved into ADO step structure |

No network. Fake repositories via protocol stubs.

---

## 4. Contract Tests

For each of the 9 tools:

- Input schema accepts valid payloads  
- Rejects invalid payloads with stable codes  
- Response envelope always has `ok`, `correlation_id`  
- Write tools honor `dry_run` (no repo create called)  

---

## 5. Integration Tests

- Azure DevOps client against **recorded HTTP fixtures** (respx / vcr)  
- Auth header injection  
- 404/401/429 mapping  
- Create JSON patch shape  
- Link relation payload shape  

Live ADO tests are optional, marked `@pytest.mark.live`, never required in default CI.

---

## 6. Golden Tests

Snapshot-style fixtures for a known story (e.g. Backend API / High risk example):

- QA Strategy required/not required sets  
- Estimate finalization given canned inventory (32 covered, 14 dupes → 18 missing)  
- CoverageReport directive  

Guardrails against silent policy drift.

---

## 7. Quality Gates (CI)

| Gate | Rule |
|------|------|
| Unit + contract | Must pass |
| Coverage | Threshold set at scaffold (recommend ≥90% on domain/validation) |
| Lint/type | ruff + mypy (planned) |
| Live ADO | Manual / nightly only |

---

## 8. Test Data Fixtures

```text
tests/fixtures/
  user_stories/
  test_cases/
  bugs/
  ado_http/
  golden/qa_strategy_backend_api_high.json
```

Include the Backend API golden QA Strategy as a fixture matching product example (18 / 32 / 14).

---

## 9. What We Do Not Test in v1

- Cursor LLM draft quality (evaluated manually / eval harness later)  
- Real network flakiness beyond mocked retries  
- Delete/update paths (out of product scope)  

---

## Related

- [07-domain-models.md](./07-domain-models.md)  
- [10-validation-layer.md](./10-validation-layer.md)  
- [03-mcp-tool-design.md](./03-mcp-tool-design.md)  
