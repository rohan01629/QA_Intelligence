# 15 — Logging Strategy

**Product:** QA Intelligence MCP Server  

---

## 1. Goals

- Production-grade structured logs (JSON)  
- Correlate a full Cursor workflow across tools  
- Debug ADO issues without leaking secrets  
- Support ops metrics extraction later  

**Library:** Structlog  

---

## 2. Correlation

| Field | Source |
|-------|--------|
| `correlation_id` | Generated per tool invocation; accept inbound if MCP client provides one |
| `tool` | MCP tool name |
| `user_story_id` | When known |
| `ado_request_id` | If ADO returns one |

Return `correlation_id` in every `ToolResponse`.

---

## 3. Standard Event Fields

```text
timestamp
level
event                  # e.g. tool.started, tool.completed, ado.request, validation.rejected
correlation_id
tool
duration_ms
outcome                # success | error | partial
error_code             # when outcome=error
user_story_id
dry_run                # for write tools
created_count          # writes
rejected_count         # writes
```

---

## 4. Log Levels

| Level | Use |
|-------|-----|
| DEBUG | Mapper details, similarity scores (non-prod default off) |
| INFO | Tool start/complete, create/link summaries |
| WARNING | Soft validation, retries, requirement override used |
| ERROR | Tool failures, ADO failures after retries |
| CRITICAL | Config missing at startup, auth provider hard failure |

---

## 5. Redaction Policy

**Never log:**

- PAT / tokens / Authorization headers  
- Full `.env` contents  
- Password-like form fields if present in descriptions (best-effort redaction filters)

**Cautiously log:**

- User Story titles (usually OK)  
- Truncated description/AC excerpts at DEBUG only  
- Test case titles on create  

---

## 6. ADO Client Logging

Log for each outbound call:

- method, path template (not raw PAT query)  
- status_code  
- duration_ms  
- retry_count  
- correlation_id  

Do not log full response bodies in INFO; DEBUG may store truncated bodies in non-prod.

---

## 7. Startup Logging

On boot:

- app version  
- transport mode  
- org/project (not PAT)  
- log level  
- whether optional suite config is set  

Fail fast on missing required settings (`ConfigurationError`).

---

## 8. Future Observability

OpenTelemetry traces around tool → service → ADO spans can be added without changing domain logic. Log fields above should align with trace attributes.

---

## Related

- [14-error-handling-strategy.md](./14-error-handling-strategy.md)  
- [11-azure-devops-integration.md](./11-azure-devops-integration.md)  
