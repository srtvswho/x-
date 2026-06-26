"""LinQingV 深度分析 — 抓 3-6 月内容 + 类型判断 + 提取可证伪预测

策略:
1. Apify 拉 @LinQingV 最近 200 条 (latest 排序)
2. 如果 < 100, 分段补 2025-11 ~ 2026-06
3. 解析 ticker / 板块 / 判断类型
4. LLM 提取"可证伪、有方向、有时间"判断清单
5. 输出类型判断 + 判断清单
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from collections import Counter, defaultdict

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
ACTOR_ID = "61RPP7dywgiy0JPD0"
OUT_DIR = Path("/workspace/logs/p5_linqingv")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 并发配置
MAX_WORKERS_LLM = 10  # LLM 批井发 (DeepSeek 5-10 路不需手走 RPM 限流)
MAX_WORKERS_APIFY = 3   # Apify 3 段同时跑 (1 actor run = 1 并发)


def apify_fetch_period(handle: str, since: str, until: str, max_items: int = 200) -> list[dict]:
    """Apify 拉 1 段时间的推文。"""
    print(f"  Apify: {handle} {since}..{until} (max {max_items})")
    input_json = json.dumps({
        "searchTerms": [f"from:{handle} since:{since} until:{until}"],
        "maxItems": max_items,
        "sort": "Latest",
    })
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}",
        data=input_json.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for retry in range(3):  # 重试 3 次
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                run_info = json.loads(r.read())
            break
        except Exception as e:
            print(f"    ! start attempt {retry+1} failed: {e}")
            if retry < 2:
                time.sleep(5 * (retry + 1))
            else:
                return []
    run_id = run_info.get("data", {}).get("id")
    if not run_id:
        print(f"    ! no run_id: {run_info}")
        return []
    print(f"    run_id: {run_id}")
    # poll
    s = "?"
    for i in range(30):
        time.sleep(8)
        try:
            with urllib.request.urlopen(
                f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}",
                timeout=30,
            ) as r2:
                s = json.loads(r2.read()).get("data", {}).get("status", "?")
        except Exception:
            continue
        if i % 4 == 0:
            print(f"    [poll {i}] {s}")
        if s in ("SUCCEEDED", "FAILED", "ABORTED"):
            break
    if s != "SUCCEEDED":
        print(f"    ! run {s}")
        return []
    try:
        with urllib.request.urlopen(
            f"https://api.apify.com/v2/datasets/{run_info['data']['defaultDatasetId']}/items?token={APIFY_TOKEN}&format=json&limit={max_items}",
            timeout=60,
        ) as r3:
            items = json.loads(r3.read())
        print(f"    → {len(items)} items")
        return items
    except Exception as e:
        print(f"    ! fetch failed: {e}")
        return []


def fetch_linqingv_deep() -> list[dict]:
    """主入口: 抓 LinQingV 全部近期内容, 3 段并发跑。"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    periods = [
        ("2026-04-01", "2026-06-23"),
        ("2025-12-01", "2026-03-31"),
        ("2025-08-01", "2025-11-30"),
    ]
    print(f"  并发跑 {len(periods)} 段 (max_workers={MAX_WORKERS_APIFY})...")
    all_items = []
    seen_ids = set()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_APIFY) as pool:
        futures = {pool.submit(apify_fetch_period, "LinQingV", s, u, 300): (s, u) for s, u in periods}
        for fut in as_completed(futures):
            s, u = futures[fut]
            try:
                items = fut.result()
            except Exception as e:
                print(f"  period {s}..{u} failed: {e}")
                continue
            new = 0
            for it in items:
                tid = it.get("id") or it.get("tweetId") or ""
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_items.append(it)
                    new += 1
            print(f"  period {s}..{u}: {new} new (total {len(all_items)})")
    # 按时间排序 (新到旧)
    def get_date(it):
        return it.get("createdAt") or it.get("created_at") or ""
    all_items.sort(key=get_date, reverse=True)
    return all_items


# === ticker / 板块提取 ===
US_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
HK_CODE_RE = re.compile(r"\b([0-9]{4,5})\.HK\b|\((?:0?\d{4,5})\)")
A_SHARE_RE = re.compile(r"\b([0-9]{6})\.(?:SH|SZ|SS)\b")
A_NAME_RE = re.compile(r"[\u4e00-\u9fff]{2,4}(?:股份|集团|科技|银行|证券|能源|医药|汽车|电子|通信|半导体|光电|新材)")

# 板块/主题关键词
SECTOR_KEYWORDS = {
    "存储/DRAM/HBM": ["DRAM", "HBM", "NAND", "存储", "闪存", "内存", "SSD", "美光", "海力士", "三星电子"],
    "光通信/光模块": ["光通信", "光模块", "光模块", "CPO", "LPO", "800G", "1.6T", "AOC"],
    "AI/算力/GPU": ["AI", "GPU", "TPU", "ASIC", "NPU", "算力", "HCCL", "GLM", "训练", "推理", "大模型", "LLM", "GPU", "CXL"],
    "半导体设备": ["光刻机", "ASML", "AMAT", "LRCX", "KLAC", "泛林", "科磊", "刻蚀", "沉积", "薄膜"],
    "A股大盘/指数": ["A股", "上证", "深证", "创业板", "科创板", "北证", "沪深300", "中证500", "中证1000"],
    "港股/中概": ["港股", "恒生", "恒生科技", "H股", "中概", "回港", "双重主要上市"],
    "美股/美债/汇率": ["美股", "纳指", "标普", "SPY", "QQQ", "美债", "TGA", "QE", "QT", "美元", "DXY"],
    "加密/数字资产": ["BTC", "ETH", "比特币", "以太坊", "稳定币", "USDT", "USDC", "Web3"],
    "消费/电商": ["消费", "电商", "拼多多", "阿里", "京东", "美团", "抖音"],
    "新能源/车": ["新能源", "电池", "宁德", "比亚迪", "锂电", "光伏", "储能", "电动车"],
    "机器人/具身智能": ["机器人", "具身", "宇树", "智元", "Figure", "Optimus"],
}

# 方向词 (多/空/防御/风险)
DIRECTION_KEYWORDS = {
    "long": ["看多", "看好", "加仓", "建仓", "买入", "买", "推荐", "强势", "上行", "突破", "新高", "将启动", "将上涨", "反弹"],
    "short": ["看空", "看跌", "减仓", "清仓", "卖出", "卖", "做空", "不推荐", "调整", "下行", "下跌", "风险", "回撤", "将跌", "走熊"],
    "neutral": ["震荡", "横盘", "中性", "防御", "谨慎", "观望", "等待", "分化"],
}


def extract_features(text: str) -> dict:
    """提取 1 条推文的所有 features。"""
    return {
        "us_tickers": list(set(US_TICKER_RE.findall(text))),
        "hk_codes": list(set(HK_CODE_RE.findall(text))),
        "a_share_codes": list(set(A_SHARE_RE.findall(text))),
        "sectors_hit": [s for s, kws in SECTOR_KEYWORDS.items() if any(kw in text for kw in kws)],
        "directions": [d for d, kws in DIRECTION_KEYWORDS.items() if any(kw in text for kw in kws)],
    }


# === LLM 提取可证伪判断 ===
EXTRACT_PROMPT = """你是 KOL 观点提取器。给定一批推文, 提取"可证伪的、有方向的、有时间窗的"判断。

【内容】{content}

【判定规则 — 必须全部满足才是有效判断】
1. **可证伪**: 不是"市场有风险""要关注 XX"这种模糊观点; 必须能事后用数据/价格/指数验证
2. **有方向**: 多/空/防御/轮动/转折 — 至少有一个明确方向
3. **有时间窗**: "3 个月内""2026 年""本季度""下一轮""明天" — 有时间锚点
4. **有具体标的或板块或指数**: 至少指向一个 (个股 / 板块 / 指数 / 标的代码), 不能是"市场整体"

【输出格式】每条判断一行 JSON:
{{
  "date": "YYYY-MM-DD",
  "type": "个股选股" / "板块轮动" / "宏观择时" / "产业卡点",
  "target": "具体标的 (个股代码 / 板块 / 指数)",
  "direction": "看多" / "看空" / "防御" / "轮动到 X" / "风险偏好上行/下行",
  "timeframe": "3 个月内" / "2026 H1" / "下一轮" / "本周" / "本季度",
  "excerpt": "原文 (≤ 50 字)",
  "consensus": "共识" / "非共识" / "反共识"
}}

如果一条推文有多个判断, 拆成多条 JSON 输出。
如果一条推文是 commentary / news sharing / 无方向观点, 跳过。
如果 30 条里一条有效判断都没有, 输出空数组 []。

【输出 JSON】{{"judgments": [...]}}
"""


def llm_extract_judgments(content_summary: str) -> list[dict]:
    """LLM 提取可证伪判断。"""
    prompt = EXTRACT_PROMPT.format(content=content_summary[:8000])
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 3000,
    }).encode()
    for retry in range(3):
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read())
            content_str = resp["choices"][0]["message"]["content"]
            if not content_str:
                raise ValueError("empty content")
            parsed = json.loads(content_str)
            return parsed.get("judgments", [])
        except Exception as e:
            print(f"    LLM attempt {retry+1} error: {e}")
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return []


# === 主流程 ===
def main():
    print("=" * 60)
    print("LinQingV 深度分析 — 3 步走 (并发版)")
    print("=" * 60)
    import time as _t
    t0 = _t.time()

    # 步骤 1: 抓数据
    print("\n[1/3] 抓 LinQingV 长段时间 (3-6 月)...")
    items = fetch_linqingv_deep()
    print(f"  total fetched: {len(items)}")
    out_path = OUT_DIR / "tweets_raw.json"
    out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False))

    # 步骤 2: 类型判断 (标的分布 + 板块分布 + 方向分布)
    print("\n[2/3] 类型判断 — 提取 features...")
    sector_count: Counter = Counter()
    direction_count: Counter = Counter()
    market_count: Counter = Counter()
    us_ticker_count: Counter = Counter()
    hk_code_count: Counter = Counter()
    a_share_count: Counter = Counter()
    date_dist: Counter = Counter()
    reply_count = 0
    retweet_count = 0
    original_count = 0

    for it in items:
        text = it.get("text") or it.get("fullText") or ""
        date = (it.get("createdAt") or "")[:7]  # YYYY-MM
        date_dist[date] += 1
        if it.get("isReply"):
            reply_count += 1
        if it.get("isRetweet"):
            retweet_count += 1
        if not it.get("isReply") and not it.get("isRetweet"):
            original_count += 1
        f = extract_features(text)
        for s in f["sectors_hit"]:
            sector_count[s] += 1
        for d in f["directions"]:
            direction_count[d] += 1
        for t in f["us_tickers"]:
            us_ticker_count[t] += 1
            market_count["US"] += 1
        for c in f["hk_codes"]:
            hk_code_count[c] += 1
            market_count["HK"] += 1
        for c in f["a_share_codes"]:
            a_share_count[c] += 1
            market_count["A_share"] += 1
        # 文字提及
        if "A股" in text or "沪深" in text:
            market_count["A_share_text"] += 1
        if "港股" in text or "恒生" in text:
            market_count["HK_text"] += 1
        if "美股" in text or "纳指" in text or "标普" in text:
            market_count["US_text"] += 1

    n = max(len(items), 1)
    print(f"\n  --- 类型画像 ({len(items)} 条) ---")
    print(f"  时间分布: {dict(date_dist.most_common())}")
    print(f"  原创/回复/转发: {original_count}/{reply_count}/{retweet_count}")
    print(f"\n  板块 Top 10: {sector_count.most_common(10)}")
    print(f"\n  方向分布: {dict(direction_count)}")
    print(f"\n  市场出现: {dict(market_count.most_common(10))}")
    print(f"\n  美股 ticker Top 15: {us_ticker_count.most_common(15)}")
    print(f"\n  港股代码 Top 10: {hk_code_count.most_common(10)}")
    print(f"\n  A 股代码 Top 10: {a_share_count.most_common(10)}")

    # 保存 features
    (OUT_DIR / "features.json").write_text(json.dumps({
        "date_dist": dict(date_dist),
        "original/reply/retweet": f"{original_count}/{reply_count}/{retweet_count}",
        "sector": dict(sector_count),
        "direction": dict(direction_count),
        "market": dict(market_count),
        "us_tickers": dict(us_ticker_count.most_common(30)),
        "hk_codes": dict(hk_code_count.most_common(20)),
        "a_share_codes": dict(a_share_count.most_common(20)),
    }, indent=2, ensure_ascii=False))

    # 步骤 3: LLM 提取判断清单 (分批提取避免超 max_tokens)
    print("\n[3/3] LLM 提取可证伪判断 (分批 15 条/批)...")
    originals = [it for it in items if not it.get("isReply") and not it.get("isRetweet")]
    print(f"  原创推文: {len(originals)}/{len(items)}")

    all_judgments = []
    batch_size = 15

    # 准备所有 batch content
    batches = []
    for i in range(0, len(originals), batch_size):
        batch = originals[i:i+batch_size]
        content_parts = []
        for it in batch:
            date = (it.get("createdAt") or "?")[:10]
            text = (it.get("text") or it.get("fullText") or "")[:300]
            content_parts.append(f"[{date}] {text}")
        batches.append((i // batch_size + 1, "\n".join(content_parts)))

    # 并发跑 LLM (max_workers=10)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"  并发 LLM 提取 {len(batches)} 批 (max_workers={MAX_WORKERS_LLM})...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_LLM) as pool:
        futures = {pool.submit(llm_extract_judgments, content): idx for idx, content in batches}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                judgments = fut.result()
            except Exception as e:
                print(f"    batch {idx} error: {e}")
                judgments = []
            print(f"    batch {idx}: {len(judgments)} 条")
            all_judgments.extend(judgments)
    print(f"  LLM 提取 total: {len(all_judgments)} 条可证伪判断")
    (OUT_DIR / "judgments.json").write_text(json.dumps(all_judgments, indent=2, ensure_ascii=False))
    # 去重
    from collections import OrderedDict
    deduped = []
    seen_keys = set()
    for j in all_judgments:
        key = (j.get("date"), (j.get("excerpt", "") or "")[:40])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(j)
    deduped.sort(key=lambda x: x.get("date", ""))
    print(f"  去重后: {len(deduped)} 条 (原 {len(all_judgments)})")
    (OUT_DIR / "judgments_deduped.json").write_text(json.dumps(deduped, indent=2, ensure_ascii=False))

    # 报告
    report = render_report(items, sector_count, direction_count, market_count,
                          us_ticker_count, hk_code_count, a_share_count, date_dist,
                          deduped, original_count, reply_count, retweet_count)
    out = Path("/workspace/outputs/p5_linqingv_deep.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"\n📄 报告: {out}")
    elapsed = _t.time() - t0
    print(f"\n⏱️  总耗时: {elapsed:.1f}s ({elapsed/60:.1f} min)")


def render_report(items, sectors, directions, markets, us_t, hk_c, a_c, dates,
                 judgments, orig, rep, rt):
    n = max(len(items), 1)
    lines = [
        "# LinQingV 深度分析 (P5-2)",
        "",
        f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M')}  ",
        f"**抓取推文**: {len(items)} 条 (原创 {orig} / 回复 {rep} / 转发 {rt})  ",
        f"**时间跨度**: {min(dates.keys(), default='?')} ~ {max(dates.keys(), default='?')}",
        "",
        "## 1. 类型判断",
        "",
        f"### 1.1 标的分布",
        "",
        "| 市场 | 出现次数 | 占比 |",
        "|---|---|---|",
    ]
    for m, c in markets.most_common(10):
        lines.append(f"| {m} | {c} | {c/n*100:.1f}% |")

    lines.extend([
        "",
        f"### 1.2 板块 Top 10",
        "",
        "| 板块 | 推文数 | 占比 |",
        "|---|---|---|",
    ])
    for s, c in sectors.most_common(10):
        lines.append(f"| {s} | {c} | {c/n*100:.1f}% |")

    lines.extend([
        "",
        f"### 1.3 美股 ticker Top 15",
        "",
        "| ticker | 推文数 |",
        "|---|---|",
    ])
    for t, c in us_t.most_common(15):
        lines.append(f"| ${t} | {c} |")

    lines.extend([
        "",
        f"### 1.4 港股代码 Top 10",
        "",
        "| 代码 | 推文数 |",
        "|---|---|",
    ])
    for t, c in hk_c.most_common(10):
        lines.append(f"| {t} | {c} |")

    lines.extend([
        "",
        f"### 1.5 A 股代码 Top 10",
        "",
        "| 代码 | 推文数 |",
        "|---|---|",
    ])
    for t, c in a_c.most_common(10):
        lines.append(f"| {t} | {c} |")

    lines.extend([
        "",
        f"### 1.6 方向词分布",
        "",
        "| 方向 | 推文数 |",
        "|---|---|",
    ])
    for d, c in directions.most_common():
        lines.append(f"| {d} | {c} |")

    lines.extend([
        "",
        "## 2. 可证伪判断清单 (LLM 提取)",
        "",
        f"**总数**: {len(judgments)} 条  ",
        f"**判定标准**: 可证伪 + 有方向 + 有时间窗 + 有具体标的/板块/指数",
        "",
    ])
    if judgments:
        lines.append("| # | 日期 | 类型 | 标的 | 方向 | 时间窗 | 共识度 | 原文 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, j in enumerate(judgments, 1):
            date = j.get("date", "?")
            jt = j.get("type", "?")
            target = j.get("target", "?")
            direction = j.get("direction", "?")
            tf = j.get("timeframe", "?")
            cons = j.get("consensus", "?")
            excerpt = (j.get("excerpt", "") or "").replace("|", "/")[:50]
            lines.append(f"| {i} | {date} | {jt} | {target} | {direction} | {tf} | {cons} | {excerpt} |")
    else:
        lines.append("⚠️ LLM 没有提取到可证伪判断 (内容偏 commentary / 缺方向 / 缺时间窗)")

    lines.extend([
        "",
        "## 3. 你的判断任务",
        "",
        "读 1.1~1.5 + 第 2 节判断清单, 决定:",
        "",
        "- **类型画像** (信号源 / 产业卡点 / 宏观择时 / 混合)",
        "- **能验证什么** (美股 ticker 可 verify, A 股/港股代码需要付费数据)",
        "- **第 2 节判断** 哪几条你觉得是真有观点 (而不是讲漂亮话)",
        "",
        "等你的判断, 我再跑第 3 步事后验证。",
    ])
    judgments = all_judgments if 'all_judgments' in dir() else judgments
    lines.append(f"**总数**: {len(judgments)} 条  ")
    if judgments:
        lines.append("| # | 日期 | 类型 | 标的 | 方向 | 时间窗 | 共识度 | 原文 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, j in enumerate(judgments, 1):
            date = j.get("date", "?")
            jt = j.get("type", "?")
            target = j.get("target", "?")
            direction = j.get("direction", "?")
            tf = j.get("timeframe", "?")
            cons = j.get("consensus", "?")
            excerpt = (j.get("excerpt", "") or "").replace("|", "/")[:50]
            lines.append(f"| {i} | {date} | {jt} | {target} | {direction} | {tf} | {cons} | {excerpt} |")
    else:
        lines.append("⚠️ LLM 没有提取到可证伪判断 (内容偏 commentary / 缺方向 / 缺时间窗)")

    lines.extend([
        "",
        "## 3. 你的判断任务",
        "",
        "读 1.1~1.5 + 第 2 节判断清单, 决定:",
        "",
        "- **类型画像** (信号源 / 产业卡点 / 宏观择时 / 混合)",
        "- **能验证什么** (美股 ticker 可 verify, A 股/港股代码需要付费数据)",
        "- **第 2 节判断** 哪几条你觉得是真有观点 (而不是讲漂亮话)",
        "",
        "等你的判断, 我再跑第 3 步事后验证。",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    main()