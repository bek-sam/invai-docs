---
name: census-api-requires-key
description: The Census Bureau EITS timeseries data endpoint requires a key even though its variables.json metadata endpoint is keyless
metadata:
  type: feedback
---

The public Census Bureau EITS API (`api.census.gov/data/timeseries/eits/marts`) requires an API
key even for a plain data read, even though `.../marts/variables.json` (metadata) answers keyless.
A keyless GET against the real data endpoint returns an HTML "Missing Key" page (HTTP 200, not an
error status), not JSON.

**Why:** T-18-2's card allowed "at most one keyless GET to the public Census API to record the
fixture"; this call failed as expected, so the fixture
(`invai-backend/src/integrations/market/fixtures/census-marts-448-monthly.json`) was built from
the documented list-of-lists response shape instead of real data. The code and report say so
explicitly rather than presenting constructed numbers as real.

**How to apply:** Before attempting a keyless-fixture recording against a `.gov` statistical API
again, test the *data* endpoint itself, not just its metadata/variables endpoints — they can have
different auth requirements. If a real `CENSUS_API_KEY` is ever obtained, re-record that fixture
for real and confirm `data_type_code: "SM"` / `category_code: "448"` against the live values list
(both were guessed from the documented shape, flagged `[U]` in `providers/census.ts`).
