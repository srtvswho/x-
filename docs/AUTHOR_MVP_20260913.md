# Three-author $5 screening experiment

Completed 2026-09-14. See [verified results](AUTHOR_MVP_RESULTS_20260914.md).
Original frozen labels/report remain available; separate schema and assistant
semantic review are exploratory revisions, not silently rewritten old outcomes.

User authorized qinbafrank (1,000 fetched / 400 AI), bboczeng (1,500 / 500),
KobeissiLetter (500 / 300), maximum $5 incremental provider spending.
User separately authorized an isolated one-time GitHub Actions entry point.

## Isolation and spending

The dedicated `codex/author-mvp-20260913` branch runs on an explicit campaign
configuration push. No schedule, deployment, master update, subscription, paid
quote service, production database write, or author pool promotion is included.
The public repository uses standard GitHub-hosted runners. Raw public posts and
model outputs are kept in a 90-day Actions artifact, not posted to master.

Before calls, check repository secrets and provider access using GET requests;
check the live Apify event prices and require the reviewed model. No credential
value is printed or exported. DeepSeek rates reviewed 2026-09-13:
Flash peak input $0.30/M, output $1.20/M; off-peak is cheaper. No expensive fallback.
Sources: https://api-docs.deepseek.com/quick_start/pricing/ and
https://docs.apify.com/api/v2/actors-runs-post . Pricing expires September 16 UTC.

Campaign caps: Apify $1.50; AI $3.40; $0.10 remains unspent contingency.
Every Apify run has a server-side `maxTotalChargeUsd`, item cap, timeout and no
automatic restart. The AI reservation uses UTF-8 input bytes plus 1,024 envelope
tokens and the full 2,400-token output allowance at peak prices. Integer
micro-dollar reservations round upward, persist before requests and never refund.
Timeouts/unknown outcomes retain the full reservation. No automatic paid retries.

A claim is committed to the dedicated branch **before** any paid work. Subsequent
dispatches or reruns stop at this claim even if artifacts were lost, preventing
fresh-budget repeats. Recover by inspecting the Apify run IDs, claim, ledger,
raw/labels and receipt artifact. Never delete the claim or start another campaign
to bypass the budget. A resumed controller must consume the original ledger.

## Frozen sampling and validation

12 monthly strata: September 2025 through August 2026, bounded Latest searches.
Existing raw posts from the compressed master snapshot are reused first. No
reply/retweet scraping; bboczeng has a frozen broad topic query. Free topic and
forward-cue rules then deterministic month-balanced sampling select AI inputs.
No forward returns enter this selection. Long posts are excluded rather than
silently truncated. Missing quote context, uncertain attribution, conditions,
news and retrospective commentary cannot become strict signals.

Only the original text and timestamp enter the model. Every signal must have an
exact supporting excerpt, explicit security identity, direction and domain.
Kobeissi is restricted to SPX/SPY, NDX/QQQ, gold/GLD and BTC. Model classifications
are exploratory, not human-reviewed certainty.

5/20/60 observed-session outcomes start at the next calendar-date market open.
Missing or immature prices remain missing. Equity benchmarks are SOXX for
semiconductors/memory, otherwise SPY. Macro uses matched asset return with an
always-long baseline; matched-asset excess cannot establish alpha. Price data
use existing Yahoo payloads first and at most 40 free-symbol fetches.

Report all calls, earliest-in-sample calls and nonoverlapping author/ticker events.
Show domains, unique tickers, clusters, concentration and prior other-ticker
20-session records with exit dates strictly before each post. No confidence
thresholds are tuned and no existing focus-signal policy is modified. These are
descriptive event returns, not portfolio CAGR or proof of persistent alpha.

## Verification

`python -m unittest discover -s tests -p 'test_author_mvp.py' -v`

The claim, provider run IDs, reservation ledger, token usage, sample coverage,
model labels and outcome report jointly determine completion. A successful push
or workflow start does not establish a finished experiment. Missing credentials,
provider errors, price gaps and budget stops must be reported explicitly.

## Authorized continuation 2026-09-14

Original run 34762158376 stopped on malformed JSON after 225 labels. All 3,000
raw posts and 1,023 selected candidates are preserved in artifact 10318939179.
The original 82 ledger rows reserve $1.494501, including all previously billed
attempts. The new entry point verifies exact ledger/selection/coverage hashes
before any model request and uses that same ledger. No scraper credential or
scraping call is available to the continuation. A separate durable continuation
claim prevents concurrent/fresh-state repeats; it grants no new spending budget.

The observed missing opening quote around a numeric post ID can be repaired
offline with an exact syntax rule and strict ID/schema checks. Original model
responses remain unchanged. New malformed batches are isolated; other batches
continue. Each known-invalid-output post has at most one single-post retry under
the cumulative budget. Unknown network/billing outcomes stop paid work. All
remaining failures are listed, and the free report stage still runs.

Frozen author selection, raw texts, extraction prompt, semantic gates, horizons
and statistical policy remain unchanged. Existing labels are reused, not billed
again. Completion requires counts reconciled to 1,023 selected posts, explicit
price gaps/immature outcomes, the full cumulative cost receipt, and report review.
