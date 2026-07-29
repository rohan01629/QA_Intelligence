# 13 — Future Scalability

**Product:** QA Intelligence MCP Server  

---

## 1. Scalability Goals

Preserve v1 tool contracts while enabling:

- Higher ADO throughput  
- Multi-project / multi-org  
- Stronger semantic duplicate detection  
- Optional server-side drafting  
- Observability at team scale  

---

## 2. Scale Axes

| Axis | v1 | Future |
|------|----|--------|
| Compute | Single MCP process | Horizontally scaled SSE/gateway workers |
| ADO I/O | Per-request REST | Connection pooling, batch APIs, read-through cache |
| Similarity | Feature scorer | Embeddings index (vector DB) behind `SimilarityScorer` |
| Analysis | Rules engine | Hybrid rules + LLM adjudicator port |
| Generation | Cursor-only | Optional `TestCaseDrafter` port |
| Tenancy | One org/project per process config | Multi-tenant config resolver |
| State | Stateless | Optional cache / outbox for reliable writes |

---

## 3. Extension Points (already designed as ports)

```text
AuthProvider          → PAT | OAuth | Managed Identity
SimilarityScorer      → Feature | Embedding | Hybrid
WorkItemRepository    → ADO | mock | recorder
TestCaseDrafter       → (future) LLM provider | Cursor-only null
```

Adding a capability should mean a new adapter, not a new MCP tool — unless product explicitly expands the closed surface via ADR.

---

## 4. Performance Strategies

1. **Parallel inventory tools** (already in workflow).  
2. **Batch work item GET** for enrichment.  
3. **Short TTL cache** for User Story + linked tests keyed by id + revision.  
4. **WIQL result capping** (`top` ≤ 50 for similar search).  
5. **Async everywhere** on I/O.  

Cache must invalidate on write (create/link) for affected story keys.

---

## 5. Multi-Project Support

Phase approach:

1. One project per MCP server instance (v1)  
2. Tool arg `project` override + config allow-list  
3. Tenant middleware selecting ADO client from DI  

Do not silently write across projects.

---

## 6. MCP Surface Evolution

Rules for adding tools later:

- Must serve QA Intelligence (not generic CRUD)  
- Must have ADR  
- Must not break existing tool names/fields (additive changes only)  
- Prefer enriching existing analyze/coverage payloads over new tools when possible  

---

## 7. Reliability Upgrades

- Outbox pattern for create+link eventual consistency  
- Idempotency keys stored against story+title hash to prevent duplicate creates on retry  
- Dead-letter log for failed links  

---

## 8. Compliance / Enterprise

- Secret store integration (Key Vault) via AuthProvider  
- Audit events for create/link (who/when/story/ids)  
- PII redaction in logs for descriptions if required  

---

## Related

- [08-repository-layer.md](./08-repository-layer.md)  
- [12-llm-interaction-flow.md](./12-llm-interaction-flow.md)  
