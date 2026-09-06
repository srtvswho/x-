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
