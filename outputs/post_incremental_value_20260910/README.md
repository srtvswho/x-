# Post incremental value replay

Start with report.md or report.html. This is a diagnostic policy revision, not a live policy or blind backtest.

Replay from the repository root (Python standard library; no paid calls):

```sh
python scripts/backtest_post_incremental_value.py run
python scripts/build_post_incremental_report.py
```

Do not rerun `freeze`: protocol.json is already frozen. Inputs are the existing scored_events.json.gz, original v1 backtest, and adjacent peer_prices.json.gz. All current candidate future outcomes are attached only after decisions_before_outcomes.json.gz is persisted.

`validate_post_incremental_value.py` additionally rechecks OHLC caches in outputs/kol_reaudit_20260910/prices; those full original quote caches are in the prior audit attachment, not duplicated here. validation.json records that completed check. The smaller peer-price archive makes the report replay standalone within this repository.

CSV values are decimal returns, not percentages. Results are event studies, not portfolio P&L. No production recommendation thresholds are changed.
