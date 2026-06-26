"""Jukan following 1357 个 → 过滤半导体相关 → 合并互动网络 → 体检"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import time
import os
import urllib.request

OUT_DIR = Path("/workspace/logs/p5_jukan_following")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"

# 已知互动网络 (from p5_jukan_network)
INTERACTION_NETWORK = json.load(open("/workspace/logs/p5_jukan_network/network.json"))
INTERACTION = INTERACTION_NETWORK["network"]  # {handle: count}
INTERACTION_REL = INTERACTION_NETWORK["relation"]  # {handle: {reply, quote, retweet}}

# 已知排除大V/媒体
EXCLUDE = {
    "Reuters", "Bloomberg", "WSJ", "FT", "FinancialTimes", "CNBC",
    "nytimes", "TechCrunch", "TheInformation", "TheVerge", "ReutersBiz", "ReutersTech",
    "BbergTV", "GoldmanSachs", "MorganStanley", "jpmorgan", "BlackRock",
    "wallstreetcn", "cls_telecom", "eastmoney", "X", "Twitter",
    "dylan522p", "StockMarketNerd", "GavinSBaker", "DougOLoughlin", "davidcitrini",
    "LeopoldAschenbrenner", "LinQingV", "qinbafrank", "SemiAnalysis_", "PatrickMoorhead",
    "jukan05",
    # 已知试过且结论 pass 的
    "deepvan",
}

# 半导体关键词 (description 匹配) — 用用户原规则, 宽筛
SEMI_KEYWORDS = [
    "semiconductor", "semis", "chip", "chips", "Chip", "Chips",
    "silicon", "silicon technologist",
    "HBM", "DRAM", "NAND", "memory",
    "CoWoS", "advanced packaging", "foundry", "fab", "wafer",
    "AI", "GPU", "ASIC", "TPU", "NPU", "FPGA",
    "NVDA", "nvidia", "AMD", "Intel", "TSMC", "Samsung", "Hynix", "SK Hynix",
    "Micron", "Marvell", "MRVL", "AVGO", "Broadcom",
    "ASML", "Applied Materials", "AMAT", "Lam Research", "LRCX",
    "Tokyo Electron", "TEL", "Advantest",
    "SoC", "EDA", "Synopsys", "SNPS", "Cadence", "CDNS",
    "SNDK", "Sandisk", "Western Digital", "WDC", "Seagate",
    "Kioxia", "Macronix", "GigaDevice",
    "光刻", "晶圆", "封装", "半导体",
    "NVIDIA", "data center", "datacenter", "AI infrastructure",
    "ML", "machine learning", "deep learning",
    "TPU", "CUDA",
    "TSMC", "三星", "海力士", "美光", "铠侠", "兆易",
    "GPU", "HBM3", "HBM4", "LPCAMM",
    "FOPLP", "CoWoS-S", "CoWoS-L",
    "inference", "training",
]


def is_semi(desc: str) -> tuple[bool, list[str]]:
    """判断 description 是否含半导体关键词 (宽筛, 按用户原规则)."""
    if not desc:
        return False, []
    matched = [k for k in SEMI_KEYWORDS if k in desc]
    return (len(matched) > 0, matched)


def main():
    import time as _t
    t0 = _t.time()
    print("=" * 60)
    print("Jukan Following 完整分析 (1357 个)")
    print("=" * 60)

    # Load
    following = json.load(open(OUT_DIR / "following.json"))
    print(f"following 总数: {len(following)}")

    # 筛: 有 description 且含半导体关键词 + 排除大V
    semi_users = []
    no_desc = 0
    for u in following:
        sn = u.get("username") or u.get("userName") or u.get("screen_name")
        if not sn:
            continue
        if sn.lower() in {e.lower() for e in EXCLUDE}:
            continue
        desc = u.get("description", "")
        if not desc:
            no_desc += 1
            continue
        hit, kw = is_semi(desc)
        if hit:
            semi_users.append({
                "handle": sn,
                "description": desc[:120],
                "matched_keywords": kw,
                "followers_count": u.get("followersCount", 0),
                "following_count": u.get("followingCount", 0),
                "user_id": u.get("userId"),
            })

    print(f"\n半导体相关 (description 命中关键词): {len(semi_users)}")
    print(f"  无 description: {no_desc}")

    # 统计 follower 数分布
    fc = Counter()
    for u in semi_users:
        f = u["followers_count"]
        if f < 1000:
            fc["<1K"] += 1
        elif f < 5000:
            fc["1K-5K"] += 1
        elif f < 10000:
            fc["5K-10K"] += 1
        elif f < 50000:
            fc["10K-50K"] += 1
        elif f < 100000:
            fc["50K-100K"] += 1
        else:
            fc[">100K"] += 1
    print(f"  follower 数分布: {dict(fc)}")

    # 合并互动网络 + 去重
    # 互动数 ≥ 1 的 = 互动过
    interaction_handles = {h for h, c in INTERACTION.items() if c >= 1}
    print(f"\n互动网络账号 (含 jukan05): {len(INTERACTION)}")

    # 给每个 semi_user 标 interaction_count
    for u in semi_users:
        ic = INTERACTION.get(u["handle"], 0)
        u["interaction_count"] = ic
        u["in_interaction_network"] = ic >= 1

    # 分组: (有互动 + 半导) vs (无互动 + 半导) — 后者是 Jukan 关注但没对话的"高段位"
    has_interaction = [u for u in semi_users if u["in_interaction_network"]]
    no_interaction = [u for u in semi_users if not u["in_interaction_network"]]
    print(f"\n  有互动 + 半导体: {len(has_interaction)} (已知: zephyr_z9, TShirtnJeans2, etc.)")
    print(f"  无互动 + 半导体: {len(no_interaction)} (Jukan 关注但没对话 = 候选池)")

    # 筛"无互动"中的中等粉丝 (1K - 100K) — 不是 noise, 不是大V
    mid_no_int = [u for u in no_interaction if 1000 <= u["followers_count"] <= 100000]
    print(f"  无互动 + 中等粉丝 (1K-100K): {len(mid_no_int)} ← 真正候选池")

    # 排序 (按 followers 升序, 关注中等粉丝的安静 KOL)
    mid_no_int.sort(key=lambda u: u["followers_count"])

    print(f"\n--- 中等粉丝候选 Top 30 (Jukan 关注但未互动) ---")
    for u in mid_no_int[:30]:
        kw = ", ".join(u["matched_keywords"][:5])
        print(f"  @{u['handle']:30s} | {u['followers_count']:>6} followers | {kw[:50]}")

    # 保存完整候选池
    (OUT_DIR / "candidates_no_interaction.json").write_text(json.dumps({
        "mid_no_int": mid_no_int,
        "has_interaction": has_interaction,
        "all_semi": semi_users,
    }, indent=2, ensure_ascii=False))

    # Step 2: 抓 Top 30 候选的 30 条推文 (并发)
    print(f"\n[2/3] 抓 Top 30 候选的最近 30 条 (并发)...")
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def apify_fetch(handle, max_items=30):
        payload = json.dumps({
            "searchTerms": [f"from:{handle}"],
            "maxItems": max_items,
            "sort": "Latest",
        })
        req = urllib.request.Request(
            f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
            data=payload.encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        for retry in range(2):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    run = json.loads(r.read())
                break
            except Exception:
                time.sleep(3)
        rid = run.get("data", {}).get("id")
        if not rid:
            return []
        s = "?"
        for i in range(15):
            time.sleep(6)
            try:
                with urllib.request.urlopen(
                    f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{rid}?token={APIFY_TOKEN}",
                    timeout=15,
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
                f"https://api.apify.com/v2/datasets/{run['data']['defaultDatasetId']}/items?token={APIFY_TOKEN}&format=json&limit={max_items}",
                timeout=30,
            ) as r3:
                return json.loads(r3.read())
        except Exception:
            return []

    candidates_top = mid_no_int[:30]
    results = {}

    # 分批 4 个并发
    for i in range(0, len(candidates_top), 4):
        batch = candidates_top[i:i+4]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(apify_fetch, u["handle"]): u["handle"] for u in batch}
            for fut in as_completed(futures):
                h = futures[fut]
                try:
                    items = fut.result()
                except Exception:
                    items = []
                results[h] = {
                    "n_items": len(items),
                    "items": items,
                    "user_info": next(u for u in batch if u["handle"] == h),
                }
                print(f"  {h}: {len(items)} items")

    # Step 3: LLM 分诊 (并发)
    print(f"\n[3/3] LLM 分诊 {len(results)} 个候选 (并发 8 路)...")

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

    def triage_one(h):
        r = results[h]
        items = r["items"]
        if not items:
            return h, {"type": "?", "lookalike_jukan": 0, "evidence": "no_data"}
        samples = []
        for it in items[:5]:
            text = (it.get("text") or it.get("fullText") or "")[:300]
            samples.append(text)
        while len(samples) < 3:
            samples.append("(无更多)")
        prompt = TRIAGE_PROMPT.format(sample1=samples[0], sample2=samples[1], sample3=samples[2])
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
                return h, json.loads(cs)
            except Exception as e:
                err = str(e)
                if retry < 2:
                    time.sleep(2 * (retry + 1))
        return h, {"type": "?", "lookalike_jukan": 0, "evidence": f"err: {err[:50]}"}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(triage_one, h): h for h in results}
        for fut in as_completed(futures):
            h = futures[fut]
            try:
                _, t = fut.result()
            except Exception as e:
                t = {"type": "?", "lookalike_jukan": 0, "evidence": f"err: {e}"}
            results[h]["triage"] = t
            print(f"  {h}: lookalike={t.get('lookalike_jukan',0)} type={t.get('type','?')}")

    # 保存
    (OUT_DIR / "triage_results.json").write_text(json.dumps({
        h: {**r, "items": None}  # 不存 items 太大
        for h, r in results.items()
    }, indent=2, ensure_ascii=False))
    # items 单独存
    for h, r in results.items():
        if r.get("items"):
            json.dump(r["items"], open(OUT_DIR / f"items_{h}.json", "w"), indent=2, ensure_ascii=False)

    # Step 4: 报告
    print(f"\n生成报告...")
    ranked = sorted(
        [(h, r) for h, r in results.items()],
        key=lambda x: -x[1].get("triage", {}).get("lookalike_jukan", 0),
    )

    lines = [
        "# Jukan Following 完整挖掘 (P5-6)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**following 总数**: {len(following)}  ",
        f"**半导体关键词命中**: {len(semi_users)} (含描述)  ",
        f"**有互动 + 半导 (已知)**: {len(has_interaction)}  ",
        f"**无互动 + 半导 (新候选)**: {len(no_interaction)}  ",
        f"**中等粉丝 (1K-100K) 新候选**: {len(mid_no_int)}  ",
        f"**已分诊 Top**: {len(ranked)}",
        "",
        "## 1. 思路",
        "",
        "互动网络不全 (Jukan 推文 2025-04 ~ 10 月残缺, 提取的回复/RT 自然不全).",
        "Following 列表是**独立完整数据**: 一次抓全, 不依赖抓多少条推文.",
        "",
        "**重点找**: `有 following + 半导体相关 + 无互动` = **Jukan 默默关注但没公开对话的高段位**",
        "",
        "## 2. Following 统计",
        "",
        "| 维度 | 数量 |",
        "|---|---|",
        f"| 总 following | {len(following)} |",
        f"| 有 description | {len(following) - no_desc} |",
        f"| 无 description (noise 风险) | {no_desc} |",
        f"| 半导体关键词命中 | {len(semi_users)} |",
        "",
        f"**follower 数分布** (半导体子集):",
        "",
        "| 区间 | 数量 |",
        "|---|---|",
    ]
    for k in ["<1K", "1K-5K", "5K-10K", "10K-50K", "50K-100K", ">100K"]:
        lines.append(f"| {k} | {fc.get(k, 0)} |")

    # 有互动 (已知)
    lines.extend([
        "",
        "## 3. 已知: 有互动 + 半导体 (已分诊 in P5-5)",
        "",
        "| 账号 | followers | 互动 | lookalike |",
        "|---|---|---|---|",
    ])
    for h, ic in sorted(INTERACTION.items(), key=lambda x: -x[1])[:20]:
        if h in {e.lower() for e in EXCLUDE} or h == "jukan05":
            continue
        u = next((x for x in semi_users if x["handle"] == h), None)
        if not u:
            continue
        # 找 triage
        lj = "—"
        for hh, rr in ranked:
            if hh == h:
                lj = rr.get("triage", {}).get("lookalike_jukan", 0)
                break
        lines.append(f"| @{h} | {u['followers_count']:,} | {ic} | {lj} |")

    # 中等粉丝无互动 (新候选)
    lines.extend([
        "",
        "## 4. 🎯 新候选: 中等粉丝 + 半导体 + 无互动 (Top 30)",
        "",
        "**这一节是关键 — Jukan 关注了但没公开对话的'高段位'候选**",
        "",
        "| # | 账号 | followers | 关键词 | **像 Jukan** | 证据 |",
        "|---|---|---|---|---|---|",
    ])
    for i, (h, r) in enumerate(ranked, 1):
        u = r["user_info"]
        t = r.get("triage", {})
        lj = t.get("lookalike_jukan", 0)
        kw = ", ".join(u["matched_keywords"][:4])
        ev = (t.get("evidence", "") or "")[:60].replace("|", "/")
        lines.append(f"| {i} | @{h} | {u['followers_count']:,} | {kw[:40]} | **{lj}/3** | {ev} |")

    # 像 Jukan ≥ 2 重点
    top_picks = [(h, r) for h, r in ranked if r.get("triage", {}).get("lookalike_jukan", 0) >= 2]
    lines.extend([
        "",
        "## 5. 像 Jukan ≥ 2 候选 — 新发现",
        "",
    ])
    if top_picks:
        for h, r in top_picks:
            u = r["user_info"]
            t = r.get("triage", {})
            lines.extend([
                f"### @{h} — lookalike {t.get('lookalike_jukan', 0)}/3",
                f"- **followers**: {u['followers_count']:,} (中等, 非大V)",
                f"- **描述**: {u['description']}",
                f"- **type**: {t.get('type', '?')} | market: {t.get('market', '?')}",
                f"- **signals**: {t.get('signals_strength', 0)}/3 | tickers: {t.get('tickers_mentioned', [])}",
                f"- **证据**: {t.get('evidence', '')}",
                f"- **Jukan 没跟他公开对话** (但默默关注)",
                "",
                "**代表内容**:",
            ])
            for it in (r.get("items") or [])[:5]:
                text = (it.get("text") or "")[:200]
                lines.append(f"> [{it.get('createdAt','?')[:10]}] {text}")
            lines.append("")
    else:
        lines.append("⚠️ 没有 lookalike ≥ 2 的新候选\n")

    # 合并互动 + following 的最终 top 候选
    lines.extend([
        "",
        "## 6. 🏆 最终合并候选池 (互动 + following)",
        "",
        "| 账号 | 来源 | followers | 互动 | lookalike |",
        "|---|---|---|---|---|",
    ])
    # 合并
    all_final = []
    # 已知互动 (lookalike 已经在 triage_results_v2.json)
    for h, ic in INTERACTION.items():
        if h == "jukan05" or h.lower() in {e.lower() for e in EXCLUDE}:
            continue
        lj = 0
        if h in {hh for hh, _ in ranked}:
            r = next(rr for hh, rr in ranked if hh == h)
            lj = r.get("triage", {}).get("lookalike_jukan", 0)
        elif h in {"zephyr_z9", "TShirtnJeans2", "rwang07", "Semicon_player"}:
            # 从 v2 读
            v2 = json.load(open("/workspace/logs/p5_jukan_network/triage_results_v2.json"))
            if h in v2:
                lj = v2[h]["triage"].get("lookalike_jukan", 0)
        # 手动修正 zephyr_z9
        if h == "zephyr_z9":
            lj = 3
        if h == "TShirtnJeans2":
            lj = 2
        # 找 user info
        u = next((x for x in semi_users if x["handle"] == h), None)
        if not u:
            # 不在 semi_users (没 description 或没关键词命中)
            # 用 INTERACTION 排序
            continue
        all_final.append({
            "handle": h,
            "source": "interaction" if ic >= 1 else "following",
            "followers": u["followers_count"],
            "interaction": ic,
            "lookalike": lj,
        })

    # 加新 (following 但没互动, lookalike ≥ 1)
    for h, r in ranked:
        if h in {a["handle"] for a in all_final}:
            continue
        t = r.get("triage", {})
        if t.get("lookalike_jukan", 0) >= 1:
            u = r["user_info"]
            all_final.append({
                "handle": h,
                "source": "following",
                "followers": u["followers_count"],
                "interaction": 0,
                "lookalike": t.get("lookalike_jukan", 0),
            })

    all_final.sort(key=lambda x: -x["lookalike"])
    for a in all_final[:30]:
        lines.append(f"| @{a['handle']} | {a['source']} | {a['followers']:,} | {a['interaction']} | **{a['lookalike']}/3** |")

    lines.append("")
    lines.append(f"⏱️  总耗时: {_t.time()-t0:.1f}s")

    out = Path("/workspace/outputs/p5_jukan_following_candidates.md")
    out.write_text("\n".join(lines))
    print(f"📄 {out}")


if __name__ == "__main__":
    main()