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
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

sys.path.insert(0, "/workspace")
from signalboard.ai.router import call_json, record_usage, resolve_route
from signalboard.db import init_db
from signalboard.extract.prompts_intel import (
    PROMPT_VERSION,
    build_user_prompt,
    get_system_prompt,
)

DB_PATH = "/workspace/data/signalboard_full.db"
DEEPSEEK_MODEL = resolve_route("bulk_post_processing").model
MAX_WORKERS = 5  # 受 deepseek RPM 限制
MAX_RETRIES = 2

# 历史回填的低成本预筛。显式 cashtag 始终算标的线索；未带 ``$`` 的文本
# 只匹配 Dashboard 已知的股票代码，避免把一整年的普通产业讨论都送给模型。
KNOWN_TICKER_CLUES = {
    "AAOI", "AEHR", "AEVA", "AMD", "AMZN", "AOSL", "ASTS", "AVGO",
    "AXTI", "COHR", "DRAM", "GFS", "GOOGL", "INTC", "IQE", "JBL",
    "LITE", "META", "MRVL", "MSFT", "MU", "NBIS", "NOK", "NVDA",
    "NVTS", "POET", "POWI", "RKLB", "SIVE", "SNDK", "SOI", "TSEM",
    "TSM", "VPG", "WOLF", "XFAB",
}
CASHTAG_RE = re.compile(r"(?<![A-Za-z0-9])\$[A-Za-z][A-Za-z0-9.\-]{0,9}\b")
KNOWN_TICKER_RE = re.compile(
    r"(?<![A-Za-z0-9$])(?:"
    + "|".join(sorted(map(re.escape, KNOWN_TICKER_CLUES), key=len, reverse=True))
    + r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)

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

EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ticker": {"anyOf": [{"type": "null"}, {"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
        "company": {"anyOf": [{"type": "null"}, {"type": "string"}, {"type": "array", "items": {"type": "string"}}]},
        "direction": {"type": "string"},
        "short_skeptical": {"type": "integer"},
        "bottleneck": {"anyOf": [{"type": "null"}, {"type": "string"}]},
        "attribution": {"type": "string"},
        "rebuts_narrative": {"anyOf": [{"type": "null"}, {"type": "string"}]},
        "summary_100": {"type": "string"},
        "is_retrospective": {"type": "integer"},
        "is_disclosure": {"type": "integer"},
        "is_self_reported_returns": {"type": "integer"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "claim_text": {"type": "string"},
                    "claim_type": {"type": "string", "enum": [
                        "FACT", "FORECAST", "OPINION", "INFERENCE", "VALUATION",
                        "CATALYST", "RISK", "POSITION", "QUESTION",
                    ]},
                    "claim_author": {"type": "string"},
                    "companies": {"type": "array", "items": {"type": "string"}},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "time_horizon": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": [
                    "claim_text", "claim_type", "claim_author", "companies",
                    "themes", "time_horizon", "confidence",
                ],
            },
        },
        "themes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "ticker", "company", "direction", "short_skeptical", "bottleneck",
        "attribution", "rebuts_narrative", "summary_100", "is_retrospective",
        "is_disclosure", "is_self_reported_returns",
        "claims", "themes",
    ],
}


def _theme_id(name: str) -> str:
    return "theme_" + hashlib.sha256(name.strip().casefold().encode()).hexdigest()[:20]


def persist_claims_and_themes(
    con: sqlite3.Connection,
    post_id: str,
    source_id: str,
    extraction: dict,
) -> None:
    """Persist atomic claims/themes emitted by the same bulk call."""
    published = con.execute("SELECT published_at FROM raw_posts WHERE post_id=?", (post_id,)).fetchone()
    point_in_time = published[0] if published else None
    top_themes = [str(x).strip() for x in extraction.get("themes") or [] if str(x).strip()]
    attribution = str(extraction.get("attribution") or "NA").upper()
    for index, claim in enumerate(extraction.get("claims") or []):
        if not isinstance(claim, dict):
            continue
        claim_text = str(claim.get("claim_text") or "").strip()
        claim_type = str(claim.get("claim_type") or "OPINION").upper()
        if not claim_text or claim_type not in {
            "FACT", "FORECAST", "OPINION", "INFERENCE", "VALUATION",
            "CATALYST", "RISK", "POSITION", "QUESTION",
        }:
            continue
        claim_themes = [str(x).strip() for x in claim.get("themes") or [] if str(x).strip()]
        all_themes = list(dict.fromkeys(claim_themes or top_themes))
        stated_author = str(claim.get("claim_author") or "").strip()
        author = source_id if attribution in {"ORIGINAL", "ENDORSED", "DISAGREED"} else stated_author
        content_hash = hashlib.sha256(claim_text.casefold().encode()).hexdigest()
        claim_id = "claim_" + hashlib.sha256(f"{post_id}\n{index}\n{content_hash}".encode()).hexdigest()[:24]
        confidence = min(1.0, max(0.0, float(claim.get("confidence") or 0.5)))
        con.execute(
            """
            INSERT OR REPLACE INTO claims (
                claim_id, claim_text, claim_type, author_id, companies_json,
                themes_json, time_horizon, source_post_id, evidence_ids_json,
                confidence, verification_status, point_in_time, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', ?, 'UNVERIFIED', ?, ?)
            """,
            (
                claim_id, claim_text, claim_type, author or None,
                json.dumps(claim.get("companies") or [], ensure_ascii=False),
                json.dumps(all_themes, ensure_ascii=False),
                str(claim.get("time_horizon") or "").strip() or None,
                post_id, confidence, point_in_time, content_hash,
            ),
        )
        for theme_name in all_themes:
            tid = _theme_id(theme_name)
            con.execute(
                "INSERT OR IGNORE INTO themes (theme_id, name) VALUES (?, ?)",
                (tid, theme_name),
            )
            con.execute(
                "INSERT OR REPLACE INTO claim_themes (claim_id, theme_id, confidence) VALUES (?, ?, ?)",
                (claim_id, tid, confidence),
            )

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


def has_ticker_clue(raw_text: str | None) -> bool:
    """是否含显式 cashtag 或 Dashboard 已知 ticker。"""
    text = raw_text or ""
    return bool(CASHTAG_RE.search(text) or KNOWN_TICKER_RE.search(text))


def get_target_posts(
    con: sqlite3.Connection,
    since_iso: str,
    *,
    until_iso: str | None = None,
    source_ids: list[str] | None = None,
    ticker_clues_only: bool = False,
    claims_missing: bool = False,
) -> list[dict]:
    """按窗口取未抽取推文；可按人物和标的线索限制历史回填范围。"""
    missing_clause = (
        "(ei.post_id IS NULL OR NOT EXISTS (SELECT 1 FROM claims c WHERE c.source_post_id=rp.post_id))"
        if claims_missing else "ei.post_id IS NULL"
    )
    where = ["rp.published_at >= ?", missing_clause]
    params: list[object] = [PROMPT_VERSION, since_iso]
    if until_iso:
        where.append("rp.published_at < ?")
        params.append(until_iso)
    if source_ids:
        placeholders = ",".join("?" for _ in source_ids)
        where.append(f"rp.source_id IN ({placeholders})")
        params.extend(source_ids)
    rows = con.execute(f"""
        SELECT rp.post_id, rp.source_id, rp.raw_text, rp.published_at
        FROM raw_posts rp
        LEFT JOIN extractions_intel ei
          ON rp.post_id = ei.post_id AND ei.prompt_version = ?
        WHERE {' AND '.join(where)}
          AND rp.source_id NOT LIKE 'ctx_%'
        ORDER BY rp.published_at ASC
    """, params).fetchall()
    posts = [
        {"post_id": r[0], "source_id": r[1], "raw_text": r[2], "published_at": r[3]}
        for r in rows
    ]
    if ticker_clues_only:
        posts = [post for post in posts if has_ticker_clue(post["raw_text"])]
    return posts


def call_deepseek(post_id: str, raw_text: str) -> dict:
    """通过统一路由执行批量 Post 抽取。"""
    sys_p = get_system_prompt()
    usr_p = build_user_prompt(post_id, raw_text)
    try:
        result = call_json(
            "bulk_post_processing", sys_p, usr_p, EXTRACTION_SCHEMA,
            schema_name="signalboard_post_extraction", max_output_tokens=1500,
            timeout=30, max_retries=MAX_RETRIES,
        )
        return {
            "ok": True, "extraction": result.data, "raw": result.text,
            "usage": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "estimated_cost_usd": result.estimated_cost_usd,
            },
            "ai_result": result,
        }
    except Exception as e:
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
            INSERT INTO extractions_intel
            (post_id, source_id, extracted_at, model_version, prompt_version,
             raw_response, ticker, company, direction, short_skeptical,
             bottleneck, attribution, rebuts_narrative, summary_100,
            is_retrospective, is_disclosure, is_self_reported_returns)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id, prompt_version) DO UPDATE SET
                source_id=excluded.source_id,
                extracted_at=excluded.extracted_at,
                model_version=excluded.model_version,
                raw_response=excluded.raw_response,
                ticker=excluded.ticker,
                company=excluded.company,
                direction=excluded.direction,
                short_skeptical=excluded.short_skeptical,
                bottleneck=excluded.bottleneck,
                attribution=excluded.attribution,
                rebuts_narrative=excluded.rebuts_narrative,
                summary_100=excluded.summary_100,
                is_retrospective=excluded.is_retrospective,
                is_disclosure=excluded.is_disclosure,
                is_self_reported_returns=excluded.is_self_reported_returns
        """, (
            post_id, source_id, now_iso, DEEPSEEK_MODEL, PROMPT_VERSION,
            raw_response, ticker, company, direction, short_skeptical,
            extraction.get("bottleneck"), extraction.get("attribution"),
            extraction.get("rebuts_narrative"), extraction.get("summary_100"),
            is_retrospective, is_disclosure, is_self_reported_returns,
        ))
        persist_claims_and_themes(con, post_id, source_id, extraction)
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
        "ai_result": result["ai_result"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="ISO date (e.g. 2026-06-19)")
    ap.add_argument("--until", help="ISO 结束日期（不含），用于限定历史回填窗口")
    ap.add_argument("--sources", help="逗号分隔 source_id，只抽指定人物")
    ap.add_argument("--ticker-clues-only", action="store_true",
                    help="只抽含 cashtag 或已知 ticker 的推文（历史低成本回填）")
    ap.add_argument("--claims-missing", action="store_true",
                    help="包含已有方向抽取但尚无 Claim 的帖子，并原位升级该抽取")
    ap.add_argument("--max-targets", type=int, default=0,
                    help="候选数超过该值就中止，防止意外产生过量 API 调用")
    ap.add_argument("--dry-run", action="store_true", help="不落库, 只抽 + 打印")
    ap.add_argument("--limit", type=int, default=0, help="最多抽几条 (0=全抽)")
    args = ap.parse_args()

    since_iso = args.since if "T" in args.since else f"{args.since}T00:00:00+00:00"
    until_iso = None
    if args.until:
        until_iso = args.until if "T" in args.until else f"{args.until}T00:00:00+00:00"
    source_ids = [s.strip() for s in (args.sources or "").split(",") if s.strip()]

    init_db(DB_PATH)
    con = sqlite3.connect(DB_PATH, timeout=120)
    init_extractions_table(con)

    targets = get_target_posts(
        con,
        since_iso,
        until_iso=until_iso,
        source_ids=source_ids or None,
        ticker_clues_only=args.ticker_clues_only,
        claims_missing=args.claims_missing,
    )
    if args.max_targets > 0 and len(targets) > args.max_targets:
        raise SystemExit(
            f"候选 {len(targets)} 条，超过安全上限 {args.max_targets}；已中止，未调用 API"
        )
    if args.limit > 0:
        targets = targets[:args.limit]
    print(f"=== 大V情报模块2: 增量抽取 ({PROMPT_VERSION}, dry_run={args.dry_run}) ===")
    print(f"  since: {since_iso}")
    print(f"  until: {until_iso or '-'}")
    print(f"  sources: {','.join(source_ids) if source_ids else 'ALL'}")
    print(f"  ticker_clues_only: {args.ticker_clues_only}")
    print(f"  claims_missing: {args.claims_missing}")
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
                record_usage(
                    con, r["ai_result"], workload="bulk_post_processing",
                    object_type="post", object_id=r["post_id"],
                )
                con.commit()
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
