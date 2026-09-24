---
name: import-dry-run
description: Run a shop's real marketplace exports through InvAI on an isolated local stack and measure parse rate, SKU auto-map rate, ship-by accuracy and personalization read, with scrubbed evidence for every miss. Use before onboarding a shop, when a shop sends new exports, or after a parser or SKU-mapper change.
---

# Import dry run

Before a shop configures anything, we know in numbers how well InvAI reads its real files, and every miss is a
logged issue with a scrubbed example.

## When to use
- Step 4 of `onboard-shop`, for every new shop and every channel it uses.
- A shop sends exports from a channel or format not seen before.
- After an engineer changes a CSV parser (`invai-backend/src/integrations/channels/csv/parse.ts`) or the SKU
  mapper (`src/modules/channels/sku.ts`, `src/modules/orders/mapping.ts`). Re-run the last dry run and
  compare.

## Steps
1. **Stage the files outside git.** Real exports go in `~/invai-pilots/<shop-slug>/raw/`. Never copy them into
   a repo, a chat or a ticket. Count rows per file (`wc -l`) and note each file's channel and format.
   Supported formats (`CSV_FORMATS`): `etsy`, `amazon`, `tiktok`, `walmart`, `shopify`, `generic`. Compare the
   headers with the fixtures in `invai-backend/src/integrations/channels/csv/fixtures/`.
2. **Use an isolated local stack,** never the shared dev DB other agents use. Follow `isolated-stack.md` (this
   folder): a separate database, a separate Redis DB index, and separate ports.
3. **Create a fresh company** by signing up at the isolated web's `/signup` with a fake email
   (`owner@<shop-slug>.test`). Add the shop's blanks (**Catalog → Blanks** import) and designs if they sent a
   list, so mapping has something to map to.
4. **Import each file** through **Settings → Channels** → **Import** (or **Import CSV** on Today), choosing a
   CSV connection and format. Record the import report: New orders, Updated, Unchanged, Rows failed, and items
   needing SKU mapping. Re-import the same file once and confirm nothing duplicates (import is idempotent on
   channel and channel order id).
5. **Measure the four numbers** with the queries in `queries.sql` (run as `docker exec -i local-postgres-1 psql -U invai -d invai_dryrun_<slug> < queries.sql`):
   - **Parse rate** = rows imported ÷ rows in the file (`import_runs.rows_total`, `rows_failed`, `errors`).
     Target ≥ 99%.
   - **SKU auto-map rate** = order items not in `needs_mapping` ÷ all items, measured twice: before any rules,
     and after you add rules for their scheme (`Suggest mappings`, `Accept N at ≥80%`, `Save as rule`). Target
     after rules: ≥ 95%. For each unmapped SKU pattern, write why (new scheme part, bundle, typo, blank not in
     catalog).
   - **Ship-by accuracy** = orders where InvAI's `ship_by` date matches the marketplace's own ship-by or
     dispatch date (from the export column, or from the shop's dashboard for 20 sampled orders) ÷ orders
     checked. Target 100%; a one-day miss can cost a late shipment.
   - **Personalization read** = personalized items whose text matches the buyer's answer exactly (check 20, or
     all if fewer), plus the count flagged `overflow`, `too_long`, `suspicious_chars` or `empty` in **Catalog
     → Personalization** → Artwork review. Amazon Custom ZIPs: note whether the file was even readable.
6. **Classify every miss** as product wrong (parser or mapper bug), the shop's data unusual, or needs training
   (a setting). Only "product wrong" becomes a product issue.
7. **Make scrubbed evidence.** For each miss, take the smallest set of rows that shows it and run
   `scrub-pii-fixture`: fake names, emails, phones and addresses; keep headers, SKUs, dates, quantities and
   personalization shapes. Save it in `invai-docs/customers/<shop-slug>/dry-runs/evidence/`. The engineer
   turns it into a fixture; you don't edit code.
8. **Log issues** with `triage-support-ticket`: a failed parse or wrong ship-by on a channel = blocks
   shipping; a wrong personalization read = wrong print.
9. **Write the report** `invai-docs/customers/<shop-slug>/dry-runs/<date>.md` from `dry-run-template.md`:
   files, the four numbers per channel, the miss list with classification and issue ids, and readiness
   (`ready`, `ready with workarounds`, `blocked`).
10. **Tear down (required).** In this order (`isolated-stack.md`, "Tear down"): stop the processes you
    started; delete the dry-run company's files from MinIO (they are the shop's real art and CSVs), after a
    dry listing of exactly that prefix:
    ```
    docker exec -e MC_HOST_local=http://invai:invai-secret@localhost:9000 local-minio-1 \
      mc rm --recursive --force local/invai-local/<companyId>/
    ```
    then drop the isolated database and flush Redis DB 7. Real data never stays in a database or bucket
    longer than the dry run.

## Rules
- MUST keep real files and real data local: `~/invai-pilots/` and an isolated local DB only. No shared, test
  or deployed database.
- MUST scrub before anything enters `invai-docs/`. No real name, email, phone, street address or order note in
  the repo.
- MUST measure per channel. A 99% total can hide a 60% Walmart file.
- MUST NOT edit parsers, rules in code or seed files. A needed change is an issue for the owning engineer.
- MUST NOT hand-edit database rows to make a number better.
- MUST NOT send files or results outside this machine. Results reach the shop through the owner.

## Done when
- A dated report exists with parse rate, SKU auto-map rate (before and after rules), ship-by accuracy and
  personalization read, per channel, each with its numerator and denominator.
- Every miss is classified; every "product wrong" miss has an issue id and scrubbed evidence.
- Re-import showed no duplicates.
- The dry-run company's MinIO prefix is deleted (`mc ls --recursive local/invai-local/<companyId>/` prints
  nothing), the isolated database is dropped and processes stopped; `git status` in `invai-docs` shows no raw
  files.

## References
- `isolated-stack.md`, `queries.sql`, `dry-run-template.md` (this folder)
- `invai-backend/src/integrations/channels/csv/` (parsers and fixtures),
  `invai-contracts/src/contract/channels.ts` (`importCsv`, `ImportReport`)
- `invai-docs/research/01-shop-workflow.md` §2 (how each marketplace exports orders and personalization)
- `invai-docs/build/demo-guide.md` steps 2–4
- Related playbooks: `onboard-shop`, `scrub-pii-fixture`, `triage-support-ticket`
