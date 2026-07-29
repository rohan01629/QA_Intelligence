# 06 — Data Flow

**Product:** QA Intelligence MCP Server  

---

## 1. End-to-End Data Flow

```text
[ADO User Story JSON]
        │
        ▼
  Mapper → UserStory (domain)
        │
        ▼
  AnalysisService + Policies
        │
        ├──► RequirementGaps[]
        └──► QAStrategy
              ├── feature_type, risk
              ├── testing_required[]
              ├── testing_not_required[]
              ├── reason
              └── estimates (preliminary)

[ADO Test Cases JSON] ──► Mapper → TestCaseSummary[]
[ADO Bugs JSON]       ──► Mapper → BugSummary[]
[Similar search hits] ──► SimilarTestCase[]

        │
        ▼
  DuplicateService → DuplicateCluster[]
        │
        ▼
  CoverageService → CoverageReport
        ├── covered / duplicate / bug_covered / missing
        ├── qa_strategy_final (estimates finalized)
        └── generation_directive

        │
        ▼
  Cursor LLM drafts TestCaseDraft[]
  (only missing ∩ testing_required)

        │
        ▼
  Validation Layer (hard gates)
        │
        ├── reject → CreateResult(error)
        └── accept → Mapper → ADO Create Test Case JSON
                            → ids
                            → Link relations to User Story
```

---

## 2. Transformation Stages

| Stage | Input | Output | Mutation? |
|-------|-------|--------|-----------|
| Fetch story | work_item_id | UserStory | No |
| Analyze | UserStory | RequirementAnalysis + QAStrategy | No |
| Inventory | story id / query | summaries, bugs, similars | No |
| Dedupe | candidates + existing | clusters | No |
| Coverage | analysis + inventory | CoverageReport | No |
| Draft | CoverageReport (in Cursor) | TestCaseDraft[] | Client-side only |
| Validate | drafts | ok drafts + errors | No ADO yet |
| Create | ok drafts | ADO ids | **Yes** |
| Link | story id + ids | relations | **Yes** |

---

## 3. QA Strategy Estimate Lifecycle

```text
analyze_requirement
  estimates.preliminary = true
  heuristic from AC count, feature type, risk, complexity signals

generate_coverage_report
  estimates.preliminary = false
  estimated_existing_coverage  ← count of covered intents
  estimated_duplicate_scenarios ← cluster sizes / overlaps
  estimated_new_test_cases      ← len(missing_scenarios)
```

**Generation budget:** Cursor should target approximately `estimated_new_test_cases` and must not recreate covered or duplicate intents.

---

## 4. Test Case Field Flow (strict)

```text
LLM draft
  title: str
  steps: [s1..sN]
  expected_results: [e1..eN]

Validator
  N must equal M
  no blank fields
  no extra keys

ADO mapper
  title → System.Title
  steps + expected → Microsoft.VSTS.TCM.Steps (or project-configured field mapping)
```

Internal metadata (`ado_id`, `url`) may exist **after** create inside domain/service results but **never** as required input fields on drafts.

---

## 5. Parallelism

After analysis (and if not blocked):

- `get_existing_test_cases`  
- `search_similar_test_cases`  
- `get_related_bugs`  

may execute concurrently. Coverage and duplicate detection require their outputs and therefore run afterward.

---

## 6. Data Retention

v1 is **stateless** regarding business data:

- No local database of test cases  
- Azure DevOps is the system of record  
- Logs retain operational telemetry only (see logging strategy)  

Future cache/read models: [13-future-scalability.md](./13-future-scalability.md).

---

## Related

- [05-sequence-diagram.md](./05-sequence-diagram.md)  
- [07-domain-models.md](./07-domain-models.md)  
- [11-azure-devops-integration.md](./11-azure-devops-integration.md)  
