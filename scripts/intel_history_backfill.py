#!/usr/bin/env python3
"""Plan/resume historical extraction for all eight authors, without a date cutoff.

Planning is read-only. --apply delegates a bounded batch to the existing guarded
extractor; it never changes AI permissions, budgets, model routes or prompts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "dashboard"))
from common import SRC2KOL
from intel_extract import PROMPT_VERSION


def plan_backfill(con, limit=400):
    if not 1 <= limit <= 500:
        raise ValueError("batch limit must be between 1 and 500")
    buckets = defaultdict(deque)
    counts = {}
    for source in SRC2KOL:
        raw_count, first, last = con.execute(
            "SELECT COUNT(*), MIN(published_at), MAX(published_at) FROM raw_posts WHERE source_id=?",
            (source,),
        ).fetchone()
        missing = con.execute("""
            SELECT r.post_id, r.published_at,
                   EXISTS(SELECT 1 FROM extractions_intel old WHERE old.post_id=r.post_id) AS had_old
            FROM raw_posts r WHERE r.source_id=? AND NOT EXISTS (
                SELECT 1 FROM extractions_intel e WHERE e.post_id=r.post_id AND e.prompt_version=?)
            ORDER BY had_old, julianday(r.published_at), r.post_id
        """, (source, PROMPT_VERSION)).fetchall()
        buckets[source].extend(p[0] for p in missing)
        counts[source] = {
            "raw_posts": raw_count, "raw_start": first, "raw_end": last,
            "pending_current_version": len(missing),
            "never_extracted": sum(not p[2] for p in missing),
            "raw_coverage": "unverified",  # Endpoints alone cannot prove continuity.
        }
    selected = []
    while len(selected) < limit and any(buckets.values()):
        for source in SRC2KOL:
            if buckets[source] and len(selected) < limit:
                selected.append(buckets[source].popleft())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION, "sources": counts,
        "pending_total": sum(c["pending_current_version"] for c in counts.values()),
        "selected_post_ids": selected, "batch_limit": limit,
        "history_complete": False, "scope": "all_stored_history",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db")
    parser.add_argument("--limit", type=int, default=400)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default="outputs/signalboard_history_rebuild_latest.json")
    args = parser.parse_args()
    with sqlite3.connect(f"file:{Path(args.db).resolve()}?mode=ro", uri=True) as con:
        before = plan_backfill(con, args.limit)
    ids = before["selected_post_ids"]
    if args.apply and ids:
        subprocess.run([
            sys.executable, str(ROOT / "scripts" / "intel_extract.py"),
            "--db", args.db, "--post-ids", ",".join(ids), "--max-targets", str(args.limit),
        ], check=True)
    with sqlite3.connect(f"file:{Path(args.db).resolve()}?mode=ro", uri=True) as con:
        report = plan_backfill(con, args.limit)
    report["applied"] = args.apply
    report["resolved_this_run"] = before["pending_total"] - report["pending_total"]
    report["attempted_post_ids"] = ids if args.apply else []
    output = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("post_ids")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
