#!/usr/bin/env python3
"""Deterministically normalize legacy 0-10 Opportunity scores to 0-100."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.intel_opportunity_engine_v12 import normalize_score_scale
from signalboard.db import init_db


SCORE_COLUMNS = (
    "opportunity_score", "thesis_quality_score", "evidence_quality_score",
    "earnings_impact_score", "mispricing_score", "catalyst_score", "risk_reward_score",
)
SCORE_KEYS = (
    "opportunity", "thesis_quality", "evidence_quality", "earnings_impact",
    "mispricing", "catalyst", "risk_reward",
)


def _walk(value: Any) -> int:
    changed = 0
    if isinstance(value, dict):
        scores = value.get("scores")
        if isinstance(scores, dict) and normalize_score_scale(scores):
            changed += 1
        for child in value.values():
            changed += _walk(child)
    elif isinstance(value, list):
        for child in value:
            changed += _walk(child)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db")
    parser.add_argument("--output-dir", default="outputs/opportunity_engine_v12")
    args = parser.parse_args()
    init_db(args.db)
    con = sqlite3.connect(args.db, timeout=120)
    changed = {"chains": 0, "opportunities": 0, "versions": 0, "files": 0, "score_objects": 0}

    for candidate_id, raw in con.execute("SELECT candidate_id,analysis_json FROM logic_chain_analyses").fetchall():
        data = json.loads(raw)
        if normalize_score_scale(data.get("scores") or {}):
            con.execute("UPDATE logic_chain_analyses SET analysis_json=? WHERE candidate_id=?",
                        (json.dumps(data, ensure_ascii=False, sort_keys=True), candidate_id))
            changed["chains"] += 1

    for opportunity_id, raw in con.execute(
        "SELECT opportunity_id,synthesis_json FROM investment_opportunities"
    ).fetchall():
        synthesis = json.loads(raw)
        scores = synthesis.get("scores") or {}
        if normalize_score_scale(scores):
            values = [scores[key] for key in SCORE_KEYS]
            assignments = ",".join(f"{column}=?" for column in SCORE_COLUMNS)
            con.execute(
                f"UPDATE investment_opportunities SET {assignments},synthesis_json=? WHERE opportunity_id=?",
                (*values, json.dumps(synthesis, ensure_ascii=False, sort_keys=True), opportunity_id),
            )
            changed["opportunities"] += 1

    for opportunity_id, version_number, raw in con.execute(
        "SELECT opportunity_id,version_number,snapshot_json FROM opportunity_versions"
    ).fetchall():
        snapshot = json.loads(raw)
        count = _walk(snapshot)
        if count:
            con.execute(
                "UPDATE opportunity_versions SET snapshot_json=? WHERE opportunity_id=? AND version_number=?",
                (json.dumps(snapshot, ensure_ascii=False, sort_keys=True), opportunity_id, version_number),
            )
            changed["versions"] += 1
            changed["score_objects"] += count
    con.commit()
    con.close()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for path in out.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        count = _walk(data)
        if count:
            if path.name == "top_opportunities.json" and isinstance(data, list):
                data.sort(key=lambda item: -float(item.get("synthesis", {}).get("scores", {}).get("opportunity", 0)))
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            changed["files"] += 1
            changed["score_objects"] += count

    report = out / "score_normalization_report.json"
    report.write_text(json.dumps(changed, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(changed, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
