#!/usr/bin/env python3
"""真实小规模冒烟脚本 — 拉 20 条推文验证字段映射。

⚠️⚠️⚠️ 会真实调用 Apify apidojo/tweet-scraper V2,按 $0.40/1000 条计费。
20 条 ≈ $0.008 ≈ 不到一分钱,很低但仍然要钱。

⚠️ 不会自动跑测试套件 — 单独执行:
    APIFY_TOKEN=xxx python scripts/scrape_real_smoke.py --handle aleabitoreddit
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signalboard.scraper import (
    ENV_API_TOKEN,
    fetch_account_history,
    format_coverage_report,
    init_db,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="真实小规模冒烟 — 拉 1 个月 20 条")
    parser.add_argument("--handle", required=True)
    parser.add_argument("--db", default="data/signalboard_smoke.db")
    parser.add_argument("--cache-dir", default=".cache_smoke")
    parser.add_argument(
        "--max-per-month", type=int, default=20,
        help="每月上限条数(默认 20,触发截断时自动二分细分)",
    )
    parser.add_argument("--months-back", type=int, default=1)
    args = parser.parse_args()

    if not os.environ.get(ENV_API_TOKEN):
        print(f"need {ENV_API_TOKEN} env var", file=sys.stderr)
        return 1

    init_db(args.db)
    t0 = time.time()
    summary = fetch_account_history(
        handle=args.handle,
        db_path=args.db,
        max_per_month=args.max_per_month,
        months_back=args.months_back,
        cache_dir=args.cache_dir,
        use_cache=True,
    )
    elapsed = time.time() - t0

    print("=" * 60)
    print(f"handle:           {summary.handle}")
    print(f"max_per_month:    {args.max_per_month}")
    print(f"months_planned:   {summary.months_planned}")
    print(f"months_done:      {summary.months_done}")
    print(f"total_scraped:    {summary.total_scraped}")
    print(f"windows_subdivided:{summary.windows_subdivided}")
    print(f"elapsed:          {elapsed:.1f}s")
    print(f"runs:             {json.dumps(summary.runs, indent=2, default=str)}")
    if summary.errors:
        print(f"errors ({len(summary.errors)}):")
        for e in summary.errors[:5]:
            print(f"  - {e}")
    print("=" * 60)
    print()
    print("覆盖率报告:")
    print(format_coverage_report(args.handle, args.db))
    print()
    print("验证 checklist:")
    print("  [1] 抽 5 条比对:raw_text 应该跟推特网页原文一致")
    print("      sqlite3 data/signalboard_smoke.db 'SELECT post_id, raw_text FROM raw_posts LIMIT 5'")
    print("  [2] raw_json 是否含完整原始 payload:")
    print("      sqlite3 data/signalboard_smoke.db \"SELECT substr(raw_json, 1, 200) FROM raw_posts LIMIT 1\"")
    print("  [3] 跑第二次,raw_posts 行数应不变:")
    print(f"      APIFY_TOKEN=... python scripts/scrape_real_smoke.py --handle {args.handle}")
    print("  [4] 中断后续抓:第一次跑时 Ctrl+C,再跑一次,行数应继续涨不重复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
