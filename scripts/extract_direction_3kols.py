"""3 KOL LLM 抽 direction 步骤 — P5 固化管道 步骤 3 (补)

对 amitisinvesting / StockSavvyShay / Sam_Badawi 的 ORIGINAL 推文,
并发 deepseek-v4-pro 抽 direction (long/short/neutral) + thesis.

每条独立 try/except + 3 retry + 25 worker.
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
MAX_WORKERS = 25

KOLS = ["amitisinvesting", "StockSavvyShay", "Sam_Badawi"]

# 重新加载 raw 拿完整 text
def load_text_by_id(handle):
    items = json.load(open(OUT_DIR / f"raw_{handle}.json"))
    return {it.get("id"): (it.get("text") or it.get("fullText") or "") for it in items if it.get("id")}

# 重新加载 attribution_results 拿 ORIGINAL judgments
attr = json.load(open(OUT_DIR / "attribution_results.json"))


PROMPT = """你是 X 推文投资方向判定器。判定作者对所提标的的"个人方向判断"。

【推文】{text}
【日期】{date}
【已识别 ticker】{ticker}
【attribution】{attribution} (ORIGINAL=作者自己判断 / RELAYED=搬运 / RC=搬运+自己加评)

【判定规则 — 严格按 P5 铁律 1+2】

1) 是否有明确建仓/推荐/不推荐声明?
   - 看多 (long): 含 buy/long/bullish/看多/做多/推荐/加仓/建仓/我会买/看好/"I'll be buying"/"I bought"/"I am long"/"to me this is a buy"
   - 看空 (short): 含 sell/short/bearish/看空/做空/不推荐/减仓/清仓/我会卖/看衰/"I sold"/"I am short"/"overvalued"
   - 暗示 (允许): "I am excited about $X" / "tobi thinks the stock is cheap" / "I see a screaming buy" / "this is a great buy"  ← 注意: 隐含 long 算
   - 暗示 short: "concerns about X" + 同向/反向/不看好/忧虑/跌/亏/估值高
   - "to me X is a buy" = long; "X is going down" = short
   - 间接动作: "Bought $X today" / "Sold $X today" / "Opened $X position" → 看多/看空

2) 区分对象 (铁律 2):
   - "buy electronics" "buy products" "buy devices" → neutral (消费建议)
   - 产品 launch 预测 ("Apple VR 不会出") → neutral (product 预测)
   - 产业 fact ("why CEO didn't announce X") → neutral (industry fact, 非建仓)
   - 询问式 (e.g. "Are you buying X?") → 中性, 算 neutral
   - 评价/感慨 (e.g. "this is a great product") → neutral (commentary)
   - 多人 ticker, 没对单个 ticker 表态 → neutral
   - 直接陈述 (e.g. "Why I'll be buying $TSLA") → 看声明方向

3) 含 hedge ("possible / maybe / perhaps / 也许 / 可能") → 仍算有方向, 但 confidence 低 (放在 evidence 备注)

4) 同一推文内, 同时说多又说空 → neutral (矛盾不取平均)

【输出严格 JSON】
{{
  "direction": "long" / "short" / "neutral",
  "thesis": "用作者原话 ≤ 30 字",
  "evidence_keyword": "触发判定的关键词/短句 (原文)"
}}

【例子】
- 原文 "Why I'll be buying $TSLA before the Q2 print" → direction=long, thesis="我会在 Q2 财报前买 TSLA"
- 原文 "Dave Portnoy has officially invested $500K in $AMC" → direction=neutral, thesis="新闻搬运, 无个人方向"
- 原文 "LONG $META" → direction=long
- 原文 "A TON OF THINGS HAPPENED IN THE STOCK MARKET TODAY" → direction=neutral
- 原文 "tobi thinks the stock is cheap" → direction=long (隐含看多)
- 原文 "Are you buying the SpaceX IPO?" → direction=neutral (问号结尾)
- 原文 "LONG $META in my view, target $1000" → direction=long
"""


def llm_direction(text: str, date: str, ticker: str, attribution: str) -> dict:
    prompt = PROMPT.format(text=text[:1500], date=date, ticker=ticker or "(无 $)", attribution=attribution)
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 400,
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
    print(f"[{time.time()-t0:.0f}s] 3 KOL LLM 抽 direction (workers={MAX_WORKERS})", flush=True)

    results = {}
    for h in KOLS:
        print(f"\n[{time.time()-t0:.0f}s] 处理 @{h}...", flush=True)
        text_by_id = load_text_by_id(h)
        judgments = attr[h]["judgments"]
        originals = [j for j in judgments if j.get("attribution") == "ORIGINAL"]
        print(f"  ORIGINAL={len(originals)}", flush=True)

        # 并发抽 direction
        def one(j):
            sid = j.get("source_id")
            text = text_by_id.get(sid) or j.get("excerpt", "")
            d = llm_direction(text, j["date"], j.get("ticker", ""), "ORIGINAL")
            return j, d

        n_done = 0
        n_err = 0
        c_dir = Counter()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(one, j): i for i, j in enumerate(originals)}
            for fut in as_completed(futures):
                try:
                    j, d = fut.result()
                    j["_dir"] = d
                    if d.get("direction") in ("long", "short"):
                        c_dir[d["direction"]] += 1
                    elif d.get("direction") == "?":
                        n_err += 1
                    n_done += 1
                    if n_done % 50 == 0:
                        print(f"  [{time.time()-t0:.0f}s]   direction {n_done}/{len(originals)} (err={n_err}) c={dict(c_dir)}", flush=True)
                except Exception as e:
                    n_err += 1
                    n_done += 1

        # 提升到顶层
        for j in originals:
            if j.get("_dir"):
                j["llm_direction"] = j["_dir"].get("direction", "?")
                j["llm_thesis"] = j["_dir"].get("thesis", "")
                j["llm_evidence"] = j["_dir"].get("evidence_keyword", "")

        # 统计
        c_dir = Counter(j.get("llm_direction", "?") for j in originals)
        results[h] = {
            "n_original": len(originals),
            "direction_count": dict(c_dir),
            "n_err": n_err,
            "judgments": originals,
        }
        print(f"  [{time.time()-t0:.0f}s]   direction: {dict(c_dir)} (err={n_err})", flush=True)

    # 保存
    out = OUT_DIR / "direction_3kols.json"
    json.dump(results, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"\n[{time.time()-t0:.0f}s] 📄 {out}", flush=True)
    print(f"[{time.time()-t0:.0f}s] ⏱️  总耗时: {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()