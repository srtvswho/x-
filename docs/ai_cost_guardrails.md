# SignalBoard AI Cost Guardrails

Paid AI is fail-closed. `AI_ENABLED` defaults to `false`; having an API key in the
environment is not permission to make a request.

## Required gates

| Control | Default | Effect |
| --- | ---: | --- |
| `AI_ENABLED` | `false` | Every routed paid request is blocked before credential access or network I/O. |
| `AI_DRY_RUN` | `false` in code; `true` in manual paid workflows | Emits model, stage, calls, token estimates and cost; sends zero API requests. |
| `AI_MAX_COST_PER_RUN_USD` | `0.50` | Blocks a request when its conservative estimate would exceed the remaining run budget. |
| `AI_MAX_DAILY_COST_USD` | `1.00` | Stops requests once risk-adjusted daily usage reaches the limit. |
| `AI_MAX_CALLS_PER_RUN` | `20` | Hard call-count ceiling independent of cost estimates. |
| Stage budgets | conservative | `MEDIA`, `THEME`, `CLAIM`, `THESIS`, `ANALYST`, and `GOLDEN` are capped separately. |
| `ALLOW_EXPENSIVE_AI_JOB` | `false` | Required for full Golden, historical media/claim backfills and full thesis regeneration. |
| `FORCE_REANALYZE` | `false` | A successful same-input/model/prompt result is reused instead of called again. |

The `ai_usage_ledger` row is committed as `PENDING` before the HTTP request. Success
or failure updates that row. A killed workflow therefore leaves a visible Pending /
Unknown risk estimate rather than an unexplained bill.

## Safe re-enable procedure

1. Leave repository secrets unchanged and keep scheduled Daily runs at their defaults.
2. Manually dispatch **Signalboard Daily Update** with `ai_enabled=true` and
   `ai_dry_run=true`. Confirm call count, token estimates and total estimated cost.
3. Set conservative run, daily, stage and call limits in the workflow/environment.
4. Dispatch one incremental run with `ai_enabled=true` and `ai_dry_run=false`.
5. Check the Dashboard AI Cost panel and `ai_usage_ledger` before enabling another run.
6. For Golden or backfill work, also set `allow_expensive_ai_job=true`; never add that
   flag to a scheduled workflow.

Do not “disable” AI by deleting a secret. The application gate is the control; secrets
may exist while `AI_ENABLED=false` and still cannot be used by the routed pipeline.
