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

## Durable disabled-job follow-up

The candidate now includes `twitterapi-recovery-candidate.yml`: **manual only, enabled=false by default, exact recovery branch only**. It has no schedule/push trigger and no publication route. It restores current master data into a separate working DB and uploads only a candidate artifact, never commits database files or changes master. No actual state branch or grant has been provisioned.

`GitBranchStore` loads preexisting `state/twitterapi-recovery:state.json`. Before each search, a compare-and-swap Git commit durably stores its 300-credit reservation and pending marker. The request is sent only after remote SHA verification. A validated page is then committed with full raw JSON and next cursor. Interrupted/unknown calls remain pending and cannot be automatically retried. A later authorized invocation continues cached successful pages; it does not start over. Changes to grant configuration or reductions of reserved credits are refused. State writes use only the allowlisted state branch, never checkout/reset/master.

Config must be explicitly reviewed: grant_id, credit_limit, expires_at, max_pages_per_window, mode, exact frozen windows, bonus_only, no_payment_instrument_verified, verified_bonus_credits, bonus_expires_at. Dispatch requires the exact config SHA256 and grant ID. Each invocation caps two additional pages/account, sixteen total; the grant and per-window total caps survive invocations. Initial empty searches remain unverified; an explicit final empty page after validated cached rows may exhaust that window. Runtime never provisions or replenishes grants. Daily requires a matching verified coverage start; catch-up cannot silently become daily.

The Git-backed paging journal is the durable runner's authoritative quota store. The standalone SQLite ledger remains a tested alternative for deployments with a persistent volume; they must not be used as independent double budgets. Balance preflight is a separate read with undocumented tariff and not included in the search-only credit ceiling. No paid balance is accepted.

Remaining owner facts/decisions: exact bonus expiry (or an intentionally shorter approved trial deadline), approved finite search-credit budget, and whether/when to publish recovered data and enable recurring daily operation. Existing TWITTERAPI_IO_KEY and repository Actions token suffice; **no additional credential or card is needed**. State branch provisioning, safe workflow activation and final production integration are implementation gates, not a reason to request another API key. No infinite-free claim; bonus expiry/quota stop preserves existing data.


### Final offline safeguards (87 tests)
- Validate complete durable journal before any provider request; unknown page attempt blocks preflight.
- Explicit `max_balance_reads` (1..16) is immutable and persisted before each read. Unknown reads block retries. Completed cache needs no balance call. Balance query tariff is unknown and is **not** included in the search-credit estimate.
- GitHub job `contents: write` is repository-wide; the state-store implementation, not the token, limits writes to `state/twitterapi-recovery`.
- No actual state branch/grant was provisioned and no new provider request was made. New candidate workflow is not on master and remains disabled by default.
- Daily scheduling/publication and promotion of catch-up coverage into daily coverage are intentionally not activated. The candidate only writes a temporary database artifact; the live dashboard remains unchanged.
- Activation requires a reviewed finite credit/request allowance and deadline (or verified bonus expiry), explicit window/bootstrap scope, and separate deployment/publication readiness. Do not ask for another API key or card.

## Authorized finite trial, 2026-11-15 (not production activation yet)
Owner accepted up to $0.30 bonus credits for Nov 12 onward catch-up and seven days of daily trial, no card/recharge/AI spending. The single grant `bonus-recovery-20261115-7d-30000` caps ALL provider operations at 30,000 credits by permitting only advanced search: reserve 300 credits per attempt, maximum 100 total across all windows, never refund failures. `/oapi/my/info` is excluded because its tariff is undocumented. Official advanced-search tariff is 15 credits per tweet, maximum 20 per page; successful empty pages cost at least 15 and fit the 300 reservation. Actual bonus debit remains unobservable; reservation is conservative, not claimed actual usage.

Grant execution expires 2026-11-22 16:10 Asia/Shanghai. This is our seven-day stop deadline, NOT a claim about account bonus expiry. Provider expiry/insufficient credit/error also stops with no retry. Historical start is 2026-11-12 00:00 Asia/Shanghai, overlapping old data safely by ID. Full immutable scope contains 88 author-windows, including seven prospective daily windows; no future window can execute before its end. Initial selection is only the first historical day for eight accounts. First incomplete account stops the invocation. Each account has at most ten pages and all runs share the single 100-page ceiling.

The existing validation workflow's recovery-branch manual route now runs this candidate instead of the obsolete smoke. It requires both AI switches false and dry run true. It never publishes or changes master. Prior completed captures reconstruct a temporary working DB on each run. Production integration and daily promotion/scheduling remain engineering gates after this initial validation; authorization does not establish that they already work. No automatic daily job has yet been activated.
