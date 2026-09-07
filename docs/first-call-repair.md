# Historical call tracking repair — 2026-09-06

The tracking table previously chose its first call after cutting events to 370 days.
It also mixed multiple interpretations of a post, allowing an obsolete long/short
classification to survive a newer neutral, disclosure, retrospective or relayed view.

The repair:

- Selects the latest interpretation per post before filtering direction and flags.
- Anchors tracking and price lookup to all stored history. UI windows filter the
  latest directional activity without moving the anchor.
- Uses legacy Serenity predictions only where the raw post has no newer extraction.
- Shows earlier mentions as source evidence, without asserting that a mention is a call.
- Reports incomplete history and earlier unprocessed posts. Performance is explicitly
  a fixed-direction sample return, with direction changes disclosed.
- Replaces uneven author/date/ticker historical filtering with a resumable queue for
  all eight authors. Every successful extraction is committed as it completes.

## Validation on the September 6 production snapshot

87 targeted tests passed; one existing optional integration test skipped. Full HTML
build passed. On the initial read-only snapshot, 620 author/ticker rows become 643;
72 anchors move earlier, and one moves later following an authoritative reclassification.
527 of 643 rows already have cached prices before the production price refresh.
Missing prices remain empty until the correct ticker/date is fetched.

Jukan MU has 33 earlier mentions; SNDK has 14. These are not silently promoted to
long calls. Their recognized directional starts remain June 24 and August 5 UTC
(June 25 and August 6 in Beijing) until consistent historical extraction establishes
earlier directional evidence. Stored posts are not proof of complete raw coverage.

The all-author extraction plan contains 36,525 posts missing the current prompt
version, including older interpretations. This count is not a count of missed calls.
No paid historical extraction was performed during local validation.

## Resume historical extraction

GitHub Actions: `Signalboard Historical Extraction Repair`, workflow file
`.github/workflows/signalboard-history-rebuild.yml`.

Run manually on master. `apply=false` only produces the coverage/queue report;
`apply=true` runs up to `batch_limit` posts (default 400, maximum 500). The workflow
uses the existing DeepSeek route with a $2/run and $3/day cap and does not enable
OpenAI or change guardrails. Completed posts are excluded on subsequent runs.
It checkpoints extraction, refreshes prices, rebuilds and publishes the dashboard.
Reports distinguish remaining extraction work from unverified raw coverage.

The queue processes never-extracted posts first, oldest first per author, and shares
each batch among all eight authors. It then upgrades old prompt versions. It does
not initiate additional historical scraping or infer full coverage from endpoint dates.

## Execution verification — September 7

The latest daily database still has 36,525 posts requiring extraction or an upgrade.
The daily job's historical step is disabled by its fixed expensive-job gate; daily
success does not mean historical extraction ran. The dedicated manual workflow is
the supported execution path. No paid extraction was run in this verification.

| Author | Pending current extraction | Never extracted |
| --- | ---: | ---: |
| Jukan | 1,692 | 509 |
| Serenity | 6,916 | 5,975 |
| Zephyr | 5,950 | 4,358 |
| Austin | 1,346 | 763 |
| DGretta | 2,780 | 1,709 |
| Feroce | 3,294 | 1,580 |
| Tradex | 10,087 | 7,392 |
| gsmferrari | 4,460 | 2,754 |

The runner now verifies that every attempted post has the current extraction in
the database. A zero subprocess exit with missing rows fails the batch. Partial
failures, launch failures and interrupts preserve a report and completed rows;
the workflow checkpoints that report with the database even when extraction fails.
Reports distinguish a completed batch from completed stored-history extraction;
neither asserts that raw historical scraping is complete. The UI also discloses
older interpretations awaiting review before each tracking start.

Validation: 75 tests passed, one optional integration test skipped; the full HTML
build passed on the September 7 snapshot. All eight authors are present across
643 tracking rows; 530 have cached return prices (82.4%), 113 remain missing.
Jukan's recognized starts still remain MU June 24 and SNDK August 5 UTC, pending
the historical extraction. No dates or returns were filled by guessing.

To execute: open Actions → Signalboard Historical Extraction Repair → Run workflow
on master, set apply=true and batch_limit=400 (maximum 500). Existing limits remain
$2 per run, $3 per day, 500 API attempts including retries. Inspect batch_status,
resolved_this_run and pending_total; a completed batch is not a completed repair.
The September 7 verification report is outputs/history_repair_status_20260907.json.
