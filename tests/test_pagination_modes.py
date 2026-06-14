"""基准测试:对比 2025-11 窗口的两种分页模式稳定性。

目标:验证 sort=Latest + disableMaximization=true 和 sort=Top + maxItems=3000
哪个能稳定返回完整 ~393 条(用 2025-11 窗口做基准)。

只跑一次,需要 APIFY_TOKEN。手动:python tests/test_pagination_modes.py
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from signalboard.scraper import _call_actor, ACTOR_ID

HANDLE = "aleabitoreddit"
START = date(2025, 11, 1)
END = date(2025, 12, 1)

# 模式 A:禁用 maximize,手动控制分页(sort=Latest)
RUN_INPUT_A = {
    "customMapFunction": "(object) => { return {...object} }",
    "includeSearchTerms": False,
    "maxItems": 100,           # 控制每页大小
    "onlyImage": False,
    "onlyQuote": False,
    "onlyTwitterBlue": False,
    "onlyVerifiedUsers": False,
    "onlyVideo": False,
    "searchTerms": [f"from:{HANDLE} since:{START.isoformat()} until:{END.isoformat()}"],
    "sort": "Latest",
    "disableMaximization": True,  # 关键:让 actor 不自己 max 化
}

# 模式 B:sort=Top + 高 maxItems(让 actor 自己跑完)
RUN_INPUT_B = {
    "customMapFunction": "(object) => { return {...object} }",
    "includeSearchTerms": False,
    "maxItems": 3000,
    "onlyImage": False,
    "onlyQuote": False,
    "onlyTwitterBlue": False,
    "onlyVerifiedUsers": False,
    "onlyVideo": False,
    "searchTerms": [f"from:{HANDLE} since:{START.isoformat()} until:{END.isoformat()}"],
    "sort": "Top",            # 改用 Top 排序
}


def measure(mode_name: str, run_input: dict, token: str) -> dict:
    print(f"\n--- 模式 {mode_name} ---")
    print(f"run_input: {json.dumps(run_input, ensure_ascii=False)[:200]}")
    t0 = time.time()
    items = _call_actor(run_input, token)
    elapsed = time.time() - t0
    n = len(items)
    sentinels = sum(1 for it in items if isinstance(it, dict) and it.get("noResults") is True)
    real = n - sentinels
    print(f"  items: {n} ({sentinels} 哨兵), 真实 {real}, 耗时 {elapsed:.1f}s")
    # 真实推文数应该 ~393(已知 2025-11 完整数)
    score = abs(real - 393)
    print(f"  vs 目标 393: 偏差 {score}")
    return {
        "mode": mode_name,
        "items_returned": n,
        "sentinels": sentinels,
        "real": real,
        "elapsed_s": round(elapsed, 1),
        "deviation_from_393": score,
    }


def main():
    import os
    token = os.environ.get("APIFY_TOKEN", "")
    if not token:
        print("ERROR: APIFY_TOKEN not set")
        sys.exit(1)

    a = measure("A: sort=Latest + disableMaximization=true", RUN_INPUT_A, token)
    b = measure("B: sort=Top + maxItems=3000", RUN_INPUT_B, token)

    print("\n=== 基准测试结果 ===")
    for r in [a, b]:
        print(json.dumps(r, ensure_ascii=False))

    # 哪个更接近 393 + 偏差 < 5
    winner = None
    if a["deviation_from_393"] < 5 and a["deviation_from_393"] <= b["deviation_from_393"]:
        winner = "A"
    elif b["deviation_from_393"] < 5 and b["deviation_from_393"] < a["deviation_from_393"]:
        winner = "B"

    if winner:
        print(f"\n✓ 模式 {winner} 更准确,采用它作为默认")
    else:
        print("\n⚠ 两种都有偏差,需要进一步排查")


if __name__ == "__main__":
    main()
