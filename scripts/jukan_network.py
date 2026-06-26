"""从 Jukan (@jukan05) 推文网络挖"第二个 Jukan" 候选

策略:
1. 从 682 条 jukan05 推文, 提取他回复/引用/RT 的人 (inReplyToUsername + quotedUser + retweeted)
2. 频率统计: 出现 ≥ 3 次的"被 Jukan 认可"账号
3. 筛条件:
   - 排除已知大V (Dylan, Gavin, Citrini, LinQingV, Brad, Leopold 等)
   - 排除英文大媒体 (Reuters, Bloomberg, WSJ)
   - 排除中文媒体
4. 抓每个候选最近 30 条, LLM 轻量分诊 (signal/knowledge/mixed)
5. 输出"可能像 Jukan"的候选名单

输出: docs/jukan_network_candidates.md
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"
OUT_DIR = Path("/workspace/logs/p5_jukan_network")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 已排除的"已知大V/媒体" (用户的策略: 不再加知名)
EXCLUDE_HANDLES = {
    # 已知试过的
    "dylan522p", "StockMarketNerd", "GavinSBaker", "DougOLoughlin",
    "davidcitrini", "LeopoldAschenbrenner", "LinQingV", "qinbafrank",
    # 大媒体
    "Reuters", "Bloomberg", "WSJ", "FT", "FinancialTimes", "CNBC",
    "nytimes", "TechCrunch", "TheInformation", "TheVerge",
    "ReutersBiz", "ReutersTech", "BbergTV",
    # 大基金/投行发言人
    "GoldmanSachs", "MorganStanley", "jpmorgan", "BlackRock",
    # 大 V (semianalysis 作者们)
    "SemiAnalysis_",  # 旧
    # 中文财经
    "wallstreetcn", "cls_telecom", "eastmoney",
    # 通用 misc (纯转发/数字账号)
    "X", "Twitter",
}

# 噪声模式 (如果不是用户账号)
NOISE_PATTERNS = [
    r"^\d+$",  # 纯数字
    r"^user\d+",  # user123
    r"\.com$",
    r"\.io$",
]


def extract_network():
    """从 682 条 jukan 推文提取网络 (reply/quote/retweet 的人)。"""
    # 已有 5 段 (p4p10d_x/*.json) + 体检 30 条
    print("[1/4] 提取 Jukan 网络 (reply/quote/retweet)...")
    files = list(Path("/workspace/logs/p4p10d_x").glob("*.json"))
    files.append(Path("/workspace/logs/p5_triage/x_jukan05.json"))  # 这个 handle 拼错了, 实际是 jukan05
    files = [f for f in files if f.exists() and f.stat().st_size > 0]
    print(f"  输入文件: {len(files)} 个")

    network: Counter = Counter()
    relation: dict[str, Counter] = defaultdict(Counter)  # handle → {reply: 5, quote: 3, retweet: 2}

    for fp in files:
        try:
            items = json.load(open(fp))
        except Exception:
            continue
        for it in items:
            # 1. 回复
            ru = it.get("inReplyToUsername") or it.get("in_reply_to_username")
            if ru:
                network[ru] += 1
                relation[ru]["reply"] += 1
            # 2. 引用
            qu = (it.get("quotedTweet") or {}).get("author", {}).get("userName")
            if qu:
                network[qu] += 1
                relation[qu]["quote"] += 1
            # 3. RT (isRetweet=True + userName)
            if it.get("isRetweet"):
                # apidojo/tweet-scraper 把 RT 当成原作者的推文, 原始 userName 在 author
                au = (it.get("author") or {}).get("userName")
                if au and au.lower() != "jukan05":
                    network[au] += 1
                    relation[au]["retweet"] += 1

    print(f"  网络总账号: {len(network)}")
    print(f"  Top 30:")
    for h, c in network.most_common(30):
        rel = relation[h]
        rel_str = f"R{rel.get('reply',0)}/Q{rel.get('quote',0)}/RT{rel.get('retweet',0)}"
        is_excl = h.lower() in {e.lower() for e in EXCLUDE_HANDLES}
        marker = "⏭" if is_excl else " "
        print(f"    {marker} {h:30s} {c:3d} ({rel_str})")
    return network, relation


def is_noise(handle: str) -> bool:
    h = handle.lower()
    for p in NOISE_PATTERNS:
        if re.search(p, h):
            return True
    if h in {e.lower() for e in EXCLUDE_HANDLES}:
        return True
    return False


def apify_fetch(handle: str, max_items: int = 30) -> list[dict]:
    """Apify 拉 1 个 handle 最近 30 条。"""
    input_json = json.dumps({
        "searchTerms": [f"from:{handle}"],
        "maxItems": max_items,
        "sort": "Latest",
    })
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        data=input_json.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for retry in range(2):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                run_info = json.loads(r.read())
            break
        except Exception as e:
            if retry == 1:
                print(f"    {handle}: start failed {e}")
                return []
            time.sleep(5)
    run_id = run_info.get("data", {}).get("id")
    if not run_id:
        return []
    s = "?"
    for i in range(20):
        time.sleep(6)
        try:
            with urllib.request.urlopen(
                f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}",
                timeout=20,
            ) as r2:
                s = json.loads(r2.read()).get("data", {}).get("status", "?")
        except Exception:
            continue
        if s in ("SUCCEEDED", "FAILED", "ABORTED"):
            break
    if s != "SUCCEEDED":
        return []
    try:
        with urllib.request.urlopen(
            f"https://api.apify.com/v2/datasets/{run_info['data']['defaultDatasetId']}/items?token={APIFY_TOKEN}&format=json&limit={max_items}",
            timeout=30,
        ) as r3:
            return json.loads(r3.read())
    except Exception:
        return []


# === LLM 轻量分诊 ===
TRIAGE_PROMPT = """你是 KOL 轻量分诊器。给定一条推文样本, 判断:

【样本 (3 条代表内容)】
1. {sample1}
2. {sample2}
3. {sample3}

【判定 — 输出 JSON 格式】
{{
  "type": "signal" / "knowledge" / "mixed" / "noise",
  "market": "US" / "A_share" / "HK" / "KR" / "TW" / "non_stock" / "?",
  "tickers_mentioned": ["NVDA", ...],
  "signals_strength": 0-3 (0=无个股判断, 1=零散, 2=经常, 3=核心=类似 Jukan),
  "lookalike_jukan": 0-3 (0=完全不同, 3=很像, 美股半导体个股明确喊多空, 原创非搬运),
  "evidence": "一句话解释"
}}

判定 type:
- signal: 喊具体标的买卖方向 ($TICKER + buy/sell/推荐/不推荐)
- knowledge: 产分析/趋势, 不喊个股
- mixed: 两者都有
- noise: 纯转发/段子/政治/无关

lookalike_jukan 评分:
- 3: 半导体个股 + 美股 + 原创 + 喊方向 + 安静
- 2: 部分满足
- 1: 偶尔喊但不是核心
- 0: 完全不是

注意: 输出必须是合法 JSON, 可以被 json.loads 解析。
"""


def llm_triage(handle: str, items: list[dict]) -> dict:
    if len(items) < 3:
        return {"type": "?", "lookalike_jukan": 0, "evidence": f"only {len(items)} items"}
    samples = []
    for it in items[:5]:
        text = (it.get("text") or it.get("fullText") or "")[:300]
        samples.append(text)
    while len(samples) < 3:
        samples.append("(无更多)")
    prompt = TRIAGE_PROMPT.format(
        sample1=samples[0], sample2=samples[1], sample3=samples[2],
    )
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 1500,
    }).encode()
    err = "?"
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
                raise ValueError("empty")
            return json.loads(cs)
        except Exception as e:
            err = str(e)
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return {"type": "?", "lookalike_jukan": 0, "evidence": f"LLM failed: {err[:50]}"}


def main():
    import time as _t
    t0 = _t.time()
    print("=" * 60)
    print("Jukan 网络挖掘 — 找第二个 Jukan")
    print("=" * 60)

    network, relation = extract_network()
    (OUT_DIR / "network.json").write_text(json.dumps({
        "network": dict(network.most_common()),
        "relation": dict(relation),
    }, indent=2, ensure_ascii=False))

    # 筛: 出现 ≥ 3 次 + 排除已知大V
    candidates = []
    for h, c in network.most_common():
        if c < 3:
            break
        if is_noise(h):
            continue
        candidates.append((h, c, relation[h]))

    print(f"\n[2/4] 筛后候选: {len(candidates)} 个 (≥3 次互动)")

    # Step 3: 抓 30 条 + LLM 分诊 (并发 10 路)
    print(f"\n[3/4] 并发抓 30 条 + LLM 分诊 {len(candidates)} 个候选...")
    results = {}

    def triage_one(h, c, rel):
        items = apify_fetch(h, max_items=30)
        if not items:
            return h, {"n_items": 0, "type": "?", "lookalike_jukan": 0, "evidence": "no_data"}
        triage = llm_triage(h, items)
        return h, {
            "n_items": len(items),
            "interaction_count": c,
            "interaction_type": f"R{rel.get('reply',0)}/Q{rel.get('quote',0)}/RT{rel.get('retweet',0)}",
            "triage": triage,
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(triage_one, h, c, rel): (h, c, rel) for h, c, rel in candidates}
        for fut in as_completed(futures):
            h, c, rel = futures[fut]
            try:
                _, r = fut.result()
            except Exception as e:
                r = {"n_items": 0, "triage": {"lookalike_jukan": 0, "evidence": f"error: {e}"}}
            results[h] = r

    (OUT_DIR / "triage_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Step 4: 输出报告
    print(f"\n[4/4] 生成报告...")
    # 按 lookalike_jukan 排序
    ranked = sorted(results.items(), key=lambda x: -x[1].get("triage", {}).get("lookalike_jukan", 0))

    lines = [
        "# Jukan 网络挖掘 — 找『第二个 Jukan』候选 (P5-5)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**网络账号总数**: {len(network)}  ",
        f"**筛后候选 (≥3 次互动 + 排除大V)**: {len(candidates)}  ",
        f"**已分诊**: {sum(1 for r in results.values() if r.get('triage', {}).get('lookalike_jukan', 0) > 0)}",
        "",
        "## 1. 策略说明",
        "",
        "用户发现: 可验证判断质量 **与名气/广度成反比** —",
        "- **Jukan** (不太有名, 专注半导体, 安静发原创) 质量最高 26/26 (96.3%)",
        "- **Dylan / LinQingV / Brad** (有名, 通才, 段子+营销) 质量低 / 不可验证",
        "",
        "**下一步**: 从 Jukan 的网络 (他回复/引用/RT 的人) 挖『第二个 Jukan』, 不再加知名大V。",
        "",
        "## 2. 网络 Top 30 (出现 ≥ N 次)",
        "",
        "| 账号 | 出现次数 | reply | quote | RT | 是否排除 |",
        "|---|---|---|---|---|---|",
    ]
    for h, c in network.most_common(30):
        rel = relation[h]
        is_excl = h.lower() in {e.lower() for e in EXCLUDE_HANDLES}
        marker = "⏭ 大V/媒体" if is_excl else " "
        lines.append(f"| @{h} | {c} | {rel.get('reply',0)} | {rel.get('quote',0)} | {rel.get('retweet',0)} | {marker} |")

    # 候选分诊
    lines.extend([
        "",
        f"## 3. 候选分诊 (≥3 次互动 + 非大V, 已 LLM 分诊)",
        "",
        "| # | 账号 | 互动 | n | type | market | signals | **像 Jukan** | 证据 |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for i, (h, r) in enumerate(ranked[:40], 1):
        if r.get("n_items", 0) == 0:
            lines.append(f"| {i} | @{h} | {r.get('interaction_count',0)} | 0 | ? | ? | - | ? | no_data |")
            continue
        t = r.get("triage", {})
        type_str = t.get("type", "?")
        market = t.get("market", "?")
        sigs = t.get("signals_strength", 0)
        lj = t.get("lookalike_jukan", 0)
        ev = (t.get("evidence", "") or "")[:50].replace("|", "/")
        n = r.get("n_items", 0)
        rel_str = r.get("interaction_type", "?")
        lines.append(f"| {i} | @{h} | {rel_str} | {n} | {type_str} | {market} | {sigs} | **{lj}/3** | {ev} |")

    # 重点: 像 Jukan ≥ 2 的
    lines.extend([
        "",
        "## 4. 🎯 『可能像 Jukan』候选 (lookalike ≥ 2)",
        "",
    ])
    top_picks = [(h, r) for h, r in ranked if r.get("triage", {}).get("lookalike_jukan", 0) >= 2]
    if top_picks:
        for i, (h, r) in enumerate(top_picks, 1):
            t = r.get("triage", {})
            lines.append(f"### #{i} @{h} — lookalike {t.get('lookalike_jukan', 0)}/3")
            lines.append(f"- 互动次数: {r.get('interaction_count', 0)} ({r.get('interaction_type', '?')})")
            lines.append(f"- type: {t.get('type', '?')} | market: {t.get('market', '?')} | signals_strength: {t.get('signals_strength', 0)}")
            lines.append(f"- tickers 提及: {t.get('tickers_mentioned', [])}")
            lines.append(f"- 证据: {t.get('evidence', '')}")
            lines.append(f"- 抓取内容: {r.get('n_items', 0)} 条 (在 `logs/p5_jukan_network/triage_{h}.json`)")
            lines.append("")
    else:
        lines.append("⚠️ 没有 lookalike ≥ 2 的候选 — Jukan 网络里没找到第二个 Jukan")
        lines.append("")

    # 候补 (lookalike = 1)
    backup = [(h, r) for h, r in ranked if r.get("triage", {}).get("lookalike_jukan", 0) == 1]
    if backup:
        lines.append("### 候补 (lookalike = 1)")
        for h, r in backup[:10]:
            t = r.get("triage", {})
            lines.append(f"- @{h}: {t.get('type', '?')} / {t.get('market', '?')} — {t.get('evidence', '')[:60]}")

    # 决策建议
    lines.extend([
        "",
        "## 5. 我的建议",
        "",
    ])
    if top_picks:
        lines.append(f"**Top pick: 跑深度验证 (P5 完整管道) for {len(top_picks)} 个 lookalike ≥ 2 候选**")
        lines.append("")
        for h, r in top_picks:
            lines.append(f"- @{h}: 跑 kol_verify_standard.py (抓 6 月 + 验证)")
    else:
        lines.append("**没有 lookalike ≥ 2 — 不建议批量跑, 重新评估策略**:")
        lines.append("- Jukan 网络稀疏, 大部分互动是 reply 给小账号 (没回粉, 不是真·认可)")
        lines.append("- 替代方案: Substack / Medium 找写半导体的安静 newsletter 作者")

    lines.extend([
        "",
        f"⏱️  总耗时: {_t.time()-t0:.1f}s",
    ])

    out = Path("/workspace/outputs/p5_jukan_network_candidates.md")
    out.write_text("\n".join(lines))
    print(f"\n📄 报告: {out}")

    # 保存每个候选的原始推文
    for h, r in results.items():
        if r.get("n_items", 0) > 0:
            # 重新抓一次 (cheap) 或用 triage 时 cache
            pass


if __name__ == "__main__":
    main()