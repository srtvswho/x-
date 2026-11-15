# TwitterAPI.io recovery candidate (offline, NOT activated)

## Verified

[Manual pilot #47](https://github.com/srtvswho/x-/actions/runs/43688297896), source `84ba1ce`: 6 Jukan + 1 Serenity records validated, 2 search pages, both `page_cap_partial`. Recharge delta 0; bonus delta unavailable. No ingestion, checkpoint changes, AI calls or publication. Receipt fixture contains actual sanitized log evidence, not raw tweet payload. Contract tweet fixtures are synthetic. Do not rerun the pilot to manufacture fixtures.

The source snapshot at base `a958994` contains 52,714 raw posts. All eight old scrape-state last-fetched times are 2026-11-12. Old latest-post time is not proof of complete coverage and must not seed a verified coverage watermark without explicitly declaring the new bootstrap range.

## Proposed execution shape

1. Restore current production snapshot to a **separate working copy**, retain original compressed DB and a verified backup. Never overwrite source snapshot from an old branch.
2. Record independently approved grant: total search-credit allowance, exact expiry, no paid balance/instrument, verified available bonus and its actual expiry. The smoke's Nov 15 exception is **not** a durable quota mechanism and is not imported by the recovery module. The documented API exposes recharge balance only, so cannot silently assert bonus remaining.
3. Keep one durable SQLite quota ledger across all runs, including failed attempts, separate from disposable Actions workspace. Reserve worst-case 300 credits before every search page. Never refund unknown/failed calls; grant limits/expiry immutable; repeated logical page IDs blocked. If ledger inaccessible, stop. Fresh workspace = missing ledger, NOT a fresh budget.
4. Catch-up is separate from daily: explicitly reviewed bootstrap per author, oldest-first windows <=24h. At most 2 pages per author and 16 pages total per logical run (4800 reserved search credits / $0.048 ceiling under documented 20×15 tariff). This is a proposed cap, not permission to spend it. Balance-query costs are outside that search cap and require their own accounting; don't silently add balance calls.
5. A window truncated at cap, malformed page, bad author/time/ID, stalled cursor or unknown empty response does not advance coverage. Stop and report, never automatically restart the same window from page 1. A bounded checkpointed continuation requires saved response/cursor evidence before further live expansion. Current candidate deliberately fails closed rather than offering automatic catch-up continuation.
6. Bind the requested handle/start/end to each captured Window and reject missing or mismatched scope, then validate all records before atomic insertion + coverage update. Existing raw text, IDs, interpretations and legacy scrape_state remain untouched; duplicate IDs skip, conflicting identity blocks. Store coverage independently of latest post. Daily and catch-up streams remain independent; do not auto-promote catch-up coverage to daily. After verified contiguous catch-up, explicitly promote the boundary with evidence and fresh review.
7. Daily needs verified starting coverage and a <=24h gap. Larger gaps route to separate catch-up plan, not expensive implicit expansion. Freeze UTC end time at run start, use [start,end) windows with since_time/until_time and string IDs. Do not use last-tweet time as completion.
8. Fetch, ingestion/coverage, AI summary and publication receipts remain separate. AI/model/price requests remain disabled in validation. Existing summaries can stay visible with dates; unavailable/expired quota is not 'no new posts' or healthy.
9. Validate all 8 accounts against temporary DB and approved bounded live scope before changing daily entrypoint. Then review production diff, backup/concurrency/CI gates, and explicit publication scope. Verify online manifest/data freshness after publication; later scheduled success remains a distinct check.

## Current implementation and blockers

- `twitterapi_io.py`: strict response parsing, dedupe, fixed official endpoints, no redirects/retries, <=16 page budget, free-tier request spacing.
- `twitterapi_recovery.py`: offline planning + durable immutable quota reservations. **No CLI activation, workflow/schedule or automatic grant creation.** Caller supplies reviewed grant and durable storage.
- Transactional ingest candidate and offline apply_captured_batch integration are independent of the old Apify job. all_eight_planned_windows_verified only covers those supplied windows, not final-target freshness. No existing daily workflow altered.
- Need real full response fixtures (only capture during the next authorized useful fetch), final profile/empty-window policy, durable ledger placement and atomic persistence across Actions, explicit grant/bonus expiry, continuation cache and daily-boundary promotion design.
- Do not promise permanent free service: sign-up bonus is finite and expires. [Official pricing](https://twitterapi.io/pricing/details) says sign-up/bonus credits expire after 31 days; actual grant date/expiry still needs account evidence.
- Do not merge current PR merely to test. Production and eight-account live recovery remain pending.
