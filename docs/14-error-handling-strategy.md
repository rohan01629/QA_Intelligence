# 14 — Error Handling Strategy

**Product:** QA Intelligence MCP Server  

---

## 1. Goals

- Machine-readable errors for Cursor  
- Human-readable messages for QA users  
- No secret leakage  
- Prefer partial success on batch writes  
- Distinguish validation failures from infrastructure failures  

---

## 2. Exception Hierarchy (domain/infrastructure)

```text
QaIntelligenceError
├── ValidationError          # format / invariant failures
├── RequirementBlockedError  # gaps forbid generation
├── NotFoundError            # ADO 404
├── AuthError                # 401/403
├── RateLimitError           # 429 (retryable)
├── UpstreamError            # 5xx / timeout (retryable)
└── ConfigurationError       # missing settings
```

MCP layer catches these and maps to `ToolResponse(ok=false, error=ErrorBody)`.

---

## 3. Stable Error Codes

| Code | HTTP/ADO analog | Retry? |
|------|-----------------|--------|
| `VALIDATION_STEP_MISMATCH` | n/a | No — fix draft |
| `VALIDATION_BLANK_TITLE` | n/a | No |
| `VALIDATION_EMPTY_STEPS` | n/a | No |
| `VALIDATION_EMPTY_EXPECTED` | n/a | No |
| `VALIDATION_EXTRA_FIELDS` | n/a | No |
| `VALIDATION_DUPLICATE_BATCH` | n/a | No — remove dupes |
| `REQUIREMENT_BLOCKED` | n/a | No — fix story or override |
| `ADO_NOT_FOUND` | 404 | No |
| `ADO_AUTH_FAILED` | 401/403 | No |
| `ADO_RATE_LIMITED` | 429 | Yes after backoff |
| `ADO_UNAVAILABLE` | 5xx/timeout | Limited |
| `ADO_WRITE_FAILED` | write error | Case-by-case |
| `CONFIG_INVALID` | n/a | No |
| `INTERNAL_ERROR` | unexpected | No (alert) |

---

## 4. Tool Response Rules

1. Unexpected exceptions → `INTERNAL_ERROR` + log stack with `correlation_id`.  
2. Never put PAT, Authorization headers, or raw env secrets in `message`/`details`.  
3. Validation errors on create are **per-item** when possible; envelope `ok=true` with mixed item statuses is allowed if at least the call executed — alternatively `ok=true` and item-level `status=rejected`. Prefer documenting one approach in ADR; **recommended:** envelope `ok=true` when the tool ran; item statuses carry outcomes; envelope `ok=false` only for total call failure (auth, config, parse of entire payload).  
4. `details` may include `index`, `field`, `expected`, `actual` for validators.

---

## 5. Retry Policy

| Error | Policy |
|-------|--------|
| RateLimitError | Respect Retry-After; exponential backoff + jitter |
| UpstreamError | Retry once (reads); writes only if idempotent key present |
| AuthError | No retry |
| ValidationError | No retry |
| NotFoundError | No retry |

Retries happen inside the ADO client, not ad hoc in every tool.

---

## 6. Partial Failure (Writes)

```text
create_test_cases([A ok, B bad, C ok])
  → A created
  → B rejected (validation)
  → C created
link_test_cases([A, C])  # Cursor links successes
```

Do not roll back successful creates (ADO has no multi-create transaction). Document ids clearly so users can clean up manually if needed (delete remains out of MCP scope).

---

## 7. Blocking Requirements

When analysis sets `blocked=true`:

- Coverage directive = `blocked`  
- Create without override → `REQUIREMENT_BLOCKED`  
- Override requires explicit flag for Test Lead exceptional path; log audit warning  

---

## Related

- [10-validation-layer.md](./10-validation-layer.md)  
- [15-logging-strategy.md](./15-logging-strategy.md)  
