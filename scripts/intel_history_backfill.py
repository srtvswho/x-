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
from signalboard.extract.prompts_intel import PROMPT_VERSION
from signalboard.history_reuse import load_reviews


def plan_backfill(con, limit=400):
    if not 1 <= limit <= 500:
        raise ValueError("batch limit must be between 1 and 500")
    reviews = load_reviews(con)
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
            ORDER BY julianday(r.published_at), r.post_id
        """, (source, PROMPT_VERSION)).fetchall()
        outdated_count = len(missing)
        reused = sum(p[0] in reviews for p in missing)
        missing = [p for p in missing if p[0] not in reviews]
        buckets[source].extend(p[0] for p in missing)
        counts[source] = {
            "raw_posts": raw_count, "raw_start": first, "raw_end": last,
            "pending_current_version": outdated_count,
            "pending_call_review": len(missing), "reused_interpretations": reused,
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
        "pending_total": sum(c["pending_call_review"] for c in counts.values()),
        "selected_post_ids": selected, "batch_limit": limit,
        "stored_history_call_review_complete": not any(buckets.values()) and not selected,
        "stored_history_extraction_complete": not any(c["pending_current_version"] for c in counts.values()),
        "history_complete": False, "scope": "all_stored_history",
    }


def read_plan(db, limit):
    with sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True) as con:
        return plan_backfill(con, limit)


def write_report(output, report):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(output)


def run_backfill(db, limit, apply, output, timeout=None):
    before = read_plan(db, limit)
    ids = before["selected_post_ids"]
    report = dict(before, applied=apply, resolved_this_run=0,
                  attempted_post_ids=ids if apply else [],
                  unresolved_attempted_post_ids=ids if apply else [],
                  batch_status="running" if apply and ids else "planned" if not apply else "no_work",
                  extractor_returncode=None)
    # Preserve the plan even if the runner is killed while the extractor is working.
    write_report(output, report)
    returncode = None
    error = None
    try:
        if apply and ids:
            returncode = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "intel_extract.py"),
                "--db", str(db), "--post-ids", ",".join(ids), "--max-targets", str(limit),
            ], check=False, **({"timeout": timeout} if timeout is not None else {})).returncode
    except (OSError, KeyboardInterrupt, subprocess.TimeoutExpired) as exc:
        error = type(exc).__name__
        returncode = 130 if isinstance(exc, KeyboardInterrupt) else 124 if isinstance(exc, subprocess.TimeoutExpired) else 1
    finally:
        after = read_plan(db, limit)
        unresolved = []
        if apply and ids:
            with sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True) as con:
                unresolved = [pid for pid in ids if not con.execute(
                    "SELECT 1 FROM extractions_intel WHERE post_id=? AND prompt_version=?",
                    (pid, PROMPT_VERSION),
                ).fetchone()]
        report = dict(after, applied=apply,
                      resolved_this_run=len(ids) - len(unresolved) if apply else 0,
                      attempted_post_ids=ids if apply else [],
                      unresolved_attempted_post_ids=unresolved,
                      extractor_returncode=returncode,
                      batch_status=("planned" if not apply else "no_work" if not ids else
                                    "incomplete" if unresolved or returncode else "completed"))
        if error:
            report["runner_error"] = error
        write_report(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db")
    parser.add_argument("--limit", type=int, default=400)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default="outputs/signalboard_history_rebuild_latest.json")
    args = parser.parse_args()
    report = run_backfill(args.db, args.limit, args.apply, args.report)
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("post_ids")}, ensure_ascii=False, indent=2))
    if report["batch_status"] == "incomplete":
        raise SystemExit("Historical extraction batch incomplete; checkpoint saved. See report and extractor errors.")


if __name__ == "__main__":
    main()
