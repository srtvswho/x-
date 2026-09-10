# Frozen historical replay, 2026-09-10

The unchanged v1 policy selected zero priority or field-watch signals from 467 first-long candidates across four quarterly windows. The rolling-at-post sensitivity also selected zero. `report.html` explains the result and six rejected diagnostic candidates; these examples are not strategy performance.

Run from the repository root, using Python's standard library only:

```sh
python tests/test_focus_signals.py
python scripts/backtest_focus_signals.py
python scripts/build_focus_backtest_report.py
```

No database, network, scraping or model calls are needed. Inputs are the adjacent frozen `policy_evidence.json.gz`, `replay_context.json.gz` and `../kol_reaudit_20260910/scored_events.json.gz`. The latter contains original post texts, direction and identity adjudications, entry prices, mature forward returns and benchmark comparisons. Replay context preserves per-source raw-post timestamps and the observed SPY session calendar. SHA-256 digests are in `manifest.json`.

`backtest.json.gz` preserves every decision, rejection reason, training sample and future outcome, plus unfiltered and same-field controls. Future outcomes are attached after selection. The signal engine enforces completed training outcomes before each cutoff and excludes the new security from its own training. The local policy baseline was commit `20c1849`; the published version adds an optional frozen-profile date without changing thresholds. The current live evidence file is independent of this frozen snapshot.

The current corpus, author/domain selection and semantic audit were assembled retrospectively. Thus this is a public-post counterfactual replay, not actual-system availability or a blind out-of-sample test. Incomplete histories and missing prices remain limitations. We did not change thresholds after viewing outcomes. Price returns exclude dividends, costs and portfolio construction; correlated observations are not independent trades.
