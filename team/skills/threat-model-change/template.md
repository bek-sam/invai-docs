# Threat model: T-<n>-<k> <title>

- Author: <role>, <date>. Reviewed by: security-reviewer (<verdict>)
- Risk flags: <tenancy, pii, auth, webhooks, files, payments, ai, …>

## 1. What changes
<2–4 lines. New or changed procedures, tables, jobs, webhooks, files, prompts, outbound calls.>

## 2. Entry points
| Entry point | Who can call it (session kind + permission) | Input trusted? | Tenant comes from |
|---|---|---|---|
| `<contract path>` | user with `<perm>` / floor session / station token / vendor / anonymous / webhook / job | Zod-validated? | session, never the body |

## 3. Data touched
| Data | PII? | Encrypted? | Retention | Who may read it |
|---|---|---|---|---|

## 4. Threats (STRIDE-style, InvAI cases)
| # | Threat | Example on this change | Control in place (file:line) | Gap? | Test that proves it |
|---|---|---|---|---|---|
| 1 | Cross-tenant read/write | shop B passes shop A's id | `withTenant` + RLS; NOT_FOUND | | |
| 2 | Privilege escalation in a tenant | presser calls an office procedure | contract `permission` + `authz.test.ts` | | |
| 3 | Spoofed webhook / replay | forged or repeated delivery | signature on raw body, delivery-id unique index | | |
| 4 | Foreign id / S3 key from input | `fileKey` of another company | `isCompanyKey`, service id validation (S-26) | | |
| 5 | PII leak | buyer address in logs, errors, prompts, analytics | redaction, `stripPiiDeep`, `shipTo` needs `orders.manage` | | |
| 6 | Injection / SSRF / ReDoS | user regex, URL from a provider | `unsafeRegexReason`, host allowlist, timeouts | | |
| 7 | Prompt injection / excessive agency | buyer personalization text steers the model | delimited data block, read-only tools, schema-validated output | | |
| 8 | Abuse without limits / denial of wallet | bulk import, AI loop | plan limits, credits, rate limits, size quotas | | |
| 9 | Fail-open | Redis timeout skips a check | fail closed or alert | | |
| 10 | Double side effect | label bought twice on retry | idempotency key, state guard | | |

## 5. Worst outcome
<one sentence: what's the worst thing an attacker or a bug could do through this change, and to how many shops.>

## 6. Decisions and follow-ups
- Required before merge: …
- Accepted risk (owner-approved if High): …
- New finding ids in `security/v1-review.md`: …
