# Project continuity

At the start of work, read `docs/WORKFLOW.md` and `docs/WORKFLOW_STATE.json`, then run `python scripts/workflow_status.py`. Reconcile the current Git revision and live state before choosing the next action. A dated handoff is historical evidence, not proof that today's data is fresh.

Continue the user's authorized objective from the first incomplete checkpoint. Use the task's existing acceptance criteria; preserve explicit user constraints. After a meaningful change, record the source revision, actual checks, blockers and next action in WORKFLOW_STATE.json and commit the handoff with the work. Never store credentials there.

Do not equate a successful build, push, HTTP 200 or a previous conversation's claim with a verified production result. Use the live checks documented below. Report missing access or incomplete verification accurately.

Also follow `INSTRUCTIONS.txt`. Preserve raw posts and prior interpretations. UI-only work uses the existing saved database and prices, with zero provider/model calls; include `[skip daily]` in UI-only source commits. Never use `git reset --hard` to resolve concurrent data changes.
