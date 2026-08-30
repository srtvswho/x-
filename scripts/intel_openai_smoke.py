#!/usr/bin/env python3
"""One-shot OpenAI Responses API/model-access check for deployment."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.ai.router import call_json, record_usage
from signalboard.db import init_db

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db")
    args = parser.parse_args()
    init_db(args.db)
    result = call_json(
        "media_understanding",
        "Return the requested JSON only.",
        "Set ok to true.",
        SCHEMA,
        schema_name="signalboard_openai_smoke",
        max_output_tokens=256,
        timeout=60,
        max_retries=0,
    )
    if result.data != {"ok": True}:
        raise SystemExit(f"unexpected smoke result: {result.data!r}")
    con = sqlite3.connect(args.db)
    record_usage(con, result, workload="media_understanding", object_type="deployment", object_id="openai_smoke")
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "provider": result.provider, "model": result.model, "cost_usd": result.estimated_cost_usd}))


if __name__ == "__main__":
    main()
