#!/usr/bin/env bash
set -Eeuo pipefail
# All data writers share the repository concurrency group. A non-fast-forward fails closed.
gzip -n -c data/signalboard_full.db > data/signalboard.db.gz.tmp
mv data/signalboard.db.gz.tmp data/signalboard.db.gz
git add data/signalboard.db.gz scripts/dashboard/summaries.json
git add -f outputs/daily-ai-windows.json
if ! git diff --cached --quiet; then
  git commit -m 'Checkpoint incremental DeepSeek interpretations [skip daily] [skip ui] [CF-Pages-Skip]'
  git push origin HEAD:master
fi
