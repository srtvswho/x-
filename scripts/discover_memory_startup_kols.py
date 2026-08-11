#!/usr/bin/env python3
"""Low-cost probe for authors who spotted the 2025 memory upcycle early.

This is discovery only. The event window must not be used in later blind scores.
The probe combines already-paid Signalboard rows with a small, capped Apify pull.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

DISCOVERY_FROM = date(2025, 4, 7)
DISCOVERY_TO = date(2025, 9, 11)
AS_OF = date(2026, 8, 11)
ACTOR_ID = "apidojo/tweet-scraper"
MODEL = "deepseek-v4-flash"
MAX_ITEMS_BROAD = 250
MAX_ITEMS_SEED = 180

SEED_HANDLES = (
    "amitisinvesting", "stocksavvyshay", "sam_badawi",
    "jukan05", "aleabitoreddit",
)

# Three broad queries plus five cheap author probes. This first run is deliberately
# capped around 1,650 rows; expansion is a separate decision after coverage audit.
BROAD_QUERIES = (
    "($SNDK OR SanDisk OR $WDC) (buy OR long OR add OR bullish OR cycle OR pricing OR supply)",
    "($MU OR Micron) (buy OR long OR add OR bullish OR cycle OR pricing OR supply)",
    "(DRAM OR NAND OR HBM OR memory cycle) (buy OR long OR bullish OR upcycle OR pricing OR supply)",
)

MEMORY_RE = re.compile(
    r"(?i)(?:\$?SNDK\b|\$?WDC\b|\$?MU\b|SanDisk|Western Digital|Micron|"
    r"DRAM|NAND|HBM|memory (?:cycle|pricing|supply)|存储|内存|闪迪|美光|海力士)"
)


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000 if value > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def text_of(item: dict[str, Any]) -> str:
    return str(item.get("text") or item.get("fullText") or item.get("tweetText") or
               item.get("raw_text") or "").strip()


def handle_of(item: dict[str, Any]) -> str | None:
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    value = (author.get("userName") or author.get("username") or
             item.get("userName") or item.get("username") or item.get("author_userName") or
             item.get("handle"))
    if not value:
        match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/", str(item.get("url") or
                                                                       item.get("raw_url") or ""), re.I)
        value = match.group(1) if match else None
    return str(value).lower().lstrip("@") if value else None


def normalize_post(item: dict[str, Any], source_query: str, source_kind: str) -> dict[str, Any] | None:
    text = text_of(item)
    handle = handle_of(item)
    dt = parse_datetime(item.get("createdAt") or item.get("created_at") or
                        item.get("published_at") or item.get("date") or item.get("timestamp"))
    if not text or not handle or not dt or not MEMORY_RE.search(text):
        return None
    if item.get("isRetweet") or text.startswith("RT @"):
        return None
    if not DISCOVERY_FROM <= dt.date() <= DISCOVERY_TO:
        return None
    post_id = str(item.get("id") or item.get("tweetId") or item.get("id_str") or
                  item.get("post_id") or "")
    if not post_id:
        post_id = hashlib.sha256(f"{handle}\n{dt.isoformat()}\n{text}".encode()).hexdigest()[:24]
    url = item.get("url") or item.get("tweetUrl") or item.get("raw_url") or \
        f"https://x.com/{handle}/status/{post_id}"
    return {
        "post_id": post_id,
        "handle": handle,
        "published_at": dt.astimezone(timezone.utc).isoformat(),
        "date": dt.date().isoformat(),
        "text": text,
        "url": url,
        "source_query": source_query,
        "source_kind": source_kind,
    }


def dataset_id(run: Any) -> str:
    value = getattr(run, "default_dataset_id", None)
    if not value and isinstance(run, dict):
        value = run.get("defaultDatasetId") or run.get("default_dataset_id")
    if not value:
        raise RuntimeError(f"Apify run has no dataset: {type(run).__name__}")
    return str(value)


def fetch_query(token: str, query: str, max_items: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from apify_client import ApifyClient

    advanced = f"{query} since:{DISCOVERY_FROM} until:{DISCOVERY_TO + timedelta(days=1)} -filter:retweets"
    client = ApifyClient(token)
    run = client.actor(ACTOR_ID).call(
        run_input={"searchTerms": [advanced], "maxItems": max_items, "sort": "Latest",
                   "includeSearchTerms": False, "onlyVerifiedUsers": False,
                   "onlyTwitterBlue": False},
        timeout=timedelta(minutes=15), memory_mbytes=2048,
    )
    items = list(client.dataset(dataset_id(run)).iterate_items())
    posts = [p for item in items if (p := normalize_post(item, query, "apify"))]
    dedup = {p["post_id"]: p for p in posts}
    ordered = sorted(dedup.values(), key=lambda p: p["published_at"])
    stats = {
        "query": query, "max_items": max_items, "returned": len(items),
        "in_window_memory_posts": len(ordered), "hit_cap": len(items) >= max_items,
        "earliest": ordered[0]["date"] if ordered else None,
        "latest": ordered[-1]["date"] if ordered else None,
    }
    return ordered, stats


def db_posts(db_gz: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not db_gz or not db_gz.exists():
        return [], {"available": False, "rows_scanned": 0, "matched": 0}
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        with gzip.open(db_gz, "rb") as src:
            while chunk := src.read(1024 * 1024):
                tmp.write(chunk)
        tmp.flush()
        con = sqlite3.connect(tmp.name)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT post_id, published_at, raw_text, raw_url, raw_json "
            "FROM raw_posts WHERE substr(published_at,1,10) BETWEEN ? AND ?",
            (DISCOVERY_FROM.isoformat(), DISCOVERY_TO.isoformat()),
        ).fetchall()
        output = []
        for row in rows:
            raw = {}
            try:
                raw = json.loads(row["raw_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                pass
            item = {**raw, "post_id": row["post_id"], "published_at": row["published_at"],
                    "raw_text": row["raw_text"], "raw_url": row["raw_url"]}
            post = normalize_post(item, "signalboard.db.gz", "existing_db")
            if post:
                output.append(post)
        con.close()
    dedup = {p["post_id"]: p for p in output}
    return list(dedup.values()), {"available": True, "rows_scanned": len(rows),
                                  "matched": len(dedup)}


PROMPT = """你是严格的投资证据审计员。目标是发现2025年存储周期启动期的事前多头作者。禁止用后来走势替作者补充观点。

分类：
- early_long_action：当时明确买入/加仓/做多/给出明确看多目标
- early_cycle_call：当时明确判断存储新一轮上行周期已开始或将开始
- early_mechanism_bull：当时以供给收紧、库存下降、DRAM/NAND/HBM涨价、盈利上修等机制明确看多
- trend_follow：上涨后追随趋势，但缺少周期或供需机制
- retrospective：事后复盘、自报战绩
- relay：搬运他人或新闻，没有作者自己的判断
- vague：模糊、中性或两面话
- bearish：看空、卖出、做空或反驳多头
- unrelated：不相关

逐条输出 index、category、tickers、original_judgment、actionable、mechanism_present、explicitness(0-3)、reasoning_quality(0-3)、reason（一句中文）。

帖子：{posts}

仅输出 JSON：{{"items":[...]}}。"""


def classify_batch(posts: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    import requests

    compact = [{"index": i, "date": p["date"], "handle": p["handle"],
                "text": p["text"][:1400]} for i, p in enumerate(posts)]
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(
            posts=json.dumps(compact, ensure_ascii=False))}],
        "response_format": {"type": "json_object"}, "temperature": 0.0,
        "max_tokens": 4500, "thinking": {"type": "disabled"},
    }
    error = None
    for attempt in range(4):
        try:
            response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload,
                                     headers={"Authorization": f"Bearer {key}"}, timeout=180)
            response.raise_for_status()
            rows = json.loads(response.json()["choices"][0]["message"]["content"]).get("items", [])
            by_index = {int(row["index"]): row for row in rows if "index" in row}
            return [by_index.get(i, {"index": i, "category": "classification_error"})
                    for i in range(len(posts))]
        except Exception as exc:
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Flash classification failed: {error}")


ELIGIBLE = {"early_long_action", "early_cycle_call", "early_mechanism_bull"}


def build_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label = row["classification"]
        if (label.get("category") in ELIGIBLE and label.get("original_judgment") and
                (label.get("actionable") or label.get("mechanism_present"))):
            grouped[row["post"]["handle"]].append(row)

    candidates = []
    for handle, evidence in grouped.items():
        evidence.sort(key=lambda r: r["post"]["published_at"])
        unique_dates = {r["post"]["date"] for r in evidence}
        mechanism = [r for r in evidence if r["classification"].get("mechanism_present")]
        cats = Counter(r["classification"]["category"] for r in evidence)
        eligible = len(unique_dates) >= 2 and bool(mechanism)
        score = 0.0
        for row in evidence:
            d = date.fromisoformat(row["post"]["date"])
            timing = max(0.0, (DISCOVERY_TO - d).days / (DISCOVERY_TO - DISCOVERY_FROM).days)
            label = row["classification"]
            base = {"early_cycle_call": 10, "early_long_action": 9,
                    "early_mechanism_bull": 8}[label["category"]]
            score += base + 4 * timing + int(label.get("explicitness", 0)) + \
                int(label.get("reasoning_quality", 0))
        candidates.append({
            "handle": handle, "passes_evidence_gate": eligible,
            "discovery_score": round(score, 2), "evidence_count": len(evidence),
            "unique_dates": len(unique_dates), "mechanism_count": len(mechanism),
            "first_evidence_date": evidence[0]["post"]["date"],
            "category_counts": dict(cats), "evidence": evidence[:12],
        })
    return sorted(candidates, key=lambda c: (not c["passes_evidence_gate"],
                                               -c["discovery_score"],
                                               c["first_evidence_date"], c["handle"]))


def render(result: dict[str, Any]) -> str:
    stats = result["stats"]
    lines = [
        "# 2025年存储启动期多头：低成本历史探针", "",
        f"发现窗口：{DISCOVERY_FROM} 至 {DISCOVERY_TO}；本窗口只用于发现，不进入后续盲测。  ",
        f"复用数据库 {stats['db_posts']} 条；Apify 新取 {stats['apify_posts']} 条；去重后 {stats['unique_posts']} 条。", "",
        "## 覆盖与停止条件", "",
        f"- 查询数：{len(result['query_stats'])}；触顶查询：{sum(q['hit_cap'] for q in result['query_stats'])}。",
        f"- 通过证据门槛作者：{stats['passing_candidates']}；门槛为不同日期至少2条，且至少1条含周期/供给/价格机制。",
        "- 本轮是探针；在审计日期覆盖和候选质量前，不自动扩大搜索、不做历史深抓。", "",
        "## 候选", "", "| 排名 | 作者 | 通过门槛 | 分数 | 证据 | 日期数 | 机制证据 | 最早日期 |",
        "|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for i, c in enumerate(result["candidates"][:30], 1):
        lines.append(f"| {i} | [@{c['handle']}](https://x.com/{c['handle']}) | "
                     f"{'是' if c['passes_evidence_gate'] else '否'} | {c['discovery_score']:.2f} | "
                     f"{c['evidence_count']} | {c['unique_dates']} | {c['mechanism_count']} | {c['first_evidence_date']} |")
    lines += ["", "## 下一步", "", "仅对人工审计通过者做分月轻测；发现窗口严格排除。若查询日期覆盖不足或已知种子均无法召回，先修搜索层，不追加预算。"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/memory_startup_probe_20260811")
    parser.add_argument("--db-gz", default="data/signalboard.db.gz")
    args = parser.parse_args()
    apify = os.environ["APIFY_TOKEN"]
    deepseek = os.environ["DEEPSEEK_API_KEY"]
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    existing, existing_stats = db_posts(Path(args.db_gz))
    query_specs = [(q, MAX_ITEMS_BROAD) for q in BROAD_QUERIES]
    query_specs += [(f"from:{h} (SNDK OR WDC OR MU OR Micron OR SanDisk OR DRAM OR NAND OR HBM)",
                     MAX_ITEMS_SEED) for h in SEED_HANDLES]
    fetched, query_stats = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_query, apify, q, cap): q for q, cap in query_specs}
        for future in as_completed(futures):
            query = futures[future]
            posts, stats = future.result()
            fetched.extend(posts); query_stats.append(stats)
            print(f"query complete: {query}: {stats}", flush=True)
    query_stats.sort(key=lambda q: q["query"])

    dedup = {p["post_id"]: p for p in existing}
    for post in fetched:
        # Prefer paid raw source when the same post also exists in DB.
        dedup[post["post_id"]] = post
    posts = sorted(dedup.values(), key=lambda p: (p["published_at"], p["handle"]))

    batches = [(i, posts[i:i + 14]) for i in range(0, len(posts), 14)]
    classified: dict[int, list[dict[str, Any]]] = {}
    failures = 0
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(classify_batch, batch, deepseek): (start, batch)
                   for start, batch in batches}
        for future in as_completed(futures):
            start, batch = futures[future]
            try:
                labels = future.result()
            except Exception as exc:
                failures += len(batch)
                labels = [{"category": "classification_error", "reason": str(exc)[:300]}
                          for _ in batch]
            classified[start] = [{"post": p, "classification": lab}
                                 for p, lab in zip(batch, labels)]
    if failures > max(14, int(len(posts) * 0.05)):
        raise RuntimeError(f"classification failures too high: {failures}/{len(posts)}")
    rows = [row for start, _ in batches for row in classified[start]]
    candidates = build_candidates(rows)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method_version": "memory-startup-probe-v1",
        "discovery_only": True,
        "discovery_window": [DISCOVERY_FROM.isoformat(), DISCOVERY_TO.isoformat()],
        "validation_rule": "All discovery-window evidence is excluded from later blind scores.",
        "existing_db": existing_stats, "query_stats": query_stats,
        "stats": {"db_posts": len(existing), "apify_posts": len(fetched),
                  "unique_posts": len(posts), "classification_failures": failures,
                  "candidate_count": len(candidates),
                  "passing_candidates": sum(c["passes_evidence_gate"] for c in candidates)},
        "candidates": candidates,
    }
    (out / "probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render(result), encoding="utf-8")
    with gzip.open(out / "raw_posts.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(posts, fh, ensure_ascii=False)
    print(json.dumps(result["stats"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
