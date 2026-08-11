#!/usr/bin/env python3
"""Capped out-of-sample light validation for 2025 memory-startup candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


CANDIDATES = ("dgretta_author", "sam_badawi", "tradexwhisperer", "thevalueist")
WINDOWS = ((date(2024, 10, 1), date(2025, 4, 6)),
           (date(2025, 9, 12), date(2026, 5, 14)))
DISCOVERY_EXCLUDED = (date(2025, 4, 7), date(2025, 9, 11))
AS_OF = date(2026, 8, 11)
ACTOR_ID = "apidojo/tweet-scraper"
MODEL = "deepseek-v4-flash"
MAX_PER_AUTHOR_WINDOW = 240
POLYGON_INTERVAL = 13.0
CASHTAG = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,7})\b")
DENY_TICKERS = {"BTC", "ETH", "SOL", "XRP", "GOLD", "SILVER", "OIL", "USD", "AI", "USA"}


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
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


def dataset_id(run: Any) -> str:
    value = getattr(run, "default_dataset_id", None)
    if not value and isinstance(run, dict):
        value = run.get("defaultDatasetId") or run.get("default_dataset_id")
    if not value:
        raise RuntimeError(f"Apify run has no dataset: {type(run).__name__}")
    return str(value)


def normalize(item: dict[str, Any], handle: str, start: date, end: date) -> dict[str, Any] | None:
    text = str(item.get("text") or item.get("fullText") or item.get("tweetText") or "").strip()
    dt = parse_datetime(item.get("createdAt") or item.get("created_at") or item.get("date"))
    if not text or not dt or not start <= dt.date() <= end:
        return None
    if item.get("isRetweet") or text.startswith("RT @"):
        return None
    post_id = str(item.get("id") or item.get("tweetId") or item.get("id_str") or "")
    if not post_id:
        post_id = hashlib.sha256(f"{handle}\n{dt.isoformat()}\n{text}".encode()).hexdigest()[:24]
    return {"post_id": post_id, "handle": handle, "date": dt.date().isoformat(),
            "published_at": dt.astimezone(timezone.utc).isoformat(), "text": text,
            "url": item.get("url") or item.get("tweetUrl") or
                   f"https://x.com/{handle}/status/{post_id}",
            "validation_window": [start.isoformat(), end.isoformat()]}


def fetch_window(handle: str, start: date, end: date, token: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from apify_client import ApifyClient

    query = f"from:{handle} filter:cashtags since:{start} until:{end + timedelta(days=1)} -filter:retweets"
    client = ApifyClient(token)
    run = client.actor(ACTOR_ID).call(
        run_input={"searchTerms": [query], "maxItems": MAX_PER_AUTHOR_WINDOW,
                   "sort": "Latest", "includeSearchTerms": False},
        timeout=timedelta(minutes=15), memory_mbytes=2048)
    items = list(client.dataset(dataset_id(run)).iterate_items())
    posts = [p for item in items if (p := normalize(item, handle, start, end))]
    posts = sorted({p["post_id"]: p for p in posts}.values(), key=lambda p: p["published_at"])
    return posts, {"handle": handle, "window": [start.isoformat(), end.isoformat()],
                   "returned": len(items), "valid": len(posts),
                   "hit_cap": len(items) >= MAX_PER_AUTHOR_WINDOW,
                   "earliest": posts[0]["date"] if posts else None,
                   "latest": posts[-1]["date"] if posts else None}


PROMPT = """你是严格的公开投资信号审计员。逐条判断帖子是否包含作者本人当时可执行、面向未来的美股方向判断。禁止把新闻转述、券商研报搬运、别人的观点、事后复盘、自报战绩、模糊两面话、未触发的条件计划算成信号。

每条输出：index、post_type（forward/retrospective/relay/neutral）、original_judgment（必须是布尔值）、signals。signals 每项包含 ticker（标准美股代码）、direction（long/short）、action（open/add/reduce/close/avoid）、confidence(0-1)、reason。仅持有但没有新的前瞻判断不算。提到多个代码但未逐个给方向时不要生成。

帖子：{posts}

仅输出 JSON：{{"items":[...]}}。"""


def extract_batch(posts: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    import requests

    compact = [{"index": i, "date": p["date"], "text": p["text"][:1500]}
               for i, p in enumerate(posts)]
    payload = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT.format(
        posts=json.dumps(compact, ensure_ascii=False))}],
        "response_format": {"type": "json_object"}, "temperature": 0.0,
        "max_tokens": 4500, "thinking": {"type": "disabled"}}
    error = None
    for attempt in range(4):
        try:
            response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload,
                                     headers={"Authorization": f"Bearer {key}"}, timeout=180)
            response.raise_for_status()
            rows = json.loads(response.json()["choices"][0]["message"]["content"]).get("items", [])
            indexed = {int(row["index"]): row for row in rows if "index" in row}
            return [indexed.get(i, {"index": i, "post_type": "error", "signals": []})
                    for i in range(len(posts))]
        except Exception as exc:
            error = exc; time.sleep(2 ** attempt)
    raise RuntimeError(f"Flash extraction failed: {error}")


def extract_signals(posts: list[dict[str, Any]], key: str) -> tuple[list[dict[str, Any]], int]:
    targets = [p for p in posts if CASHTAG.search(p["text"])]
    batches = [(i, targets[i:i + 12]) for i in range(0, len(targets), 12)]
    output, failures = {}, 0
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(extract_batch, batch, key): (start, batch)
                   for start, batch in batches}
        for future in as_completed(futures):
            start, batch = futures[future]
            try:
                labels = future.result()
            except Exception as exc:
                failures += len(batch)
                labels = [{"post_type": "error", "signals": [], "error": str(exc)[:300]}
                          for _ in batch]
            output[start] = list(zip(batch, labels))
    if failures > max(12, int(len(targets) * .05)):
        raise RuntimeError(f"Flash failures too high: {failures}/{len(targets)}")
    signals = []
    for start, _ in batches:
        for post, label in output[start]:
            if label.get("post_type") != "forward" or label.get("original_judgment") is not True:
                continue
            for signal in label.get("signals", []):
                ticker = str(signal.get("ticker") or "").upper().replace("$", "")
                if (re.fullmatch(r"[A-Z][A-Z0-9.]{0,7}", ticker) and ticker not in DENY_TICKERS and
                        signal.get("direction") in ("long", "short") and
                        float(signal.get("confidence") or 0) >= .65):
                    signals.append({**signal, "ticker": ticker, "post": post})
    return signals, failures


def dedup_events(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals.sort(key=lambda s: s["post"]["published_at"])
    kept, last = [], {}
    for signal in signals:
        key = (signal["post"]["handle"], signal["ticker"], signal["direction"])
        day = date.fromisoformat(signal["post"]["date"])
        if key in last and (day - last[key]).days < 21:
            continue
        last[key] = day; kept.append(signal)
    return kept


def polygon_bars(ticker: str, key: str) -> list[dict[str, Any]]:
    import requests

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{WINDOWS[0][0]}/{AS_OF}"
    response = requests.get(url, params={"adjusted": "true", "sort": "asc", "limit": 5000,
                                                 "apiKey": key}, timeout=60)
    if response.status_code == 429:
        time.sleep(POLYGON_INTERVAL)
        response = requests.get(url, params={"adjusted": "true", "sort": "asc", "limit": 5000,
                                             "apiKey": key}, timeout=60)
    response.raise_for_status()
    return [{"date": datetime.fromtimestamp(x["t"] / 1000, tz=timezone.utc).date(),
             "open": x["o"], "high": x["h"], "low": x["l"], "close": x["c"]}
            for x in response.json().get("results", [])]


def verify(signal: dict[str, Any], bars: list[dict[str, Any]], bench: list[dict[str, Any]]) -> dict[str, Any] | None:
    source = date.fromisoformat(signal["post"]["date"])
    future = [b for b in bars if b["date"] > source]
    bench_future = [b for b in bench if b["date"] > source]
    if len(future) < 20 or len(bench_future) < 20:
        return None
    entry, exit_bar = future[0], future[19]
    b_entry, b_exit = bench_future[0], bench_future[19]
    sign = 1 if signal["direction"] == "long" else -1
    raw = sign * (exit_bar["close"] / entry["open"] - 1)
    bret = sign * (b_exit["close"] / b_entry["open"] - 1)
    path = [sign * (b["close"] / entry["open"] - 1) for b in future[:20]]
    return {**signal, "entry_date": entry["date"].isoformat(), "exit_date": exit_bar["date"].isoformat(),
            "entry_price": entry["open"], "exit_price": exit_bar["close"],
            "raw_return": raw, "excess_soxx": raw - bret,
            "mfe": max(path), "mae": min(path), "hit": raw > 0}


def wilson(wins: int, n: int) -> float:
    if not n: return 0.0
    z, p = 1.96, wins / n
    return (p + z*z/(2*n) - z*math.sqrt((p*(1-p)+z*z/(4*n))/n)) / (1+z*z/n)


def summarize(handle: str, rows: list[dict[str, Any]], coverage: dict[str, Any]) -> dict[str, Any]:
    own = [r for r in rows if r["post"]["handle"] == handle]
    wins, n = sum(r["hit"] for r in own), len(own)
    ordered = sorted(own, key=lambda r: r["raw_return"])
    return {"handle": handle, "n": n, "wins": wins, "hit_rate": wins/n if n else 0,
            "wilson_lower": wilson(wins, n),
            "median_raw_return": statistics.median(r["raw_return"] for r in own) if own else 0,
            "median_excess_soxx": statistics.median(r["excess_soxx"] for r in own) if own else 0,
            "median_mfe": statistics.median(r["mfe"] for r in own) if own else 0,
            "median_mae": statistics.median(r["mae"] for r in own) if own else 0,
            **coverage, "worst": ordered[:3], "best": list(reversed(ordered[-3:]))}


def render(result: dict[str, Any]) -> str:
    lines = ["# 2025存储启动期候选：发现窗口外轻测", "",
             "发现窗口 2025-04-07 至 2025-09-11 完全排除；同作者/标的/方向21日内合并为一个事件。", "",
             "| 排名 | 作者 | n | 命中率 | 中位收益 | 中位超额SOXX | 抓取帖数 | 是否触顶 |",
             "|---:|---|---:|---:|---:|---:|---:|---|"]
    for i, row in enumerate(result["ranking"], 1):
        lines.append(f"| {i} | @{row['handle']} | {row['n']} | {row['hit_rate']:.1%} | "
                     f"{row['median_raw_return']:.1%} | {row['median_excess_soxx']:.1%} | "
                     f"{row['raw_posts']} | {'是' if row['hit_cap'] else '否'} |")
    lines += ["", "本轮为轻测：只有结果和最差案例经人工审计后，才决定是否补抓完整历史。"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/memory_startup_light_validation_20260811")
    args = parser.parse_args()
    apify, deepseek, polygon = (os.environ[x] for x in
                                ("APIFY_TOKEN", "DEEPSEEK_API_KEY", "POLYGON_API_KEY"))
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    histories, fetch_stats = defaultdict(list), []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_window, h, s, e, apify): (h, s, e)
                   for h in CANDIDATES for s, e in WINDOWS}
        for future in as_completed(futures):
            posts, stats = future.result(); histories[stats["handle"]].extend(posts); fetch_stats.append(stats)
            print(f"history complete: {stats}", flush=True)
    for handle in CANDIDATES:
        histories[handle] = sorted({p["post_id"]: p for p in histories[handle]}.values(),
                                   key=lambda p: p["published_at"])
    posts = [p for h in CANDIDATES for p in histories[h]]
    signals, failures = extract_signals(posts, deepseek)
    signals = dedup_events(signals)

    tickers = sorted({s["ticker"] for s in signals} | {"SOXX"})
    prices = {}
    for i, ticker in enumerate(tickers, 1):
        try:
            prices[ticker] = polygon_bars(ticker, polygon)
        except Exception as exc:
            print(f"price failed {ticker}: {exc}", flush=True); prices[ticker] = []
        print(f"price {i}/{len(tickers)} {ticker}: {len(prices[ticker])}", flush=True)
        if i < len(tickers): time.sleep(POLYGON_INTERVAL)
    bench = prices.get("SOXX", [])
    verified = [v for s in signals if prices.get(s["ticker"])
                if (v := verify(s, prices[s["ticker"]], bench))]
    coverage = {h: {"raw_posts": len(histories[h]),
                    "hit_cap": any(x["handle"] == h and x["hit_cap"] for x in fetch_stats),
                    "extracted_events": sum(s["post"]["handle"] == h for s in signals)}
                for h in CANDIDATES}
    ranking = [summarize(h, verified, coverage[h]) for h in CANDIDATES]
    ranking.sort(key=lambda x: (-x["hit_rate"], -x["median_raw_return"], -x["n"]))
    result = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "method_version": "memory-startup-light-validation-v1",
              "validation_windows": [[s.isoformat(), e.isoformat()] for s, e in WINDOWS],
              "discovery_window_excluded": [d.isoformat() for d in DISCOVERY_EXCLUDED],
              "stats": {"raw_posts": len(posts), "dedup_events": len(signals),
                        "verified_events": len(verified), "flash_failures": failures,
                        "price_tickers": len(tickers)},
              "fetch_stats": fetch_stats, "ranking": ranking}
    (out / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render(result), encoding="utf-8")
    print(json.dumps(result["stats"]), flush=True)


if __name__ == "__main__": main()
