# SignalBoard Research Thesis Engine v1.1

This release adds an auditable research-quality layer without replacing the existing Post, Claim, Theme, or Thesis tables.

## Quality gates

1. Historical Post graphs can be replayed by exact post ID, including recovered context posts.
2. Media is downloaded, SHA-256 hashed, deduplicated, prioritized, and analyzed in bounded batches. Failures become `FAILED_RETRYABLE` and never block daily ingestion.
3. Theme embeddings only generate candidates. Terra must return a high-confidence `MERGE_ALIAS` decision before links are canonicalized; related drivers and products remain distinct.
4. Social reposts are grouped under an `Underlying Source ID`. Social mention count and independent evidence count are reported separately.
5. High-importance Claims use Responses web search and the following evidence hierarchy: primary filings/data, major secondary reporting, industry media. Social posts remain author claims.
6. Author × Theme Thesis updates consume the current Thesis plus only new Claims, new media, and new verification results.
7. Terra produces the independent Analyst record and cross-author synthesis. Sol is never scheduled; it is only reachable through explicit `--deep-analysis` invocation.
8. The home page only shows Analyst-reviewed Thesis Changes with change score at least 10. Allowed actionability labels are `NOT_ACTIONABLE`, `WATCH`, `RESEARCH`, `BUY_CANDIDATE`, `HEDGE_CANDIDATE`, and `AVOID`.
9. Human-bounded Research Cases synthesize evidence across multiple Author × Theme records. They answer explicit audit questions, retain unknowns, and are refreshed only when their evidence digest changes.

## Golden validation

`tests/golden_cases.json` defines explicit facts, logic steps, corrections, risks, beneficiaries, losers, unknowns, reference edges, and required media for:

- YMTC → NAND → China WFE
- ABF → CoPoS / CoWoP → PCB

`scripts/intel_golden_tests.py` checks the graph and structured outputs by category. Raw social text cannot satisfy a correction, Analyst assessment, or verified-evidence check by itself. Source deduplication passes only when at least two social/visual mentions resolve to the same Underlying Source; newly found verification sources remain separate independent evidence.

## Bounded media backfill

Run the `Signalboard Media Backfill` workflow after Golden validation passes. `batch_size` defaults to 30. Each run checkpoints the compressed database to `master`; repeated runs only select media without a current analysis.
