#!/usr/bin/env python3
"""Second-pass, time-sliced discovery for 2025 memory-cycle authors.

Reuses the first probe's paid raw posts, then fills only known coverage gaps.
The expanded discovery window remains excluded from later validation scores.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "discover_memory_startup_kols.py"
if not BASE_PATH.exists():
    BASE_PATH = Path(__file__).with_name("startup_probe.py")
spec = importlib.util.spec_from_file_location("memory_startup_probe_base", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

DISCOVERY_FROM = date(2025, 3, 1)
DISCOVERY_TO = date(2025, 10, 31)
ACTOR_ID = "apidojo/tweet-scraper"
MAX_ITEMS_SLICE = 105
MAX_ITEMS_TARGET = 80

# August is deliberately omitted: it was well represented by the first broad probe
# and the existing DB. The intervals below fill never-covered and cap-distorted areas.
SEARCH_SLICES = (
    (date(2025, 3, 1), date(2025, 3, 31)),
    (date(2025, 4, 1), date(2025, 4, 6)),
    (date(2025, 4, 7), date(2025, 4, 30)),
    (date(2025, 5, 1), date(2025, 5, 31)),
    (date(2025, 6, 1), date(2025, 6, 30)),
    (date(2025, 7, 1), date(2025, 7, 31)),
    (date(2025, 9, 12), date(2025, 9, 30)),
    (date(2025, 10, 1), date(2025, 10, 31)),
)

QUERY_FAMILIES = (
    '(\u0024MU OR Micron OR \u0024SNDK OR SanDisk OR \u0024WDC OR "Western Digital") '
    '(buy OR long OR add OR bullish OR undervalued OR upside OR calls OR "sell put")',
    '(DRAM OR NAND OR HBM OR DDR4 OR SSD OR "memory pricing" OR "contract price") '
    '(inventory OR shortage OR supply OR pricing OR ASP OR capacity OR utilization OR '
    'earnings OR estimates OR upcycle OR cycle)',
)

TARGET_HANDLES = ("oopsguess", "mukund", "wallstjesus", "askfinnnow")


def timing_tier(day: date) -> tuple[str, float]:
    if day <= date(2025, 6, 30):
        return "startup_discoverer", 1.0
    if day <= date(2025, 9, 11):
        return "early_confirmer", 0.7
    return "trend_confirmer", 0.4


def dataset_id(run: Any) -> str:
    value = getattr(run, "default_dataset_id", None)
    if not value and isinstance(run, dict):
        value = run.get("defaultDatasetId") or run.get("default_dataset_id")
    if not value:
        raise RuntimeError("Apify run has no default dataset")
    return str(value)


def fetch_slice(token: str, query: str, start: date, end: date, cap: int,
                kind: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from apify_client import ApifyClient

    advanced = f"{query} since:{start} until:{end + timedelta(days=1)} -filter:retweets"
    client = ApifyClient(token)
    run = client.actor(ACTOR_ID).call(
        run_input={"searchTerms": [advanced], "maxItems": cap, "sort": "Latest",
                   "includeSearchTerms": False, "onlyVerifiedUsers": False,
                   "onlyTwitterBlue": False},
        timeout=timedelta(minutes=15), memory_mbytes=2048,
    )
    items = list(client.dataset(dataset_id(run)).iterate_items())
    posts = []
    for item in items:
        post = base.normalize_post(item, advanced, kind)
        if post and start <= date.fromisoformat(post["date"]) <= end:
            posts.append(post)
    ordered = sorted({p["post_id"]: p for p in posts}.values(),
                     key=lambda p: p["published_at"])
    return ordered, {
        "query": query, "kind": kind, "window": [start.isoformat(), end.isoformat()],
        "cap": cap, "returned": len(items), "valid": len(ordered),
        "hit_cap": len(items) >= cap,
        "earliest": ordered[0]["date"] if ordered else None,
        "latest": ordered[-1]["date"] if ordered else None,
    }


def load_prior(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        rows = json.load(fh)
    return [p for p in rows if DISCOVERY_FROM <= date.fromisoformat(p["date"]) <= DISCOVERY_TO]


def add_timing(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for candidate in candidates:
        tier, multiplier = timing_tier(date.fromisoformat(candidate["first_evidence_date"]))
        candidate["timing_tier"] = tier
        candidate["timing_multiplier"] = multiplier
        candidate["timing_adjusted_score"] = round(candidate["discovery_score"] * multiplier, 2)
    return sorted(candidates, key=lambda c: (
        not c["passes_evidence_gate"], -c["timing_adjusted_score"],
        c["first_evidence_date"], c["handle"]))


def render(result: dict[str, Any]) -> str:
    s = result["stats"]
    lines = [
        "# 2025存储周期作者：第二轮时间切片扩搜", "",
        "发现窗口扩展至2025-03-01至2025-10-31；全部发现证据继续排除在后续盲测之外。", "",
        "时间分层：3–6月=启动发现者；7月–9月11日=早期确认者；9月12日–10月=趋势确认者。后两类可以晋级，但提前量权重分别为0.7和0.4。", "",
        f"复用首轮原帖 {s['prior_posts']} 条；新抓 {s['new_posts']} 条；合并去重 {s['unique_posts']} 条。  ",
        f"查询 {s['queries']} 组，触顶 {s['hit_cap_queries']} 组，通过自动证据门槛 {s['passing_candidates']} 人。", "",
        "| 排名 | 作者 | 时间层 | 调整分 | 原始分 | 证据 | 日期数 | 机制 | 最早证据 |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for i, c in enumerate(result["candidates"][:50], 1):
        lines.append(
            f"| {i} | [@{c['handle']}](https://x.com/{c['handle']}) | {c['timing_tier']} | "
            f"{c['timing_adjusted_score']:.2f} | {c['discovery_score']:.2f} | "
            f"{c['evidence_count']} | {c['unique_dates']} | {c['mechanism_count']} | "
            f"{c['first_evidence_date']} |")
    lines += ["", "新增候选须人工排除研报搬运、新闻摘要、无关标的与产品营销后，才进入发现窗口外轻测。"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-raw", default="outputs/memory_startup_probe_20260811/raw_posts.json.gz")
    parser.add_argument("--output-dir", default="outputs/memory_startup_expansion_20260811")
    args = parser.parse_args()
    token, deepseek = os.environ["APIFY_TOKEN"], os.environ["DEEPSEEK_API_KEY"]
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    # The imported normalizer and candidate scorer read these globals dynamically.
    base.DISCOVERY_FROM, base.DISCOVERY_TO = DISCOVERY_FROM, DISCOVERY_TO
    prior = load_prior(Path(args.prior_raw))
    specs = [(q, start, end, MAX_ITEMS_SLICE, "monthly_slice")
             for start, end in SEARCH_SLICES for q in QUERY_FAMILIES]
    specs += [(f"from:{h} (SNDK OR WDC OR MU OR Micron OR SanDisk OR DRAM OR NAND OR HBM OR DDR4)",
               DISCOVERY_FROM, DISCOVERY_TO, MAX_ITEMS_TARGET, "targeted_followup")
              for h in TARGET_HANDLES]

    fetched, query_stats = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_slice, token, *spec): spec for spec in specs}
        for future in as_completed(futures):
            posts, stats = future.result()
            fetched.extend(posts); query_stats.append(stats)
            print(f"query complete: {stats}", flush=True)

    dedup = {p["post_id"]: p for p in prior}
    for p in fetched:
        dedup[p["post_id"]] = p
    posts = sorted(dedup.values(), key=lambda p: (p["published_at"], p["handle"]))

    batches = [(i, posts[i:i + 14]) for i in range(0, len(posts), 14)]
    classified, failures = {}, 0
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(base.classify_batch, batch, deepseek): (start, batch)
                   for start, batch in batches}
        for future in as_completed(futures):
            start, batch = futures[future]
            try:
                labels = future.result()
            except Exception as exc:
                failures += len(batch)
                labels = [{"category": "classification_error", "reason": str(exc)[:300]}
                          for _ in batch]
            classified[start] = [{"post": p, "classification": label}
                                 for p, label in zip(batch, labels)]
    if failures > max(14, int(len(posts) * 0.05)):
        raise RuntimeError(f"classification failures too high: {failures}/{len(posts)}")
    rows = [row for start, _ in batches for row in classified[start]]
    candidates = add_timing(base.build_candidates(rows))
    query_stats.sort(key=lambda x: (x["window"], x["kind"], x["query"]))
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method_version": "memory-startup-expansion-v2",
        "discovery_only": True,
        "discovery_window": [DISCOVERY_FROM.isoformat(), DISCOVERY_TO.isoformat()],
        "timing_tiers": {
            "startup_discoverer": ["2025-03-01", "2025-06-30", 1.0],
            "early_confirmer": ["2025-07-01", "2025-09-11", 0.7],
            "trend_confirmer": ["2025-09-12", "2025-10-31", 0.4],
        },
        "validation_rule": "All expanded discovery-window evidence is excluded from later blind scores.",
        "query_stats": query_stats,
        "stats": {"prior_posts": len(prior), "new_posts": len(fetched),
                  "unique_posts": len(posts), "queries": len(query_stats),
                  "hit_cap_queries": sum(q["hit_cap"] for q in query_stats),
                  "classification_failures": failures, "candidate_count": len(candidates),
                  "passing_candidates": sum(c["passes_evidence_gate"] for c in candidates)},
        "candidates": candidates,
    }
    (out / "expansion.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render(result), encoding="utf-8")
    with gzip.open(out / "raw_posts.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(posts, fh, ensure_ascii=False)
    print(json.dumps(result["stats"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
