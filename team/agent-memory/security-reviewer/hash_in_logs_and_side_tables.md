---
name: hash-in-logs-and-side-tables
description: T-22-3 — unkeyed hash of low-entropy text in logs is reversible; new side tables holding PII-derived hashes escape purgeBuyerPii/redactOrders
metadata:
  type: feedback
---

2026-09-29 T-22-3: when a card replaces logged text with a hash, check the hash is keyed (hmacHex with a server secret). Unkeyed sha256Hex of a templated subject (shop + profit) was brute-forced in seconds (S-38). Prove with a plain node script plus a one-line test `hash !== sha256Hex(text).slice(0,16)`.

Also check every new table holding PII-derived data (even an HMAC) against `purgeBuyerPii` (orders/jobs.ts) and `redactOrders` (privacy/service.ts): orders rows are never deleted by those paths, so an `onDelete: cascade` FK to orders does NOT give 30-day/erasure coverage.

**Why:** the "it's hashed / it cascades" argument looks sufficient in the author's report and a previous review run accepted it.
**How to apply:** grep the new table name in both purge paths; grep log fields ending in Hash for sha256Hex.
Related: [[link-route-token-and-pii-log-pattern]]

2026-09-29 T-22-3 r2: in zsh, `env $E cmd` with a multi-var string does NOT word-split; export the TEST_* vars instead, or the DB name swallows the rest (3D000). Also check sibling log fields: mailer `toHash` is still unkeyed sha256 (pre-existing, Low follow-up).
