# 08 — Repository Layer

**Product:** QA Intelligence MCP Server  

---

## 1. Purpose

The repository layer isolates Azure DevOps transport and JSON shapes from application services. Services speak **domain models**; adapters speak **REST**.

Pattern: **Repository + Protocol (port) + Mapper**.

---

## 2. Ports (Protocols)

### WorkItemRepository

```text
get_user_story(id: int) -> UserStory
get_bug(id: int) -> BugSummary
get_related_work_items(id: int, link_types: list[str]) -> list[RelatedRef]
```

### TestCaseRepository

```text
list_linked_to_story(user_story_id: int) -> list[TestCaseSummary]
get_test_case(id: int) -> TestCaseSummary
create_test_case(draft: TestCaseDraft) -> int   # returns ADO id
link_to_user_story(user_story_id: int, test_case_id: int) -> None
# optional (config):
add_to_suite(suite_id: int, test_case_id: int) -> None
```

### QueryRepository

```text
search_test_cases(query: str, area_path: str | None, top: int) -> list[TestCaseSummary]
list_bugs_for_story(user_story_id: int) -> list[BugSummary]
```

### AuthProvider

```text
get_authorization_header() -> dict[str, str]
```

### SimilarityScorer

```text
score(a: ScenarioText, b: ScenarioText) -> float
```

Used by DuplicateService / similar search ranking. v1: deterministic feature scorer. Future: embeddings behind same port.

---

## 3. Adapter Implementations (planned)

| Adapter | Implements | Notes |
|---------|------------|-------|
| `AdoWorkItemRepository` | WorkItemRepository | Work Item Tracking REST |
| `AdoTestCaseRepository` | TestCaseRepository | WI create + relations; optional Test Plan APIs |
| `AdoQueryRepository` | QueryRepository | WIQL and/or Search API |
| `PatAuthProvider` | AuthProvider | Basic PAT encoding |
| `FeatureSimilarityScorer` | SimilarityScorer | Weighted intent/workflow/expected |

---

## 4. Mapping Rules

- Mappers live in `infrastructure/ado/mappers.py`.  
- Never leak raw ADO field dictionaries into services (except optional `debug` behind flag).  
- Acceptance Criteria: support common field variants (Description sections, custom AC fields) via configurable field names.  
- Test steps: map to/from `Microsoft.VSTS.TCM.Steps` XML/HTML structure used by ADO Test Case work items (exact mapping documented in ADO integration).  

---

## 5. Error Mapping

| ADO / HTTP | Repository behavior |
|------------|---------------------|
| 404 | raise `NotFoundError` |
| 401/403 | raise `AuthError` |
| 429 | raise `RateLimitError` (retryable) |
| 5xx | raise `UpstreamError` (retryable once) |
| Timeout | raise `UpstreamError` |

Services / MCP layer map these to tool error codes.

---

## 6. What Repositories Must Not Do

- Category policy / QA Strategy decisions  
- Step↔expected validation (domain validation layer)  
- LLM prompting  
- Logging secrets or full PAT  

---

## Related

- [11-azure-devops-integration.md](./11-azure-devops-integration.md)  
- [09-service-layer.md](./09-service-layer.md)  
- [14-error-handling-strategy.md](./14-error-handling-strategy.md)  
