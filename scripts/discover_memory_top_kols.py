#!/usr/bin/env python3
"""Discover X authors who identified the June 2026 memory-stock top in real time.

The event window is used only for candidate discovery. It must never be reused as
the candidate's out-of-sample validation score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import requests


AS_OF = date(2026, 8, 11)
PRICE_FROM = date(2026, 5, 15)
PEAK_FROM = date(2026, 6, 1)
PEAK_TO = date(2026, 7, 15)
SEARCH_FROM = date(2026, 5, 15)
SEARCH_TO = date(2026, 7, 25)
TICKERS = ("MU", "SNDK", "SOXX")
CONFIRM_DRAWDOWN = {"MU": 0.15, "SNDK": 0.15, "SOXX": 0.10}
ACTOR_ID = "apidojo/tweet-scraper"
MODEL = "deepseek-v4-flash"
KNOWN_HANDLES = {
    "jukan05", "aleabitoreddit", "zephyr_z9", "austinsemis", "kovainvest"
}
QUERIES = (
    "$MU (sell OR sold OR trim OR trimmed OR exit OR exited OR short OR top OR peak OR risk)",
    "Micron (sell OR trim OR exit OR short OR top OR peak OR overvalued)",
    "$SNDK (sell OR sold OR trim OR trimmed OR exit OR exited OR short OR top OR peak OR risk)",
    "SanDisk (sell OR trim OR exit OR short OR top OR peak OR overvalued)",
    "(DRAM OR NAND) (cycle top OR pricing peak OR price rollover OR demand slowdown OR inventory)",
    "(memory stocks OR memory cycle) (top OR peak OR sell OR trim OR short OR slowdown)",
    "(HBM OR high bandwidth memory) (peak OR slowdown OR orders OR demand OR inventory)",
    "(SK hynix OR Samsung memory) (sell OR top OR peak OR slowdown OR leverage)",
    "($SOXX OR $SMH) (sell OR trim OR exit OR short OR top OR risk off)",
    "(semiconductor OR semis) (cycle top OR peak earnings OR estimate cuts OR de-risk)",
    "美光 (顶部 OR 见顶 OR 减仓 OR 清仓 OR 做空 OR 周期 OR 库存)",
    "(存储 OR 内存 OR 闪迪 OR 海力士) (顶部 OR 见顶 OR 减仓 OR 清仓 OR 做空 OR 降速)",
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
    if raw.isdigit():
        return parse_datetime(int(raw))
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


def polygon_bars(ticker: str, api_key: str) -> list[dict[str, Any]]:
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{PRICE_FROM.isoformat()}/{AS_OF.isoformat()}"
    )
    response = requests.get(url, params={"adjusted": "true", "sort": "asc", "limit": 5000,
                                        "apiKey": api_key}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    bars = []
    for row in payload.get("results", []):
        day = datetime.fromtimestamp(row["t"] / 1000, tz=timezone.utc).date()
        bars.append({"date": day, "open": row["o"], "high": row["h"],
                     "low": row["l"], "close": row["c"]})
    if not bars:
        raise RuntimeError(f"Polygon returned no bars for {ticker}: {payload}")
    return bars


def define_event(ticker: str, bars: list[dict[str, Any]]) -> dict[str, Any]:
    peak_pool = [b for b in bars if PEAK_FROM <= b["date"] <= PEAK_TO]
    if not peak_pool:
        raise RuntimeError(f"No peak-window bars for {ticker}")
    peak = max(peak_pool, key=lambda b: b["high"])
    threshold = CONFIRM_DRAWDOWN[ticker]
    confirm = None
    for bar in bars:
        if bar["date"] > peak["date"] and bar["close"] <= peak["high"] * (1 - threshold):
            confirm = bar
            break
    cutoff = min(confirm["date"] if confirm else SEARCH_TO, SEARCH_TO)
    return {
        "ticker": ticker,
        "peak_date": peak["date"].isoformat(),
        "peak_high": peak["high"],
        "drawdown_threshold": threshold,
        "confirmation_date": confirm["date"].isoformat() if confirm else None,
        "confirmation_close": confirm["close"] if confirm else None,
        "evidence_cutoff": cutoff.isoformat(),
    }


def extract_text(item: dict[str, Any]) -> str:
    return str(item.get("text") or item.get("fullText") or item.get("tweetText") or "").strip()


def extract_handle(item: dict[str, Any]) -> str | None:
    author = item.get("author")
    value = None
    if isinstance(author, dict):
        value = author.get("userName") or author.get("username") or author.get("screen_name")
    value = value or item.get("userName") or item.get("username") or item.get("author_userName")
    if not value:
        match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/", str(item.get("url") or ""), re.I)
        value = match.group(1) if match else None
    return str(value).lower().lstrip("@") if value else None


def normalize_post(item: dict[str, Any], query: str) -> dict[str, Any] | None:
    text = extract_text(item)
    handle = extract_handle(item)
    dt = parse_datetime(item.get("createdAt") or item.get("created_at") or item.get("date") or
                        item.get("timestamp"))
    if not text or not handle or not dt:
        return None
    if item.get("isRetweet") or text.startswith("RT @"):
        return None
    post_id = str(item.get("id") or item.get("tweetId") or item.get("id_str") or "")
    url = item.get("url") or item.get("tweetUrl")
    if not url and post_id:
        url = f"https://x.com/{handle}/status/{post_id}"
    digest = hashlib.sha256(f"{handle}\n{dt.isoformat()}\n{text}".encode()).hexdigest()[:24]
    author_obj = item.get("author") if isinstance(item.get("author"), dict) else {}

    def safe_int(value: Any) -> int:
        try:
            return int(str(value or 0).replace(",", ""))
        except ValueError:
            return 0

    return {
        "post_id": post_id or digest,
        "handle": handle,
        "published_at": dt.astimezone(timezone.utc).isoformat(),
        "published_date": dt.date().isoformat(),
        "text": text,
        "url": url,
        "query": query,
        "likes": safe_int(item.get("likeCount") or item.get("favorite_count")),
        "reposts": safe_int(item.get("retweetCount") or item.get("retweet_count")),
        "followers": safe_int(author_obj.get("followers") or author_obj.get("followersCount")),
    }


def run_search(apify_token: str, query: str) -> list[dict[str, Any]]:
    from apify_client import ApifyClient

    client = ApifyClient(apify_token)
    advanced = f"{query} since:{SEARCH_FROM.isoformat()} until:{(SEARCH_TO + timedelta(days=1)).isoformat()}"
    run_input = {
        "searchTerms": [advanced],
        "maxItems": 1000,
        "sort": "Latest",
        "includeSearchTerms": False,
        "onlyVerifiedUsers": False,
        "onlyTwitterBlue": False,
    }
    run = client.actor(ACTOR_ID).call(run_input=run_input, timeout=timedelta(minutes=15),
                                      memory_mbytes=2048)
    if not run:
        raise RuntimeError(f"Apify returned no run for query: {query}")
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


CLASSIFY_PROMPT = """你是投资证据审计员。下面帖子来自一次候选发现搜索，目标是发现谁在2026年存储股顶部形成期实时识别了风险。逐条分类，禁止用后来走势替作者补充观点。

事件元数据：{events}

分类：
- advance_top_call：当时明确说见顶/周期顶/估值顶，或明确做空
- advance_exit：当时明确清仓/卖出/大幅减仓
- advance_risk_reduction：当时明确降低仓位或建议规避，尚未断言顶部
- advance_fundamental_slowdown：在回撤确认前指出价格二阶导、供给、库存、需求、盈利预期等将转弱，但动作不明确
- retrospective：主要是在事后回顾自己曾判断正确
- relay：转发、引用或复述他人判断，作者没有形成自己的结论
- vague：泛泛提示风险、技术位、两面话或没有明确方向
- unrelated：不相关

对每条帖子输出：index、category、tickers、actionable、original_judgment、reasoning_quality(0-3)、explicitness(0-3)、reason（一句中文）、evidence_quote（不超过18个英文单词或30个中文字符）。

帖子：
{posts}

仅输出 JSON：{{"items":[...]}}。"""


def classify_batch(posts: list[dict[str, Any]], events: dict[str, Any], api_key: str) -> list[dict[str, Any]]:
    compact = [{"index": i, "date": p["published_date"], "handle": p["handle"],
                "text": p["text"][:1200]} for i, p in enumerate(posts)]
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": CLASSIFY_PROMPT.format(
            events=json.dumps(events, ensure_ascii=False),
            posts=json.dumps(compact, ensure_ascii=False))}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 5000,
    }
    last_error = None
    for attempt in range(4):
        try:
            response = requests.post("https://api.deepseek.com/chat/completions", json=payload,
                                     headers={"Authorization": f"Bearer {api_key}"}, timeout=180)
            response.raise_for_status()
            body = response.json()
            parsed = json.loads(body["choices"][0]["message"]["content"])
            break
        except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 3:
                raise RuntimeError(f"Flash classification failed after retries: {exc}") from exc
            time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"Flash classification failed: {last_error}")
    by_index = {int(row["index"]): row for row in parsed.get("items", []) if "index" in row}
    return [by_index.get(i, {"index": i, "category": "classification_error",
                             "actionable": False, "original_judgment": False,
                             "reasoning_quality": 0, "explicitness": 0,
                             "reason": "模型未返回该条"}) for i in range(len(posts))]


ELIGIBLE = {"advance_top_call", "advance_exit", "advance_risk_reduction",
            "advance_fundamental_slowdown"}
CATEGORY_POINTS = {"advance_top_call": 10, "advance_exit": 9,
                   "advance_risk_reduction": 6, "advance_fundamental_slowdown": 5}


def candidate_score(evidence: list[dict[str, Any]], peak_dates: list[date]) -> float:
    score = 0.0
    for row in evidence:
        cls = row["classification"]
        d = date.fromisoformat(row["post"]["published_date"])
        days_before = max((peak - d).days for peak in peak_dates)
        timing = 4 if days_before >= 10 else 3 if days_before >= 3 else 2 if days_before >= 0 else 1
        engagement = math.log10(1 + row["post"]["likes"] + 2 * row["post"]["reposts"])
        score += (CATEGORY_POINTS.get(cls["category"], 0) + timing +
                  int(cls.get("reasoning_quality", 0)) + int(cls.get("explicitness", 0)) +
                  min(engagement, 2.0))
    return round(score + min(max(len(evidence) - 1, 0) * 2, 8), 2)


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 2026年6月存储顶部识别者：第一轮候选发现",
        "",
        f"生成时间：{result['generated_at']}  ",
        f"搜索原帖：{result['stats']['unique_posts']} 条；合格发现证据：{result['stats']['eligible_posts']} 条；候选作者：{result['stats']['candidate_count']} 人。",
        "",
        "> 本报告只用于找候选，不是胜率报告。6月事件不会进入候选人的后续盲测主分。",
        "",
        "## 事件锚点",
        "",
        "| 标的 | 峰值日 | 峰值 | 回撤确认日 | 证据截止日 |",
        "|---|---:|---:|---:|---:|",
    ]
    for event in result["events"].values():
        lines.append(f"| {event['ticker']} | {event['peak_date']} | {event['peak_high']:.2f} | {event['confirmation_date'] or '未确认'} | {event['evidence_cutoff']} |")
    lines += ["", "## 新候选排行榜", "", "| 排名 | 作者 | 发现分 | 合格证据 | 最早证据 | 类型 |", "|---:|---|---:|---:|---:|---|"]
    new_candidates = [c for c in result["candidates"] if not c["known"]]
    for rank, cand in enumerate(new_candidates[:40], 1):
        cats = ", ".join(f"{k}:{v}" for k, v in cand["category_counts"].items())
        lines.append(f"| {rank} | [@{cand['handle']}](https://x.com/{cand['handle']}) | {cand['discovery_score']:.2f} | {cand['eligible_evidence_count']} | {cand['first_evidence_date']} | {cats} |")
    lines += ["", "## 已知账号（仅作基准，不作为新人）", ""]
    known = [c for c in result["candidates"] if c["known"]]
    lines.append(", ".join(f"@{c['handle']} ({c['discovery_score']:.1f})" for c in known) or "无")
    lines += ["", "## 下一阶段", "", "对排行榜靠前作者抓取此前6–12个月完整公开历史；剔除本次6月发现窗口，按事前信号、原帖可追溯性、收益/MFE/MAE、相对SOXX收益和失败披露进行盲测。"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/memory_top_discovery_20260811")
    args = parser.parse_args()
    apify_token = os.environ["APIFY_TOKEN"]
    deepseek_key = os.environ["DEEPSEEK_API_KEY"]
    polygon_key = os.environ["POLYGON_API_KEY"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    events = {ticker: define_event(ticker, polygon_bars(ticker, polygon_key)) for ticker in TICKERS}
    dedup: dict[str, dict[str, Any]] = {}
    query_stats = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(run_search, apify_token, query): (pos, query)
                   for pos, query in enumerate(QUERIES, 1)}
        for future in as_completed(futures):
            pos, query = futures[future]
            print(f"[{pos}/{len(QUERIES)} complete] {query}", flush=True)
            try:
                items = future.result()
            except Exception as exc:
                print(f"Query failed: {exc}", flush=True)
                query_stats.append({"position": pos, "query": query, "returned": 0,
                                    "in_window": 0, "error": str(exc)[:500]})
                continue
            valid = 0
            for item in items:
                post = normalize_post(item, query)
                if not post:
                    continue
                d = date.fromisoformat(post["published_date"])
                if SEARCH_FROM <= d <= SEARCH_TO:
                    dedup.setdefault(post["post_id"], post)
                    valid += 1
            query_stats.append({"position": pos, "query": query,
                                "returned": len(items), "in_window": valid})
    query_stats.sort(key=lambda row: row["position"])

    posts = sorted(dedup.values(), key=lambda p: (p["published_at"], p["handle"]))
    classified = []
    for start in range(0, len(posts), 16):
        batch = posts[start:start + 16]
        print(f"Classify {start + 1}-{start + len(batch)}/{len(posts)}", flush=True)
        labels = classify_batch(batch, events, deepseek_key)
        classified.extend({"post": post, "classification": label} for post, label in zip(batch, labels))
        time.sleep(0.2)

    earliest_cutoff = min(date.fromisoformat(e["evidence_cutoff"]) for e in events.values())
    eligible_rows = []
    for row in classified:
        cls = row["classification"]
        d = date.fromisoformat(row["post"]["published_date"])
        mentioned = {str(t).upper().replace("$", "") for t in cls.get("tickers", [])}
        relevant = mentioned.intersection(events)
        valid_for = sorted(
            t for t in relevant if d <= date.fromisoformat(events[t]["evidence_cutoff"])
        )
        temporal_valid = bool(valid_for) if relevant else d <= earliest_cutoff
        row["temporal_valid_for"] = valid_for if relevant else (["INDUSTRY"] if temporal_valid else [])
        if (temporal_valid and cls.get("category") in ELIGIBLE and
                cls.get("original_judgment") and
                (cls.get("actionable") or cls.get("category") == "advance_fundamental_slowdown")):
            eligible_rows.append(row)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible_rows:
        grouped[row["post"]["handle"]].append(row)
    peak_dates = [date.fromisoformat(e["peak_date"]) for e in events.values()]
    candidates = []
    for handle, evidence in grouped.items():
        evidence.sort(key=lambda r: r["post"]["published_at"])
        counts: dict[str, int] = defaultdict(int)
        for row in evidence:
            counts[row["classification"]["category"]] += 1
        candidates.append({
            "handle": handle,
            "known": handle in KNOWN_HANDLES,
            "discovery_score": candidate_score(evidence, peak_dates),
            "eligible_evidence_count": len(evidence),
            "first_evidence_date": evidence[0]["post"]["published_date"],
            "category_counts": dict(sorted(counts.items())),
            "evidence": evidence[:12],
        })
    candidates.sort(key=lambda c: (-c["discovery_score"], c["first_evidence_date"], c["handle"]))

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method_version": "memory-top-discovery-v1",
        "discovery_only": True,
        "validation_exclusion": "All 2026-05-15 through 2026-07-25 discovery evidence must be excluded from candidate blind-validation scores.",
        "events": events,
        "queries": query_stats,
        "stats": {"unique_posts": len(posts), "eligible_posts": len(eligible_rows),
                  "candidate_count": len(candidates)},
        "candidates": candidates,
    }
    (output_dir / "candidates.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "report.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result["stats"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
