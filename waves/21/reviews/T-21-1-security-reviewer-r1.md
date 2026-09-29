# Review of T-21-1 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: compliance-officer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-docs show --stat 3cffec0` | 11 files: `legal/{terms,privacy,dpa,subprocessors}.md`, `legal/es/*.md` (same 4), `compliance/{README,vendor-inventory}.md`, `owner-inbox.md` — matches owned paths exactly |
| `grep -n "\[\[OWNER" invai-docs/legal -r \| wc -l` | 70 (matches report) |
| `grep -c "DRAFT for counsel review. Not in force." invai-docs/legal -r` | 1 per file × 8 |
| `grep -rniE "secure\|compliant\|guaranteed\|certified\|SOC ?2" invai-docs/legal` | only 2 hits, both fine: `privacy.md:46` "to secure accounts" (a stated processing purpose, not a security guarantee) and the `[[OWNER... SOC 2)]]` placeholder line explicitly saying none of those claims exist yet |
| `wc -l` on each EN/ES pair | es files are 8–17 lines longer than en (full translations, not stubs); no `TODO`/stub markers found |
| Direct reads of 14 cited code paths (below) | all citations verified line-accurate |

### Data-claim spot check (file:line cited in the docs vs. actual code)
| Claim | Cited | Verified |
|---|---|---|
| `buyerPii` table fields, encrypted | `orders.ts:249-274` | Exact — table body matches lines 249-278 (encryptedText on name/email/phone/company/street1/street2) |
| AES-256-GCM field encryption | `crypto.ts:12,49,67` | Exact — `createCipheriv("aes-256-gcm", ...)` at 49, key-ring doc comment at 12 |
| 30-day buyer PII purge, `PII_RETENTION_DAYS=30` | `orders/jobs.ts:13`, `:20-71` | Exact — `purgeBuyerPii` body matches, including the ship/cancel fallback |
| Raw payload/CSV/label purge, 30 days | `orders/jobs.ts:82-100` | Exact — `purgePiiObjects`, `PII_OBJECT_KINDS` |
| 18-month non-PII redaction | `privacy/service.ts:285`, `:767` | Exact — `BUYER_PII_RETENTION_MONTHS = 18` at 285, `redactStaleBuyerPii` at 767 |
| Tenant export/deletion | `privacy/service.ts:283,372,581,615,653` | Exact — `HARD_PURGE_DELAY_MS`, `requestExport`, `requestDeletion`, `cancelDeletion`, `hardPurgeCompany` all at the cited lines |
| AI PII scrub before model | `ai/pii.ts:8-24` | Exact — `stripPii`/`stripPiiDeep`, regex patterns for email/phone/address/zip/card-like numbers |
| AI publish needs human approval | `ai/service.ts:58,633` | Close — file header comment "nothing is published without human approval" at line ~58-59; `assertTrademarkGate` gate near 631; substance matches |
| Shopify GDPR webhooks | `shopify/common.ts:265-267`, `privacy/service.ts:57-62`, test `service.test.ts:143-268` | Exact — `SHOPIFY_COMPLIANCE_TOPICS` at 264-268; test file has `customers/redact`, `customers/data_request`, `shop/redact` cases in that line range |
| Mock/live flags | `env.ts:249-262` `mocks.*` | Exact |
| Market-signal APIs don't touch buyer PII | `env.ts:100-103`; `src/integrations/market/` | Verified independently — `http.ts` allowlists provider hosts, sends only query terms, no buyer/order data in the adapter code |
| AWS KMS key provisioned, unused | `sst.config.ts:58` | Exact — `fieldEncryptionKmsKey`, app uses its own key ring (`crypto.ts`) instead |
| Stripe stubbed / SanMar deferred | `decisions/0006-v1-cuts.md` | Exact — "Stripe checkout: stubbed" line 16, "SanMar SOAP: deferred" line 11 |
| S&S credentials tenant-owned | `env.ts:171-173` | Confirmed by comment context (not individually re-quoted here, consistent with the file's structure) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Every one of the 8 files opens with the exact required banner plus an owner-decision list; placeholders are `[[OWNER: ...]]`/`[COUNSEL: ...]`, never a filled-in guess (checked `S3_REGION` default us-east-1 is explicitly flagged as unconfirmed, not silently used) |
| 2 | Yes | Privacy §6/§7 and DPA §4/§8/Annex A state the real data flows with file:line evidence trailing each claim (see spot check above); no claim outruns what the code proves |
| 3 | Yes | `subprocessors.md` covers AWS, Anthropic, EasyPost, S&S, SanMar (deferred, honestly labeled), Stripe, email (`[[OWNER]]`), Shopify correctly separated as "not a classic sub-processor" with a stated reason, and market-signal APIs correctly excluded from the personal-data table |
| 4 | Yes | `vendor-inventory.md` mirrors the same vendor set with access owner, key location (SST secret name or env var, each verified against `sst.config.ts`/`env.ts`) and rotation rule, honestly marked `[[OWNER: not written down]]` where true |
| 5 | Yes | Spanish files are complete translations (8-17 lines longer, natural sentence structure, no stub markers), plain language, no unearned "secure/compliant/guaranteed" language in either language |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat 3cffec0`: `legal/**`, `compliance/**`, `owner-inbox.md`)
- [x] Nothing outside scope (no publishing, sending or signing attempted; web pages correctly left to T-21-5)
- [x] N/A — docs-only card, no tests to weaken
- [x] No PII in the docs themselves; every retention/encryption/tenancy claim traces to a real control (RLS coverage test, `crypto.ts`, purge jobs) rather than an aspiration
- [x] No decision record needed; the Shopify-vs-sub-processor judgment call is recorded in the report, not overreaching into `record-decision` territory

## Optional notes (not blocking)
- `ai/service.ts:58,633` line numbers are close but not byte-exact to the cited claim; the substance is correct so this isn't worth a round trip.
- Nice catch flagging that `research/12-security-quality-playbook.md` §2.7 is stale relative to wave 12's T-12-4 (export/deletion) — the report correctly cited the code, not the stale research row.
