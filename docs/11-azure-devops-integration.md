# 11 — Azure DevOps Integration

**Product:** QA Intelligence MCP Server  

---

## 1. Scope

Integrate **only** what QA Intelligence needs:

- Read User Stories  
- Read / search Test Cases  
- Read related Bugs  
- Create Test Cases  
- Link Test Cases to User Stories  
- Optionally add to a Test Suite (config)

**Out of scope:** generic CRUD, updates, deletes, comments, attachments.

---

## 2. Connectivity

| Setting | Purpose |
|---------|---------|
| `ADO_ORGANIZATION` | Org name |
| `ADO_PROJECT` | Project name |
| `ADO_BASE_URL` | Default `https://dev.azure.com` |
| `ADO_API_VERSION` | REST api-version |
| `ADO_PAT` | v1 secret via env |
| `HTTP_TIMEOUT_SECONDS` | Client timeout |
| `HTTP_MAX_RETRIES` | Idempotent retry budget |
| `ADO_DEFAULT_TEST_PLAN_ID` | Optional |
| `ADO_DEFAULT_SUITE_ID` | Optional |
| `ADO_USER_STORY_TYPE` | Default `User Story` (configurable) |
| `ADO_TEST_CASE_TYPE` | Default `Test Case` |
| `ADO_AC_FIELD` | Optional custom AC field reference |

Transport: async HTTP client (e.g. httpx.AsyncClient) inside `AzureDevOpsClient`.

---

## 3. Authentication

**v1:** Personal Access Token via `AuthProvider` → HTTP Basic (`:` + PAT) or Bearer as required by endpoint.

**Design constraint:** repositories call `AuthProvider.get_authorization_header()` only. Future Managed Identity / OAuth replaces the provider implementation without changing repository code.

Never log the PAT or Authorization header values.

---

## 4. API Usage Map

| Capability | Typical ADO API | Used by |
|------------|-----------------|---------|
| Get work item | WIT Work Items – Get | Story, Bug, TestCase get |
| Batch get | WIT Work Items – Get Batch | Inventory enrichment |
| WIQL query | WIT WIQL | Similar search, bug listing heuristics |
| Create work item | WIT Work Items – Create (JSON Patch) | create_test_cases |
| Create relation | WIT updates with Relations | link_test_cases |
| Test suite add | Test Plan Suites – Add test cases | optional suite placement |

Exact routes and api-versions are fixed at implementation time in one client module.

---

## 5. Field Mapping (logical)

### User Story → domain

| Domain | ADO source (typical) |
|--------|----------------------|
| title | `System.Title` |
| description | `System.Description` |
| acceptance_criteria | `ADO_AC_FIELD` or parsed Description section |
| state | `System.State` |
| area_path | `System.AreaPath` |
| iteration_path | `System.IterationPath` |
| tags | `System.Tags` |

### Test Case draft → ADO create

| Domain | ADO target (typical) |
|--------|----------------------|
| title | `System.Title` |
| steps + expected_results | `Microsoft.VSTS.TCM.Steps` (structured step/expected pairs) |

Mapper must preserve **1:1 step ↔ expected** into ADO’s step format.

### Links

Recommended relation: Test Case **Tests** User Story / User Story **Tested By** Test Case (confirm against process template; make link type configurable).

---

## 6. Related Bugs Strategy

Order of resolution:

1. Work item relations from the User Story (Related, Produced By, etc. — configurable set)  
2. WIQL fallback: same AreaPath + tags overlap + recent bugs (bounded)  

Return unified `BugSummary[]` with provenance in logs, not necessarily in tool payload (keep payload lean).

---

## 7. Similar Test Case Search

1. Build query string from story title + key AC phrases + modules from analysis  
2. WIQL against Test Case type, optional AreaPath filter, `top` limit  
3. Rank with `SimilarityScorer`  
4. Return top N with scores and match signals  

---

## 8. Idempotency & Safety

- Prefer `create_test_cases(dry_run=true)` before write  
- No update/delete APIs exposed  
- Partial create success is OK; return per-item ids  
- Link step is separate and retryable  

---

## 9. Rate Limits & Resilience

- Honor `Retry-After` on 429  
- Exponential backoff with jitter for retryable failures  
- Circuit-style budget: stop after `HTTP_MAX_RETRIES`  
- Correlate all ADO calls with `correlation_id`  

---

## Related

- [08-repository-layer.md](./08-repository-layer.md)  
- [14-error-handling-strategy.md](./14-error-handling-strategy.md)  
- [15-logging-strategy.md](./15-logging-strategy.md)  
