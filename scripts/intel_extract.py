"""大V情报 — 模块 2: 增量结构化抽取 + 入库

v2.0.0-intel 简化 prompt (8 字段):
- ticker / company / direction / short_skeptical / bottleneck
- attribution / rebuts_narrative / summary_100

落表 extractions_intel (FK -> raw_posts.post_id, 幂等).

使用:
  python intel_extract.py --since 2026-06-19  # 抽最近 7 天
  python intel_extract.py --since 2026-05-27  # 抽最近 30 天
  python intel_extract.py --dry-run --since 2026-06-19  # 不入库, 只打印

设计:
- 5 worker ThreadPoolExecutor (受 deepseek RPM 限制, 20-30 worker 会触发限流)
- 每条独立 try/except + 2 次重试
- 跳过已抽取 (幂等: UNIQUE(post_id, prompt_version))
- 强制 FK 验证 (raw_posts.post_id 必须存在)
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

sys.path.insert(0, "/workspace")
from signalboard.extract.prompts_intel import (
    PROMPT_VERSION,
    build_user_prompt,
    get_system_prompt,
)

DB_PATH = "/workspace/data/signalboard_full.db"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"  # 跨项目硬规则
MAX_WORKERS = 5  # 受 deepseek RPM 限制
MAX_RETRIES = 2

# DDL
DDL = """
CREATE TABLE IF NOT EXISTS extractions_intel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    raw_response TEXT NOT NULL,
    ticker TEXT,
    company TEXT,
    direction TEXT NOT NULL,
    short_skeptical INTEGER NOT NULL DEFAULT 1,
    bottleneck TEXT,
    attribution TEXT,
    rebuts_narrative TEXT,
    summary_100 TEXT,
    is_retrospective INTEGER NOT NULL DEFAULT 0,
    is_disclosure INTEGER NOT NULL DEFAULT 0,
    is_self_reported_returns INTEGER NOT NULL DEFAULT 0,
    UNIQUE(post_id, prompt_version)
);
CREATE INDEX IF NOT EXISTS idx_extractions_intel_post ON extractions_intel(post_id);
CREATE INDEX IF NOT EXISTS idx_extractions_intel_source ON extractions_intel(source_id);
CREATE INDEX IF NOT EXISTS idx_extractions_intel_direction ON extractions_intel(direction);
CREATE INDEX IF NOT EXISTS idx_extractions_intel_extracted_at ON extractions_intel(extracted_at);
CREATE INDEX IF NOT EXISTS idx_extractions_intel_retrospective ON extractions_intel(is_retrospective);
CREATE INDEX IF NOT EXISTS idx_extractions_intel_disclosure ON extractions_intel(is_disclosure);
"""

# Migration: 加 3 个 R12 flag 列 (针对已存在的旧表)
MIGRATION = """
ALTER TABLE extractions_intel ADD COLUMN is_retrospective INTEGER NOT NULL DEFAULT 0;
ALTER TABLE extractions_intel ADD COLUMN is_disclosure INTEGER NOT NULL DEFAULT 0;
ALTER TABLE extractions_intel ADD COLUMN is_self_reported_returns INTEGER NOT NULL DEFAULT 0;
"""


def init_extractions_table(con: sqlite3.Connection) -> None:
    """建表 (幂等)."""
    # 1. 如表已存在但缺新列, 先 ALTER TABLE
    cols = {row[1] for row in con.execute("PRAGMA table_info(extractions_intel)").fetchall()}
    table_exists = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='extractions_intel'"
    ).fetchone() is not None
    if table_exists:
        for col in ["is_retrospective", "is_disclosure", "is_self_reported_returns"]:
            if col not in cols:
                con.execute(f"ALTER TABLE extractions_intel ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0")
    else:
        # 表不存在, CREATE TABLE (含新列)
        con.executescript(DDL)
    # 2. CREATE INDEX (幂等)
    con.executescript("""
    CREATE INDEX IF NOT EXISTS idx_extractions_intel_post ON extractions_intel(post_id);
    CREATE INDEX IF NOT EXISTS idx_extractions_intel_source ON extractions_intel(source_id);
    CREATE INDEX IF NOT EXISTS idx_extractions_intel_direction ON extractions_intel(direction);
    CREATE INDEX IF NOT EXISTS idx_extractions_intel_extracted_at ON extractions_intel(extracted_at);
    CREATE INDEX IF NOT EXISTS idx_extractions_intel_retrospective ON extractions_intel(is_retrospective);
    CREATE INDEX IF NOT EXISTS idx_extractions_intel_disclosure ON extractions_intel(is_disclosure);
    """)
    con.commit()


def get_target_posts(con: sqlite3.Connection, since_iso: str) -> list[dict]:
    """拿 since 之后的所有推文, 排除已抽取的 (post_id, prompt_version)."""
    rows = con.execute("""
        SELECT rp.post_id, rp.source_id, rp.raw_text, rp.published_at
        FROM raw_posts rp
        LEFT JOIN extractions_intel ei
          ON rp.post_id = ei.post_id AND ei.prompt_version = ?
        WHERE rp.published_at >= ?
          AND ei.post_id IS NULL
        ORDER BY rp.published_at DESC
    """, (PROMPT_VERSION, since_iso)).fetchall()
    return [
        {"post_id": r[0], "source_id": r[1], "raw_text": r[2], "published_at": r[3]}
        for r in rows
    ]


def call_deepseek(post_id: str, raw_text: str) -> dict:
    """调 LLM 抽 (单条). 含 retry."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    sys_p = get_system_prompt()
    usr_p = build_user_prompt(post_id, raw_text)
    data = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": usr_p},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},  # ★ 跨项目硬规则: 关闭思考模式
    }).encode()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(DEEPSEEK_URL, data=data, headers=headers, timeout=30)
            r.raise_for_status()
            j = r.json()
            content = j["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {"ok": True, "extraction": parsed, "raw": content, "usage": j.get("usage", {})}
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(1 + attempt * 2)
                continue
            return {"ok": False, "error": str(e)}


def persist_extraction(con: sqlite3.Connection, post_id: str, source_id: str,
                       raw_response: str, extraction: dict) -> bool:
    """落库 (幂等: UNIQUE 冲突静默跳过)."""
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    # ticker / company 可能是 string 或 array, 统一存 JSON string
    ticker = extraction.get("ticker")
    if isinstance(ticker, list):
        ticker = json.dumps(ticker, ensure_ascii=False)
    company = extraction.get("company")
    if isinstance(company, list):
        company = json.dumps(company, ensure_ascii=False)
    direction = extraction.get("direction", "neutral")
    short_skeptical = extraction.get("short_skeptical", 1)
    is_retrospective = extraction.get("is_retrospective", 0)
    is_disclosure = extraction.get("is_disclosure", 0)
    is_self_reported_returns = extraction.get("is_self_reported_returns", 0)
    try:
        con.execute("""
            INSERT OR IGNORE INTO extractions_intel
            (post_id, source_id, extracted_at, model_version, prompt_version,
             raw_response, ticker, company, direction, short_skeptical,
             bottleneck, attribution, rebuts_narrative, summary_100,
             is_retrospective, is_disclosure, is_self_reported_returns)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id, source_id, now_iso, DEEPSEEK_MODEL, PROMPT_VERSION,
            raw_response, ticker, company, direction, short_skeptical,
            extraction.get("bottleneck"), extraction.get("attribution"),
            extraction.get("rebuts_narrative"), extraction.get("summary_100"),
            is_retrospective, is_disclosure, is_self_reported_returns,
        ))
        con.commit()
        return True
    except Exception as e:
        print(f"  ❌ persist fail {post_id}: {e}")
        return False


def extract_one(post: dict) -> dict:
    """抽一条 (并发: worker 只抽, 不入库 — SQLite 不允许跨线程)."""
    pid = post["post_id"]
    result = call_deepseek(pid, post["raw_text"])
    if not result["ok"]:
        return {"post_id": pid, "source_id": post["source_id"], "ok": False, "error": result["error"]}
    return {
        "post_id": pid,
        "source_id": post["source_id"],
        "ok": True,
        "extraction": result["extraction"],
        "raw_response": result["raw"],
        "usage": result["usage"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="ISO date (e.g. 2026-06-19)")
    ap.add_argument("--dry-run", action="store_true", help="不落库, 只抽 + 打印")
    ap.add_argument("--limit", type=int, default=0, help="最多抽几条 (0=全抽)")
    args = ap.parse_args()

    since_iso = args.since if "T" in args.since else f"{args.since}T00:00:00+00:00"

    con = sqlite3.connect(DB_PATH, timeout=120)
    init_extractions_table(con)

    targets = get_target_posts(con, since_iso)
    if args.limit > 0:
        targets = targets[:args.limit]
    print(f"=== 大V情报模块2: 增量抽取 ({PROMPT_VERSION}, dry_run={args.dry_run}) ===")
    print(f"  since: {since_iso}")
    print(f"  targets: {len(targets)} 条 (排除已抽取)")
    print(f"  workers: {MAX_WORKERS}")
    print()

    if not targets:
        print("  没有新推文需要抽取.")
        return

    # 4 大V 分布
    by_source = {}
    for t in targets:
        by_source[t["source_id"]] = by_source.get(t["source_id"], 0) + 1
    print("  by source_id:")
    for sid, n in by_source.items():
        print(f"    {sid}: {n}")

    # 并发抽 (5 worker, 只抽不入库 — SQLite 不允许跨线程)
    results = []
    fail_count = 0
    short_count = 0
    short_skeptical_count = 0
    rebuts_count = 0
    direction_count = {"long": 0, "short": 0, "neutral": 0}
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(extract_one, t): t for t in targets}
        for i, future in enumerate(as_completed(futures), 1):
            r = future.result()
            results.append(r)
            if not r["ok"]:
                fail_count += 1
                print(f"  [{i}/{len(targets)}] ❌ {r['post_id'][:20]}... ERR: {r.get('error', '?')[:80]}")
            else:
                ext = r["extraction"]
                d = ext.get("direction", "?")
                direction_count[d] = direction_count.get(d, 0) + 1
                if d == "short":
                    short_count += 1
                    if ext.get("short_skeptical") == 1:
                        short_skeptical_count += 1
                if ext.get("rebuts_narrative"):
                    rebuts_count += 1
                # 每条打印 (前 5 + 失败)
                if i <= 5 or not r["ok"]:
                    print(f"  [{i}/{len(targets)}] {r['source_id']:25s} {d:8s} ticker={ext.get('ticker')!r} attr={ext.get('attribution')!r} rebut={'Y' if ext.get('rebuts_narrative') else 'N'}")

    # 串行入库 (main thread, SQLite 安全)
    persist_count = 0
    if not args.dry_run:
        print()
        print("=== 串行入库 (main thread) ===")
        for r in results:
            if not r["ok"]:
                continue
            if persist_extraction(con, r["post_id"], r["source_id"], r["raw_response"], r["extraction"]):
                persist_count += 1
        print(f"  落库: {persist_count}/{len(results) - fail_count}")

    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"✅ 完成: {len(targets)} 条, 成功 {len(targets)-fail_count}, 失败 {fail_count}")
    print(f"  耗时: {elapsed:.1f}s (avg {elapsed/len(targets):.2f}s/条)")
    print()
    print("  direction 分布:")
    for d, c in direction_count.items():
        print(f"    {d}: {c}")
    print()
    print(f"  short 抽取: {short_count}")
    print(f"  short_skeptical=1 (怀疑误抽): {short_skeptical_count}")
    print(f"  rebuts_narrative 抓到: {rebuts_count}")
    print()
    if args.dry_run:
        print("  ⚠️  DRY RUN — 未落库")

    # 入库验证
    if not args.dry_run:
        print()
        print("=== 入库后验证 ===")
        n_total = con.execute("SELECT COUNT(*) FROM extractions_intel").fetchone()[0]
        n_dup = con.execute("""
            SELECT COUNT(*) FROM (
                SELECT post_id, COUNT(*) c FROM extractions_intel
                GROUP BY post_id, prompt_version HAVING c > 1
            )
        """).fetchone()[0]
        n_no_fk = con.execute("""
            SELECT COUNT(*) FROM extractions_intel ei
            WHERE NOT EXISTS (SELECT 1 FROM raw_posts rp WHERE rp.post_id = ei.post_id)
        """).fetchone()[0]
        n_fields_null = con.execute("""
            SELECT COUNT(*) FROM extractions_intel
            WHERE summary_100 IS NULL OR summary_100 = ''
        """).fetchone()[0]
        print(f"  extractions_intel 总行数: {n_total}")
        print(f"  重复 (post_id, prompt_version): {n_dup} (应为 0)")
        print(f"  FK 孤儿 (raw_posts 无对应 post_id): {n_no_fk} (应为 0)")
        print(f"  summary_100 空: {n_fields_null} (应为 0)")
        # 本次新入库
        n_this_run = con.execute("""
            SELECT COUNT(*) FROM extractions_intel
            WHERE extracted_at >= ?
        """, (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z"),)).fetchone()[0]
        print(f"  本次 (今天 extracted_at): {n_this_run}")

    con.close()


if __name__ == "__main__":
    main()
