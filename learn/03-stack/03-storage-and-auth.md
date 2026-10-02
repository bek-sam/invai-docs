# Lesson 3.3 — S3/MinIO for files, Better Auth for sign-in

## 1. In one sentence
InvAI keeps every real file (print art, gang sheets, labels) in S3-shaped object storage —
MinIO locally, real S3 in the cloud — addressed only by key, never shipped as bytes through the
API; and it signs people in with Better Auth, a self-hosted, free library that keeps every
user's data in InvAI's own database instead of a third-party identity vendor's.

## 2. Why it exists
Two very different problems, one shared theme: both choices were made to avoid handing a
third party control over data that (a) is large and would be expensive to proxy through the
API, or (b) is identity data that matters a lot for the Amazon SP-API security review (module
09) and for building a tablet PIN-login scheme no hosted vendor offers out of the box.

## 3. How it works

### Object storage — why S3-shaped, and why MinIO locally
`invai-docs/research/05-tools-hosting.md:254-284` compares S3 against Cloudflare R2, Backblaze
B2, Tigris, GCS and DigitalOcean Spaces for cost, compliance and operational weight. S3 (behind
a CloudFront flat-rate plan) wins on **compliance**: "KMS encryption; Object Lock; lifecycle
rules for the 30-day PII deletion; free gateway endpoint; access logs" — all first-class AWS
features that matter directly for the Amazon SP-API security review and for the 30-day PII
expiry rule the platform needs regardless of provider. R2's selling point (no egress fees)
stops mattering once you're behind a flat-rate CDN plan anyway.

Locally, the stack runs **MinIO** (`invai-infra/local/docker-compose.yml:35` —
`quay.io/minio/minio:latest`) because MinIO speaks the exact same S3 API — the backend's own
code never needs to know whether it's talking to MinIO or real AWS S3. (The image comes from
`quay.io`, not Docker Hub, because `minio/minio` on Docker Hub was discontinued — noted in
`CLAUDE.md`'s environment section.)

The actual rule, enforced in code, is: **the backend and `invai-imaging` only ever pass S3
*keys* around, never file bytes.** `invai-backend/src/lib/s3.ts:52` —
`objectKey(companyId, kind, ext, id)` — builds a predictable key path per company and kind;
`:66` — `isCompanyKey(companyId, key)` — checks a key actually belongs to the calling tenant
before it's ever read or written, the storage-layer equivalent of RLS. The browser gets a
short-lived **presigned URL** (`:74` — `presignPut`, `:103` — `presignGet`) to upload or
download directly against the bucket — the backend's own request body never carries the file.

### Better Auth — self-hosted identity, including a custom PIN scheme no vendor sells
`invai-docs/research/06-tools-backend.md:120-149` opens with a blunt finding: **"Nobody offers
shared-tablet PIN login."** None of the hosted identity providers researched (Clerk, WorkOS,
Kinde, Auth0, Stytch, Supabase Auth, Zitadel) support "shared tablet, staff switch in with a
4-6 digit PIN" as a built-in feature — the standard design even with a hosted vendor is "the
tablet authenticates as a device/station credential, and staff switch with a PIN checked by
*your own* backend." Since you'd be writing that custom layer either way, the research scored
**Better Auth at 9.5/10**: it's MIT-licensed, costs $0 at every volume tier (vs. Clerk's
$25-125/mo once a shop has enough staff to need the B2B org add-on, or Auth0's $150-1,300/mo),
and — the compliance point that matters most — "Your Postgres, your region (best for the
Amazon review)." A hosted vendor would mean staff identity data living outside InvAI's own
database, which is one more sub-processor to disclose and one more vendor whose breach becomes
InvAI's incident.

`invai-backend/src/auth.ts:10` imports `organization` and `twoFactor` from
`better-auth/plugins` — companies *are* Better Auth "organizations" (one company = one org,
with a `type` field), and the 2FA plugin gives TOTP/backup-codes for free rather than being
hand-rolled. The floor app's station-token + PIN scheme sits *beside* Better Auth, as its own
custom layer, exactly as the research predicted every option would require — module 09 covers
it in full.

## 4. In our code
- `invai-backend/src/lib/s3.ts:52,61,66,74,103` — `objectKey`, `isSafeKey`, `isCompanyKey`,
  `presignPut`, `presignGet`: the whole "keys only, presigned, tenant-checked" pattern in one
  file.
- `invai-infra/local/docker-compose.yml:35` — the MinIO image and why it's from `quay.io`.
- `invai-backend/src/auth.ts:10,43-50` — Better Auth's `organization`/`twoFactor` plugins and
  the comment explaining "companies are organizations."
- `invai-docs/research/05-tools-hosting.md:254-284` — the object-storage comparison table.
- `invai-docs/research/06-tools-backend.md:120-149` — the auth comparison table, including the
  "nobody offers shared-tablet PIN login" finding.

## 5. What it uses
- **S3 (MinIO locally)** — object storage for every real file; code addresses it only by key,
  never by shipping bytes through the API body.
- **AWS KMS, S3 Object Lock, lifecycle rules** — the compliance features that made S3 beat R2
  despite R2's egress-fee advantage, once a CDN flat-rate plan is in place.
- **Better Auth 1.7.5** — self-hosted auth; organization + two-factor plugins; $0 cost, data
  stays in InvAI's own Postgres.

## 6. Try it yourself
1. With the local stack up, open the MinIO console (usually `http://localhost:9001` — check
   `invai-infra/local/docker-compose.yml` for the exact mapped port) and log in with
   `invai` / `invai-secret` (from `CLAUDE.md`'s Environment section). Browse the `invai-local`
   bucket and find a design or gang-sheet file; note that its key path encodes a company id.
2. Open `invai-backend/src/lib/s3.ts` and read `isCompanyKey` — write down, in your own words,
   what it's checking and why a presigned URL alone (without this check) wouldn't be enough.
3. Sign in to the web dashboard, then look at Better Auth's session cookie in your browser's
   dev tools (Application → Cookies). Confirm it's a plain HTTP-only cookie, not a token from
   an external identity provider's domain.

## 7. Common mistakes
- Sending a file's bytes through an oRPC procedure's request/response body "because it's
  simpler for this one case." The whole point of presigned URLs is that large files never
  touch the backend's own request handling — a one-off exception defeats that and can also
  blow past typical body-size limits.
- Assuming MinIO and S3 "probably behave the same" without checking `isCompanyKey` and
  `isSafeKey` actually run against both — a local-only shortcut that skips these checks would
  pass locally and fail the real tenant-isolation guarantee in production.
- Reaching for a hosted auth vendor "because it's less code to write" without checking
  whether it actually supports the floor's PIN-login requirement — per the research, none do,
  so the custom layer has to be written either way; Better Auth at least keeps it in one
  Postgres database instead of straddling two systems.

## 8. Check yourself
<details>
<summary>1. Why does the backend pass S3 *keys* around instead of file bytes, even between
its own modules?</summary>

So large files never pass through the backend's own request/response handling — the browser
or `invai-imaging` talks to the bucket directly via a short-lived presigned URL, which is
cheaper and avoids body-size limits.
</details>

<details>
<summary>2. What finding from the auth research most directly explains why InvAI didn't just
buy a hosted identity provider?</summary>

"Nobody offers shared-tablet PIN login" — every vendor researched would still require a
custom station-token + PIN layer built on top, so the decision became "self-host the
*base* auth cheaply (Better Auth, $0, your own Postgres) and build the custom layer once,"
rather than paying for a vendor and still building the same custom layer beside it.
</details>

<details>
<summary>3. What does `isCompanyKey` protect against that a presigned URL alone does not?</summary>

A presigned URL only proves the holder was authorized to get *that specific* URL at
generation time; `isCompanyKey` is a second check, at generation time, that the key path
actually belongs to the calling tenant — preventing a bug elsewhere from generating a
presigned URL for the wrong company's file in the first place.
</details>

## 9. Words to know
- **Presigned URL** — a time-limited URL to directly PUT or GET one specific object in a
  bucket, generated by the backend but used by the browser or another service without the
  backend proxying the bytes.
- **Object key** — the path-like string identifying one file inside a bucket; InvAI's keys
  encode the owning company so storage-layer checks (`isCompanyKey`) are possible.
- **Better Auth organization** — Better Auth's built-in multi-user-group concept; InvAI maps
  one company to one organization.
