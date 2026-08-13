#!/usr/bin/env python3
"""Out-of-sample validation for candidates discovered around the June 2026 memory top."""
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

import requests


HISTORY_FROM = date(2025, 8, 11)
HISTORY_TO = date(2026, 5, 14)  # hard wall: discovery window starts 2026-05-15
AS_OF = date(2026, 8, 11)
ACTOR_ID = "apidojo/tweet-scraper"
MODEL = "deepseek-v4-flash"
POLYGON_INTERVAL = 13.0
CANDIDATES = (
    "gsmferrari", "macroalphahq", "stanphylcap", "thierryborgeat",
    "oilstocktrader", "mampillyguru", "reasonus4", "ulkser",
    "stuckonstocks", "alshfaw", "lucybuilding", "itsmichaelluu",
)
REUSE_APIFY_RUN_IDS = {"sssjeffpu": "cd3e9bBIaKydLSDCi"}
CASHTAG = re.compile(r"\$([A-Za-z][A-Za-z0-9.]{0,7})\b")


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


def text_of(item: dict[str, Any]) -> str:
    return str(item.get("text") or item.get("fullText") or item.get("tweetText") or "").strip()


def normalize_post(item: dict[str, Any], handle: str) -> dict[str, Any] | None:
    text = text_of(item)
    dt = parse_datetime(item.get("createdAt") or item.get("created_at") or item.get("date"))
    if not text or not dt or item.get("isRetweet") or text.startswith("RT @"):
        return None
    if not (HISTORY_FROM <= dt.date() <= HISTORY_TO):
        return None
    post_id = str(item.get("id") or item.get("tweetId") or item.get("id_str") or "")
    if not post_id:
        post_id = hashlib.sha256(f"{handle}\n{dt.isoformat()}\n{text}".encode()).hexdigest()[:24]
    url = item.get("url") or item.get("tweetUrl") or f"https://x.com/{handle}/status/{post_id}"
    return {"post_id": post_id, "handle": handle, "published_at": dt.isoformat(),
            "date": dt.date().isoformat(), "text": text, "url": url}


def fetch_history(handle: str, token: str) -> list[dict[str, Any]]:
    from apify_client import ApifyClient
    client = ApifyClient(token)
    reuse_run_id = REUSE_APIFY_RUN_IDS.get(handle)
    if reuse_run_id:
        run = client.run(reuse_run_id).get()
    else:
        query = f"from:{handle} since:{HISTORY_FROM.isoformat()} until:{(HISTORY_TO + timedelta(days=1)).isoformat()}"
        run = client.actor(ACTOR_ID).call(run_input={"searchTerms": [query], "maxItems": 2500,
                                                     "sort": "Latest", "includeSearchTerms": False},
                                          timeout=timedelta(minutes=20), memory_mbytes=2048)
    dataset_id = getattr(run, "default_dataset_id", None)
    if not dataset_id and isinstance(run, dict):
        dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise RuntimeError(f"No dataset for @{handle}")
    posts = []
    for item in client.dataset(dataset_id).iterate_items():
        post = normalize_post(item, handle)
        if post:
            posts.append(post)
    dedup = {p["post_id"]: p for p in posts}
    return sorted(dedup.values(), key=lambda p: p["published_at"])


EXTRACT_PROMPT = """你是严格的公开投资信号审计员。逐条判断帖子是否包含作者本人当时可执行的、面向未来的美股方向判断。不要把新闻转述、复盘战绩、持仓截图、自夸、模糊两面话或别人的观点算成信号。

每条输出 index、post_type（forward/retrospective/relay/neutral）、original_judgment、signals。signals 每项包含 ticker（标准美股代码）、direction（long/short）、action（open/add/reduce/close/avoid/hold）、confidence(0-1)、reason。卖出/清仓/规避视为 short 方向；仅“持有”且没有新判断不算。条件未触发的计划不算。一个帖子可有多个标的，但只提到代码而没有逐标的方向时不要生成。

帖子：{posts}

仅输出 JSON：{{"items":[...]}}。"""


def extract_batch(posts: list[dict[str, Any]], api_key: str) -> list[dict[str, Any]]:
    compact = [{"index": i, "date": p["date"], "text": p["text"][:1400]}
               for i, p in enumerate(posts)]
    payload = {"model": MODEL, "messages": [{"role": "user", "content": EXTRACT_PROMPT.format(
        posts=json.dumps(compact, ensure_ascii=False))}], "response_format": {"type": "json_object"},
        "temperature": 0.0, "max_tokens": 4500, "thinking": {"type": "disabled"}}
    last = None
    for attempt in range(4):
        try:
            r = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload,
                              headers={"Authorization": f"Bearer {api_key}"}, timeout=180)
            r.raise_for_status()
            parsed = json.loads(r.json()["choices"][0]["message"]["content"])
            rows = {int(x["index"]): x for x in parsed.get("items", []) if "index" in x}
            return [rows.get(i, {"index": i, "post_type": "error", "signals": []})
                    for i in range(len(posts))]
        except Exception as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Flash extraction failed: {last}")


def extract_signals(posts: list[dict[str, Any]], api_key: str) -> tuple[list[dict[str, Any]], int]:
    # Ad-hoc analyst accounts often use hashtags or company names instead of cashtags.
    # The strict LLM prompt still rejects relays, retrospectives and non-directional posts.
    targets = posts
    batches = [(i, targets[i:i + 12]) for i in range(0, len(targets), 12)]
    output: dict[int, list[dict[str, Any]]] = {}
    failed = 0
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(extract_batch, b, api_key): (start, b) for start, b in batches}
        done = 0
        for fut in as_completed(futures):
            start, batch = futures[fut]
            done += 1
            try:
                labels = fut.result()
            except Exception as exc:
                failed += len(batch)
                print(f"extract batch {start} failed: {exc}", flush=True)
                labels = [{"post_type": "error", "signals": []} for _ in batch]
            output[start] = [{"post": p, "label": lab} for p, lab in zip(batch, labels)]
            if done == 1 or done % 20 == 0 or done == len(batches):
                print(f"Extracted batches {done}/{len(batches)}", flush=True)
    if failed > max(12, int(len(targets) * 0.05)):
        raise RuntimeError(f"Extraction failures too high: {failed}/{len(targets)}")
    rows = [x for start, _ in batches for x in output[start]]
    signals = []
    for row in rows:
        lab = row["label"]
        if lab.get("post_type") != "forward" or not lab.get("original_judgment"):
            continue
        for sig in lab.get("signals", []):
            ticker = str(sig.get("ticker") or "").upper().replace("$", "")
            if (re.fullmatch(r"[A-Z][A-Z0-9.]{0,7}", ticker) and
                    sig.get("direction") in ("long", "short") and
                    float(sig.get("confidence") or 0) >= 0.65):
                signals.append({**sig, "ticker": ticker, "post": row["post"]})
    return signals, failed


def dedup_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals.sort(key=lambda s: s["post"]["published_at"])
    kept, last = [], {}
    for sig in signals:
        key = (sig["post"]["handle"], sig["ticker"], sig["direction"])
        d = date.fromisoformat(sig["post"]["date"])
        if key in last and (d - last[key]).days < 7:
            continue
        last[key] = d
        kept.append(sig)
    return kept


def polygon_bars(ticker: str, api_key: str) -> list[dict[str, Any]]:
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{HISTORY_FROM}/{AS_OF}"
    r = requests.get(url, params={"adjusted": "true", "sort": "asc", "limit": 5000,
                                  "apiKey": api_key}, timeout=60)
    if r.status_code == 429:
        time.sleep(POLYGON_INTERVAL)
        r = requests.get(url, params={"adjusted": "true", "sort": "asc", "limit": 5000,
                                      "apiKey": api_key}, timeout=60)
    r.raise_for_status()
    return [{"date": datetime.fromtimestamp(x["t"] / 1000, tz=timezone.utc).date(),
             "open": x["o"], "high": x["h"], "low": x["l"], "close": x["c"]}
            for x in r.json().get("results", [])]


def verify_signal(sig: dict[str, Any], bars: list[dict[str, Any]], bench: list[dict[str, Any]]) -> dict[str, Any] | None:
    source_date = date.fromisoformat(sig["post"]["date"])
    future = [b for b in bars if b["date"] > source_date]
    bench_future = [b for b in bench if b["date"] > source_date]
    if len(future) < 20 or len(bench_future) < 20:
        return None
    entry, exit_bar = future[0], future[19]
    bench_entry, bench_exit = bench_future[0], bench_future[19]
    sign = 1 if sig["direction"] == "long" else -1
    raw = sign * (exit_bar["close"] / entry["open"] - 1)
    bench_ret = sign * (bench_exit["close"] / bench_entry["open"] - 1)
    path = future[:20]
    path_returns = [sign * (b["close"] / entry["open"] - 1) for b in path]
    return {**sig, "entry_date": entry["date"].isoformat(), "entry_price": entry["open"],
            "exit_date": exit_bar["date"].isoformat(), "exit_price": exit_bar["close"],
            "raw_return": raw, "excess_soxx": raw - bench_ret,
            "mfe": max(path_returns), "mae": min(path_returns), "hit": raw > 0}


def wilson_lower(wins: int, n: int) -> float:
    if not n:
        return 0.0
    z, p = 1.96, wins / n
    return (p + z*z/(2*n) - z*math.sqrt((p*(1-p)+z*z/(4*n))/n)) / (1+z*z/n)


def summarize(handle: str, verified: list[dict[str, Any]], coverage: dict[str, Any]) -> dict[str, Any]:
    rows = [v for v in verified if v["post"]["handle"] == handle]
    wins = sum(v["hit"] for v in rows)
    n = len(rows)
    hit = wins / n if n else 0
    med = statistics.median(v["raw_return"] for v in rows) if rows else 0
    excess = statistics.median(v["excess_soxx"] for v in rows) if rows else 0
    shorts = sum(v["direction"] == "short" for v in rows)
    if n >= 20 and hit >= .60 and med > 0 and excess > 0:
        grade = "A"
    elif n >= 10 and hit >= .55 and med > 0:
        grade = "B"
    elif n >= 5 and hit >= .48:
        grade = "C"
    elif n < 5:
        grade = "INSUFFICIENT"
    else:
        grade = "D"
    ordered = sorted(rows, key=lambda v: v["raw_return"])
    return {"handle": handle, "grade": grade, "n": n, "wins": wins,
            "hit_rate": hit, "wilson_lower": wilson_lower(wins, n),
            "median_raw_return": med, "median_excess_soxx": excess,
            "median_mfe": statistics.median(v["mfe"] for v in rows) if rows else 0,
            "median_mae": statistics.median(v["mae"] for v in rows) if rows else 0,
            "short_share": shorts / n if n else 0, **coverage,
            "worst": ordered[:3], "best": list(reversed(ordered[-3:]))}


def render(result: dict[str, Any]) -> str:
    lines = ["# 存储顶部候选 KOL：独立历史盲测", "",
             f"验证历史：{HISTORY_FROM} 至 {HISTORY_TO}（与6月发现窗口完全隔离）  ",
             "统一口径：发帖后下一交易日开盘入场，20个交易日后收盘，重复同向信号7日去重。", "",
             "| 排名 | 作者 | 等级 | n | 命中率 | 中位收益 | 中位超额SOXX | 空头占比 |",
             "|---:|---|---|---:|---:|---:|---:|---:|"]
    for i, c in enumerate(result["ranking"], 1):
        lines.append(f"| {i} | @{c['handle']} | {c['grade']} | {c['n']} | {c['hit_rate']:.1%} | {c['median_raw_return']:.1%} | {c['median_excess_soxx']:.1%} | {c['short_share']:.1%} |")
    lines += ["", "## 口径限制", "", "- 发现用的 2026-05-15 至 2026-07-25 帖子没有进入评分。", "- 只验证公开、原创、事前且方向明确的美股信号；事后复盘与转述不计。", "- 等级同时受样本量约束；单次精准顶部不能直接得到高等级。"]
    return "\n".join(lines) + "\n"


def main() -> None:
    global HISTORY_FROM, HISTORY_TO, AS_OF
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/memory_top_validation_20260811")
    parser.add_argument("--candidates", nargs="+", default=list(CANDIDATES),
                        help="X handles to validate (without @)")
    parser.add_argument("--history-from", default=HISTORY_FROM.isoformat())
    parser.add_argument("--history-to", default=HISTORY_TO.isoformat())
    parser.add_argument("--as-of", default=AS_OF.isoformat())
    args = parser.parse_args()
    HISTORY_FROM = date.fromisoformat(args.history_from)
    HISTORY_TO = date.fromisoformat(args.history_to)
    AS_OF = date.fromisoformat(args.as_of)
    candidates = tuple(h.lstrip("@").strip() for h in args.candidates if h.strip())
    if not candidates:
        parser.error("at least one candidate is required")
    apify, deepseek, polygon = (os.environ[x] for x in
                                ("APIFY_TOKEN", "DEEPSEEK_API_KEY", "POLYGON_API_KEY"))
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    histories = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_history, h, apify): h for h in candidates}
        for fut in as_completed(futures):
            h = futures[fut]; histories[h] = fut.result()
            print(f"@{h}: {len(histories[h])} history posts", flush=True)
    all_posts = [p for h in candidates for p in histories[h]]
    signals, failed = extract_signals(all_posts, deepseek)
    signals = dedup_signals(signals)

    tickers = sorted({s["ticker"] for s in signals} | {"SOXX"})
    prices = {}
    for i, ticker in enumerate(tickers, 1):
        try:
            prices[ticker] = polygon_bars(ticker, polygon)
            print(f"price {i}/{len(tickers)} {ticker}: {len(prices[ticker])}", flush=True)
        except Exception as exc:
            print(f"price failed {ticker}: {exc}", flush=True)
            prices[ticker] = []
        if i < len(tickers):
            time.sleep(POLYGON_INTERVAL)
    bench = prices["SOXX"]
    verified = [v for s in signals if prices.get(s["ticker"])
                if (v := verify_signal(s, prices[s["ticker"]], bench))]
    coverage = {h: {"raw_posts": len(histories[h]),
                    "cashtag_posts": sum(bool(CASHTAG.search(p["text"])) for p in histories[h]),
                    "extracted_signals": sum(s["post"]["handle"] == h for s in signals)}
                for h in candidates}
    ranking = [summarize(h, verified, coverage[h]) for h in candidates]
    ranking.sort(key=lambda c: (c["grade"] == "INSUFFICIENT", -c["hit_rate"],
                                -c["median_raw_return"], -c["n"]))
    result = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "validation_window": [HISTORY_FROM.isoformat(), HISTORY_TO.isoformat()],
              "discovery_window_excluded": ["2026-05-15", "2026-07-25"],
              "stats": {"raw_posts": len(all_posts), "dedup_signals": len(signals),
                        "verified_signals": len(verified), "flash_failed_posts": failed,
                        "price_tickers": len(tickers)},
              "ranking": ranking,
              "verified": verified}
    (out / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render(result), encoding="utf-8")
    print(json.dumps(result["stats"]), flush=True)


if __name__ == "__main__":
    main()
