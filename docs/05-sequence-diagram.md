# 05 — Sequence Diagram

**Product:** QA Intelligence MCP Server  

---

## 1. Primary End-to-End Sequence

Happy path: *Generate test cases for User Story N* (gap-fill).

```mermaid
sequenceDiagram
  actor User as QA Engineer
  participant Cursor as Cursor LLM
  participant MCP as QA Intelligence MCP
  participant Svc as Services
  participant ADO as Azure DevOps

  User->>Cursor: Generate test cases for US N
  Cursor->>MCP: get_user_story(N)
  MCP->>Svc: StoryService.get
  Svc->>ADO: GET work item
  ADO-->>Svc: payload
  Svc-->>MCP: UserStory
  MCP-->>Cursor: UserStory

  Cursor->>MCP: analyze_requirement(N)
  MCP->>Svc: AnalysisService.analyze
  Note over Svc: QA Strategy + gaps<br/>preliminary estimates
  Svc-->>MCP: RequirementAnalysis
  MCP-->>Cursor: QA Strategy

  opt Code Intelligence (optional local path and/or Azure Repos)
    Cursor->>MCP: analyze_codebase(path and/or ado_repository, N)
    MCP->>Svc: CodeIntelligenceService.analyze
    Note over Svc: Optional shallow ADO clone<br/>+ local FS search + impact<br/>ImplementationSummary
    Svc-->>MCP: ImplementationSummary
    MCP-->>Cursor: ImplementationSummary
  end

  alt blocked == true
    Cursor-->>User: Report requirement gaps (stop)
  else not blocked
    par Inventory
      Cursor->>MCP: get_existing_test_cases(N)
      MCP->>ADO: linked tests
      MCP-->>Cursor: existing[]
      Cursor->>MCP: search_similar_test_cases(query)
      MCP->>ADO: WIQL / search
      MCP-->>Cursor: similar[]
      Cursor->>MCP: get_related_bugs(N)
      MCP->>ADO: related bugs
      MCP-->>Cursor: bugs[]
    end

    Cursor->>MCP: detect_duplicate_test_cases(...)
    MCP->>Svc: DuplicateService.cluster
    MCP-->>Cursor: clusters[]

    Cursor->>MCP: generate_coverage_report(...)
    MCP->>Svc: CoverageService.report
    Note over Svc: Finalize estimates<br/>missing scenarios
    MCP-->>Cursor: CoverageReport

    Note over Cursor: Draft ONLY missing scenarios<br/>inside testing_required

    Cursor->>MCP: create_test_cases(drafts, dry_run?)
    MCP->>Svc: validate hard rules
    alt dry_run
      MCP-->>Cursor: validation results only
    else write
      Svc->>ADO: create Test Cases
      ADO-->>Svc: ids
      MCP-->>Cursor: CreateResult[]
      Cursor->>MCP: link_test_cases(N, ids)
      Svc->>ADO: create relations
      MCP-->>Cursor: LinkResult[]
    end
    Cursor-->>User: Summary (created, skipped, strategy)
  end
```

---

## 2. Analyze Requirement (detail)

```text
Cursor                AnalysisService           CategoryPolicy        GapPolicy
  |                         |                         |                    |
  | analyze_requirement     |                         |                    |
  |------------------------>|                         |                    |
  |                         | classify feature/risk   |                    |
  |                         |------------------------>|                    |
  |                         | required / not required |                    |
  |                         |------------------------>|                    |
  |                         | detect gaps             |-------------------->
  |                         | blocked?                |<-------------------|
  |                         | build QAStrategy        |                    |
  |<------------------------|                         |                    |
```

---

## 3. Create Test Cases (validation gate)

```text
Cursor          TestCaseService       FormatValidator      TestCaseRepository      ADO
  |                   |                     |                      |                |
  | create(drafts)    |                     |                      |                |
  |------------------>|                     |                      |                |
  |                   | validate each       |                      |                |
  |                   |-------------------->|                      |                |
  |                   | ok / errors         |                      |                |
  |                   |<--------------------|                      |                |
  |                   | if ok & !dry_run    |                      |                |
  |                   |------------------------------------------->|                |
  |                   |                                            | create WI      |
  |                   |                                            |--------------->|
  |                   |                                            |<---------------|
  | CreateResult[]    |                                            |                |
  |<------------------|                                            |                |
```

Invalid items never call ADO. Valid items proceed independently (per-item results).

---

## 4. Failure Sequences (summary)

| Failure | Sequence outcome |
|---------|------------------|
| Story not found | `ok=false`, `ADO_NOT_FOUND`; stop workflow |
| Auth failure | `ADO_AUTH_FAILED`; no retries with same bad secret |
| Blocking gaps | Analysis succeeds with `blocked=true`; no create unless override |
| Step/result mismatch | Item-level validation error; other items may still create |
| ADO 429 | Retry with backoff on reads; then `ADO_RATE_LIMITED` |

---

## Related

- [06-data-flow.md](./06-data-flow.md)  
- [12-llm-interaction-flow.md](./12-llm-interaction-flow.md)  
- [14-error-handling-strategy.md](./14-error-handling-strategy.md)  
