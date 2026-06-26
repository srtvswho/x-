"""Retry 失败的 direction + 然后 verify 3 人

策略: 用更大 max_tokens (800) + 更短 prompt retry ? 条
"""
import json
import os
import re
import time
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path

OUT_DIR = Path("/workspace/logs/p5_4kol_triage")
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
MAX_WORKERS = 30

dir_data = json.load(open(OUT_DIR / "direction_3kols.json"))


# 简化版 prompt, 给 max_tokens 800
PROMPT = """X 推文投资方向判定。给定推文+日期+ticker+attribution, 判方向。

【规则 — 严格按 P5 铁律 1+2】
- 看多: 关键词 buy/long/bullish/看多/做多/推荐/加仓/建仓/我会买/看好/"I will be buying"/"I bought"/"to me this is a buy"/"this is a great buy"/"screaming buy"/"strong buy"/"tier 1 buy"/"the stock is cheap"
- 看空: sell/short/bearish/看空/做空/不推荐/减仓/清仓/"I sold"/"I am short"/"overvalued"/"the stock is expensive"/"concerns about / 担忧"
- 暗示: "Bought $X today" / "Sold $X today" / "Opened position" / "I am long" / "I am short" → 强方向
- "tobi thinks the stock is cheap" / "I am excited about $X" / "I see this going higher" / "I see this going lower" → 隐含 long/short
- "to me X is a buy" = long; "X is going down" = short

区分对象 (铁律 2):
- 消费建议 (buy electronics/products) → neutral
- 产品 launch 预测 (VR 不会出) → neutral
- 产业 fact (why CEO didn't announce X) → neutral
- 询问式 (Are you buying?) → neutral
- 评价/感慨 (great product) → neutral
- 多人 ticker 没对单个表态 → neutral

【输出严格 JSON】
{{
  "direction": "long" / "short" / "neutral",
  "thesis": "作者原话 ≤ 30 字",
  "evidence_keyword": "触发判定的关键词"
}}
"""


def llm_direction_short(text: str, date: str, ticker: str, attribution: str) -> dict:
    full = f"【推文】{text[:1200]}\n【日期】{date}\n【ticker】{ticker or '(无 $)'}\n【attribution】{attribution}"
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": PROMPT + "\n\n" + full}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 800,
    }).encode()
    last_err = "?"
    for retry in range(3):
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            cs = resp["choices"][0]["message"]["content"]
            if not cs:
                raise ValueError("empty content")
            return json.loads(cs)
        except Exception as e:
            last_err = str(e)
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return {"direction": "?", "thesis": f"err: {last_err[:50]}", "evidence_keyword": ""}


def main():
    t0 = time.time()
    print(f"[{time.time()-t0:.0f}s] Retry ? direction (max_tokens=800, workers={MAX_WORKERS})", flush=True)

    n_total_failed = 0
    n_total_resolved = 0
    n_total_failed_still = 0

    for h, r in dir_data.items():
        judgments = r["judgments"]
        failed = [j for j in judgments if j.get("llm_direction") == "?"]
        n_total_failed += len(failed)
        print(f"\n[{time.time()-t0:.0f}s] @{h}: retry {len(failed)} failed", flush=True)

        n_done = 0
        n_resolved = 0
        n_still_fail = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(llm_direction_short, j.get("excerpt", ""), j["date"], j.get("ticker", ""), "ORIGINAL"): j for j in failed}
            for fut in as_completed(futures):
                j = futures[fut]
                try:
                    d = fut.result()
                    if d.get("direction") in ("long", "short", "neutral"):
                        j["llm_direction"] = d["direction"]
                        j["llm_thesis"] = d.get("thesis", "")
                        j["llm_evidence"] = d.get("evidence_keyword", "")
                        n_resolved += 1
                    else:
                        n_still_fail += 1
                except Exception:
                    n_still_fail += 1
                n_done += 1
        n_total_resolved += n_resolved
        n_total_failed_still += n_still_fail
        print(f"  [{time.time()-t0:.0f}s]   resolved: {n_resolved}, still failed: {n_still_fail}", flush=True)

    # 重新统计
    for h, r in dir_data.items():
        c = Counter(j.get("llm_direction", "?") for j in r["judgments"])
        r["direction_count"] = dict(c)
        print(f"\n  {h}: {dict(c)}", flush=True)

    # 保存
    json.dump(dir_data, open(OUT_DIR / "direction_3kols_v2.json", "w"), indent=2, ensure_ascii=False)
    print(f"\n[{time.time()-t0:.0f}s] total failed before: {n_total_failed} resolved: {n_total_resolved} still: {n_total_failed_still}", flush=True)


if __name__ == "__main__":
    main()