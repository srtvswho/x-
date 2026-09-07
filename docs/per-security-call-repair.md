# Per-security call repair — 2026-09-07

Historical post interpretation is complete, but a post-level direction was being
expanded to every mentioned security. This incorrectly attributed Jukan's
2025-07-15 Hynix/Samsung outlook and 2025-08-01 Samsung outlook to MU, and
Serenity's September 2025 TSM recommendations to comparison stocks.

Both tracking selectors now consume shared per-security evidence. Unreviewed
multi-security posts stay visible in the raw feed and in review coverage debt,
but cannot manufacture calls. Exact manual corrections are pinned to both raw
text and the reviewed extraction payload. Later interpretations invalidate them.

The focused review stage reuses saved summaries/claims, supplies the original
post, requires a decision for each candidate and exact author quotations for
non-neutral decisions, and retains every original extraction. It checkpoints
200-post batches and defers failed records, allowing two batch attempts before
blocking unresolved debt. The initial snapshot had 1,076 candidates; four exact
reviews leave 1,072 for adjudication. The campaign uses the same existing AI_RUN_ID
and cumulative $30 cap. Daily new posts use the existing daily extraction budget.
No wholesale prompt-version upgrade or post-history re-extraction is required.

Explicit company-name aliases are normalized; actual ADR symbols are preserved.
Exchange-qualified Korean, Japanese and other supported foreign listings use
native-currency chart closes. The provider symbol/currency must match, market
local dates are retained, and no future price is substituted for a missing anchor.
The price audit remains open for unsupported/ambiguous securities. A price-gap
campaign does not repeat indefinitely unless a tracked repair revision changes.

Verified issuer references:
- https://investors.micron.com/overview/default.aspx (MU)
- https://investors.credosemi.com/resources/investor-faqs/default.aspx (CRDO)
- https://www.skhynix.com/ (SK hynix)
- https://finance.yahoo.com/quote/000660.KS/
- https://finance.yahoo.com/quote/285A.T/

Read-only live chart checks confirmed 005930.KS/KRW, 000660.KS/KRW and 285A.T/JPY.
The database regression restores Jukan MU to 2025-09-05 and leaves SNDK at
2025-09-30, pending any earlier independently supported evidence. Stored raw
history continuity remains unverified; these are earliest identified calls,
not proof of first-ever X posts or actual executions.

## Production JSON-contract recovery

The first targeted run revealed a provider-boundary defect: DeepSeek receives
`response_format=json_object`, not the Python schema. The prompt described the
meaning of a decision but did not specify the `decisions` envelope, exact field
names, or direction enum. Responses were valid JSON but mostly unusable by the
strict validator (399 of the first 400 attempted records failed; one succeeded).
This was not a failure of the original historical post extraction.

The v2 request includes the exact schema and a compact example in the system
message. Evidence validation stays strict. Existing valid/manual reviews remain
valid; only unresolved records receive the corrected request. Semantic retries
include the prior validation error to avoid replaying a completed request hash.
Paid structured responses, including invalid ones, are retained in a separate
`call_attribution_attempts` table without modifying original interpretations.

A six-post canary must reach 80% validation success before 200-post batches are
allowed. A majority-failing batch or exhausted retry debt blocks the campaign
and persists a blocked gate, preventing repeated scheduled spending without a
new code-repair revision. Checkpoints include per-security pending debt rather
than reporting complete merely because post extraction is complete. The stable
campaign ID, original ledger, and cumulative $30 cap are unchanged. Production
acceptance still requires final attribution, price-gap, and live-page checks.

## Exact evidence display-format recovery

The corrected contract resolved most records, but production paused with 143
remaining validation failures. Inspection of the retained paid responses found
many quotes differed only by collapsed newlines/spaces or decoded `&amp;`.
The v3 validator maps only those reversible display differences back to an exact
contiguous substring of the stored raw post and saves that original substring.
It does not fuzzy-match, ignore case, remove words, alter punctuation, splice
sentences, or accept ellipses in place of text.

Before any new paid requests, v3 revalidates saved v2/v3 responses against the
same extraction ID and raw-post hash. Valid/manual reviews remain untouched;
only remaining unresolved posts can receive new reviews under the same budget.
Original model payloads remain in the attempts table for audit. The canary and
failure gate still apply. Tests cover whitespace/entities, raw-offset fidelity,
stale inputs, paraphrases, negation, changed tickers and invented quotations.

The v3 production recovery restored 103 paid responses without API calls. Its
six-record canary then accepted four and deferred two long recommendation lists.
The v4 follow-up distinguishes valid JSON with per-record evidence debt from a
broken provider contract: evidence failures remain pending and get bounded
retries, while untouched records can continue. Exhausted debt still blocks final
publication. Strict standalone Buy/Strong Buy/Hold/Sell/Strong Sell lists can
provide deterministic evidence: the saved quote includes the literal heading
through that ticker, with all intervening tickers intact. A direction must match
that ticker's heading, conflicting labels are rejected, and prose/separators
terminate the list. This does not transfer one company's recommendation to peers.

## Final four exact-raw adjudications

After v4, only four posts remained after two bounded review attempts. They were
read directly and pinned to their exact raw and extraction hashes, with zero new
AI calls: Serenity 1993327956585070661 is bullish NBIS only (other names are
comparators/partners); TradexWhisperer 2054266085889982497 and
2055007237207453843 explicitly argue for MU/SNDK rerating, without making WDC/STX
short calls. FeroceResearch 2016725956002537717 recommends broad portfolio themes;
appended tags alone are not promoted into individual securities' calls. This
sector view remains available in raw intelligence. No first-date overrides were
introduced. The new campaign revision applies these four reviews and resumes
final price/publication stages, retaining the original cumulative cost ledger.
