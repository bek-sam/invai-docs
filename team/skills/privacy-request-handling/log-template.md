# Privacy request log

File: `invai-docs/compliance/privacy-requests/log.md`. Append-only. **No PII.** Ids only.

```
# Privacy requests

| Req id | Received (UTC) | Source | Company id | Channel | Type | Subject ref | Our due | Legal due | Status | Evidence | Owner draft |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PR-001 | 2026-10-02 14:10 | shopify webhook / shop email / buyer email | <uuid> | shopify | export / delete / correct / opt-out / offboard | shopify customer id or channel order id | 2026-10-17 | 2026-11-01 (Shopify 30 d) | open / waiting on shop / in progress / done / escalated | card T-…, counts | OI-… |
```

Notes under the table, one block per request when needed:
```
### PR-001
- Routed to: <shop / owner>, on <date>
- Found: <n> buyer_pii rows, <n> S3 objects, <n> other
- Action: <exported / redacted / deleted>, by <card>, verified by <reviewer>
- Closed: <date>. Missed clock? <no / yes → lesson logged>
```
