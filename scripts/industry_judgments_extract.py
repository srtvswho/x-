"""@fi56622380 体检 + 3 人新标准产业判断抽取"""
import json, re, os, time, urllib.request, sys
from collections import Counter
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# === @fi56622380 体检 ===
fi = json.load(open("/workspace/logs/p5_industry_judgments/raw_fi56622380.json"))
print(f"@fi56622380: {len(fi)} tweets")

US_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
RELAYED_MARKERS = ["Goldman", "Morgan Stanley", "JP Morgan", "Bernstein", "Wedbush", "Piper", "Evercore", "Jefferies", "Susquehanna", "Raymond James", "TrendForce", "Counterpoint", "IDC", "Gartner", "Canalys", "Nikkei", "Reuters", "Bloomberg", "WSJ", "研报", "据彭博", "据路透", "TREND", "checks indicate", "checks suggest", "sources say"]
ORIGINAL_MARKERS = ["I think", "in my view", "my view", "my take", "in my opinion", "I believe", "I expect", "I'll buy", "I'll sell", "I am buying", "I am selling", "I'm buying", "I'm selling", "I'm long", "I'm short", "不推荐", "推荐", "I would add", "But I", "However, I", "I disagree", "I see it differently", "I however", "I see ", "I'd say", "I think ", "I want to", "I am going", "我倾向于", "我认为", "我看", "我的判断", "看好", "看衰", "看多", "看空", "我不认为", "我觉得", "大概率", "我觉得", "事实上", "实际上"]
NEWS_MARKERS = ["BREAKING:", "JUST IN:", "REPORT:", "WSJ:", "Reuters:", "Bloomberg:", "Nikkei:", "TrendForce:", "according to ", "is reportedly", "is said to"]

def attr(text):
    has_r = any(m in text for m in RELAYED_MARKERS)
    has_o = any(m in text for m in ORIGINAL_MARKERS)
    has_news = any(m in text for m in NEWS_MARKERS)
    if has_r and not has_o: return "RELAYED"
    if has_o and not has_r: return "ORIGINAL"
    if has_r and has_o: return "RELAYED+COMMENT"
    if has_news and not has_o: return "news"
    return "?"

attr_count = Counter()
us_tickers = Counter()
for t in fi:
    text = t.get("text", "")
    if not text: continue
    attr_count[attr(text)] += 1
    for tk in US_TICKER_RE.findall(text):
        us_tickers[tk] += 1
print(f"\nattribution:")
for k, c in attr_count.most_common():
    print(f"  {k}: {c} ({c/len(fi)*100:.1f}%)")
print(f"\nUS ticker top 20:")
for t, c in us_tickers.most_common(20):
    print(f"  ${t}: {c}")

# === 3 人产业判断抽取 (新 prompt) ===
JUDGMENT_PROMPT = """你是 X 推文产业判断抽取器. 抽取"有明确方向性 + 可证伪 + 能对应到标的"的产业判断.

【规则 — 不再要求 buy/sell 建仓词, 接受任何方向性表达】

**可证伪产业判断** = 满足 3 个条件:
1) **有明确方向性**: X 会涨/会崩/会赢/会被淘汰/会供不应求/被低估/被高估/会先量产/会率先用/会失败/会主导
   - 不需要 "buy/sell" 关键词, 但必须有"有立场"的话术
   - 包括: "will be / would / is going to / should / must / 必然 / 注定 / 看好 / 看衰 / 看多 / 看空 / 优先 / 主导"
   - 包括: "I think X is Y" (X 标的 + Y 评价) 算
2) **可证伪**: 有具体对象 + 隐含时间, 不是"市场有风险"这种废话
3) **能对应到标的**: 明说 $ticker, 或能从公司名/事件推导出受益/受损公司

【方向映射 — 推导标的时要保守, 不要牵强附会】
- "光交换机消失/衰退" → COHR, LITE, ACIA, FN, AAOI (光通信)
- "AI infra 持续繁荣" → NVDA, AMD, AVGO, MU, VRT, NVMI, AMD 供应链
- "CPO 赢 vs Pluggable" → COHR (CPO), LITE (pluggable transceiver)
- "TSMC 领先" → TSM, NVDA (依赖 TSMC)
- "HBM 紧缺" → MU, Samsung (韩股), SK Hynix
- "Intel 制造衰弱/翻身" → INTC
- "Marvell 主导 AI chip" → MRVL

【判断所属类型】(择 1)
- LONG: 标的看多 (会涨/会赢/会主导)
- SHORT: 标的看空 (会跌/会衰退/会被淘汰)
- SUPPLY/DEMAND: 供应链紧缺/过剩 (引申 LONG/SHORT)
- TECHNICAL: 技术路线胜出/淘汰 (引申 LONG/SHORT)
- COMPETITIVE: 公司间竞争 (引申相对 LONG/SHORT)
- MACRO: 宏观判断 (引申多标的)
- COMMENTARY: 一般评论, 无方向 — 跳过

【输出严格 JSON】
{{"judgments": [
  {{
    "judgment": "原文 1 句话",
    "date": "YYYY-MM-DD",
    "type": "LONG/SHORT/SUPPLY/TECHNICAL/COMPETITIVE/MACRO/COMMENTARY",
    "direction": "long/short/neutral",  # 对应到标的的方向
    "implied_tickers": ["ticker1", "ticker2"],  # 明说或推导出的标的
    "implied_market": "US/KR/TW/HK",  # 标的可验市场
    "confidence": "high/medium/low",  # 方向明确性
    "derivation_logic": "如果隐含 ticker, 写推导逻辑"
  }}
]}}
如无判断, 返回 {{"judgments": []}}
"""

def llm_judgments(text, date, source):
    full = f"【推文】{text[:1500]}\n【日期】{date}\n【来源】@{source}\n\n" + JUDGMENT_PROMPT
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": full}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 1500,
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
                resp = json.loads(r.read().decode())
            cs = resp["choices"][0]["message"]["content"]
            if not cs:
                raise ValueError("empty content")
            return json.loads(cs)
        except Exception as e:
            last_err = str(e)
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return {"judgments": [], "error": last_err}


# 抽样推文 (不能全部跑, 太多)
def load_tweets(path):
    t = json.load(open(path))
    out = []
    for x in t:
        ca = x.get("createdAt", "")
        if not ca: continue
        try:
            d = parsedate_to_datetime(ca).strftime("%Y-%m-%d")
        except:
            continue
        text = x.get("text") or x.get("fullText") or ""
        if not text: continue
        out.append({"id": x.get("id"), "date": d, "text": text})
    return out


# === 3 人抽样 + 并发 LLM ===
TARGETS = {
    "fi56622380": ("@fi56622380", "logs/p5_industry_judgments/raw_fi56622380.json"),
    "zephyr_z9": ("@zephyr_z9", "logs/p5_zephyr/raw_all.json"),
    "austinsemis": ("@austinsemis", "logs/p5_newcandidates/raw_austinsemis.json"),
}

import random
random.seed(42)
all_judgments = {}

for handle, (source, path) in TARGETS.items():
    tweets = load_tweets(f"/workspace/{path}")
    print(f"\n=== @{handle}: {len(tweets)} 推文 ===")
    # 抽样 50 条 (不能全跑, 太多)
    if len(tweets) > 100:
        # 跨月份均匀抽样
        by_month = {}
        for t in tweets:
            by_month.setdefault(t["date"][:7], []).append(t)
        # 每月抽 3 条
        sampled = []
        for mo, items in sorted(by_month.items()):
            sampled.extend(random.sample(items, min(3, len(items))))
        tweets = sampled
        print(f"  抽样: {len(tweets)} 条")

    # 并发 LLM
    t0 = time.time()
    n_done = 0
    n_judgments = 0
    judgments = []
    def one(t):
        return t, llm_judgments(t["text"], t["date"], source)

    with ThreadPoolExecutor(max_workers=25) as pool:
        futures = {pool.submit(one, t): t for t in tweets}
        for fut in as_completed(futures):
            try:
                t, r = fut.result()
                for j in r.get("judgments", []):
                    j["source_handle"] = source
                    j["source_id"] = t["id"]
                    judgments.append(j)
                    n_judgments += 1
            except Exception as e:
                sys.stderr.write(f"err: {e}\n")
            n_done += 1
            if n_done % 10 == 0:
                print(f"  [{time.time()-t0:.0f}s] {n_done}/{len(tweets)} judgments={n_judgments}", flush=True)
    print(f"  [{time.time()-t0:.0f}s] done: {n_judgments} judgments from {n_done} tweets", flush=True)
    all_judgments[handle] = judgments

# 保存
json.dump(all_judgments, open("/workspace/logs/p5_industry_judgments/judgments_3kols.json", "w"), indent=2, ensure_ascii=False)
print(f"\n💾 saved: {sum(len(v) for v in all_judgments.values())} judgments")
