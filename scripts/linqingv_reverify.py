"""LinQingV 重验 — 修对日期 + 走 P5 完整管道 (LLM 抽 direction + attribution + Polygon verify)"""
import json, re, statistics, urllib.request, os, time, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PRICE_DIR = Path("/workspace/data/price_cache")
DATA_END = "2026-06-22"
HORIZON_DAYS = 90
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

# 1. 修对日期
tweets = json.load(open("/workspace/logs/p5_linqingv/tweets_raw.json"))
print(f"LinQingV raw: {len(tweets)}", flush=True)

id_to_text = {}
for t in tweets:
    tid = t.get("id")
    text = t.get("text") or t.get("fullText") or ""
    if tid:
        id_to_text[tid] = text

# 修 date
n_fixed = 0
for t in tweets:
    ca = t.get("createdAt", "")
    if ca:
        try:
            d = parsedate_to_datetime(ca).strftime("%Y-%m-%d")
            t["date"] = d
            n_fixed += 1
        except:
            t["date"] = None
print(f"修 date: {n_fixed}/{len(tweets)}", flush=True)

# 2. LLM 抽 direction (并发 25)
DIRECTION_PROMPT = """你是 X 推文投资方向判定器. 判定作者对所提标的的"个人方向判断".

【推文】{text}
【日期】{date}
【ticker】{ticker}

【规则 — 严格按 P5 铁律 1+2】
- 看多 (long): 关键词 buy/long/bullish/看多/做多/推荐/加仓/建仓/我会买/看好/"I will be buying"/"I bought"/"I am long"/"to me this is a buy"/"this is a great buy"
- 看空 (short): sell/short/bearish/看空/做空/不推荐/减仓/清仓/我会卖/看衰/"I sold"/"I am short"/"overvalued"
- 暗示: "Bought $X today" / "Sold $X today" / "Opened $X position" → 强方向
- "tobi thinks the stock is cheap" / "I am excited about $X" / "I see this going higher/lower" → 隐含 long/short
- "to me X is a buy" = long; "X is going down" = short

区分对象 (铁律 2):
- 消费建议 (buy electronics/products) → neutral
- 产品 launch 预测 (VR 不会出) → neutral
- 产业 fact (why CEO didn't announce X) → neutral
- 询问式 (Are you buying?) → neutral
- 评价/感慨 (great product) → neutral
- 多人 ticker 没对单个表态 → neutral

【输出严格 JSON】
{{"direction": "long"/"short"/"neutral", "thesis": "作者原话 ≤ 30 字", "evidence_keyword": "触发判定的关键词"}}
"""


def llm_direction(text, date, ticker):
    full = DIRECTION_PROMPT.format(text=text[:1500], date=date, ticker=ticker or "(无 $)")
    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": full}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 600,
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
    return {"direction": "?", "thesis": f"err: {last_err[:50]}", "evidence_keyword": ""}


# 3. 提取含 ticker 的推文
US_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
A_SHARE_RE = re.compile(r"\b[0-9]{6}\.(?:SH|SZ|SS)\b")
HK_RE = re.compile(r"\b[0-9]{4,5}\.HK\b")
KR_RE = re.compile(r"\b[0-9]{6}\.(?:KS|KQ)\b")
TW_RE = re.compile(r"\b[0-9]{4}\.(?:TW|TWO)\b")
TW_COMPANIES = ["TSMC", "UMC", "MediaTek", "Realtek", "ASpeed", "Win Semi", "Nuvoton", "Macronix", "Nanya", "Powerchip"]


def market_of(text, dollar_t):
    if KR_RE.search(text): return "KR"
    if TW_RE.search(text): return "TW"
    if HK_RE.search(text): return "HK"
    if A_SHARE_RE.search(text): return "A_share"
    if dollar_t:
        for t in dollar_t:
            if t == "TSM": return "TW"
        return "US"
    for c in TW_COMPANIES:
        if c in text: return "TW"
    return "?"


# 找 ticker 推文
candidates = []
for t in tweets:
    text = t.get("text") or t.get("fullText") or ""
    if not text: continue
    date = t.get("date")
    if not date: continue
    dollar_t = US_TICKER_RE.findall(text)
    market = market_of(text, dollar_t)
    if market == "US" and dollar_t:
        # 美股可验 (默认所有 US ticker)
        candidates.append({"id": t.get("id"), "date": date, "ticker": dollar_t[0], "text": text, "market": "US"})

print(f"\n美股 ticker 推文 (candidates): {len(candidates)}", flush=True)

# 4. LLM 抽 direction (并发 25)
print(f"开始 LLM 抽 direction (concurrent=25)...", flush=True)
t0 = time.time()
n_done = 0
n_long = n_short = n_neutral = n_err = 0
def one(c):
    d = llm_direction(c["text"][:1500], c["date"], c["ticker"])
    return c, d

with ThreadPoolExecutor(max_workers=25) as pool:
    futures = {pool.submit(one, c): c for c in candidates}
    for fut in as_completed(futures):
        c, d = fut.result()
        c["llm_direction"] = d.get("direction", "?")
        c["llm_thesis"] = d.get("thesis", "")
        c["llm_evidence"] = d.get("evidence_keyword", "")
        if d.get("direction") == "long": n_long += 1
        elif d.get("direction") == "short": n_short += 1
        elif d.get("direction") == "neutral": n_neutral += 1
        else: n_err += 1
        n_done += 1
        if n_done % 20 == 0:
            print(f"  [{time.time()-t0:.0f}s] {n_done}/{len(candidates)} c={n_long}/{n_short}/{n_neutral}/{n_err}", flush=True)

print(f"\n方向分布: long={n_long} short={n_short} neutral={n_neutral} err={n_err}", flush=True)

# 5. attribution heuristic
RELAYED_MARKERS = ["Goldman", "Morgan Stanley", "JP Morgan", "Bernstein", "Wedbush", "Piper", "Evercore", "Jefferies", "Susquehanna", "Raymond James", "TrendForce", "Counterpoint", "IDC", "Gartner", "Canalys", "Nikkei", "Reuters", "Bloomberg", "WSJ", "研报", "据彭博", "据路透"]
ORIGINAL_MARKERS = ["I think", "in my view", "my view", "my take", "in my opinion", "I believe", "I expect", "I'll buy", "I'll sell", "I am buying", "I am selling", "I'm buying", "I'm selling", "I'm long", "I'm short", "不推荐", "推荐", "I would add", "But I", "However, I", "I disagree", "I see it differently", "I however", "I see ", "I'd say", "I think "]
NEWS_MARKERS = ["BREAKING:", "JUST IN:", "REPORT:", "WSJ:", "Reuters:", "Bloomberg:", "Nikkei:", "TrendForce:", "according to ", "is reportedly"]

def attr(text):
    has_r = any(m in text for m in RELAYED_MARKERS)
    has_o = any(m in text for m in ORIGINAL_MARKERS)
    has_news = any(m in text for m in NEWS_MARKERS)
    if has_r and not has_o: return "RELAYED"
    if has_o and not has_r: return "ORIGINAL"
    if has_r and has_o: return "RELAYED+COMMENT"
    if has_news and not has_o: return "news"
    return "?"

for c in candidates:
    c["attribution"] = attr(c["text"])

# 6. Polygon verify (跟之前 verify_3kol_v6 逻辑)
def find_price(bars, target):
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None

def load_bars(ticker):
    fp = PRICE_DIR / f"{ticker}_FULL_HISTORY.json"
    if fp.exists():
        return json.load(open(fp))
    return []

def verify_one(c, benchmarks):
    entry_date = c["date"]
    try:
        d_obj = datetime.strptime(entry_date, "%Y-%m-%d")
    except:
        return {"resolved": False, "reason": "bad_date"}
    exit_target = (d_obj + timedelta(days=HORIZON_DAYS)).strftime("%Y-%m-%d")
    exit_actual = min(datetime.strptime(exit_target, "%Y-%m-%d"), datetime.strptime(DATA_END, "%Y-%m-%d")).strftime("%Y-%m-%d")
    
    bars = load_bars(c["ticker"])
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{c['ticker']}"}
    
    e_px, _ = find_price(bars, entry_date)
    x_px, _ = find_price(bars, exit_actual)
    if not e_px or not x_px:
        return {"resolved": False, "reason": f"no_px"}
    
    direction = c["llm_direction"]
    if direction == "long":
        raw_ret = (x_px - e_px) / e_px * 100
    elif direction == "short":
        raw_ret = (e_px - x_px) / e_px * 100
    else:
        return {"resolved": False, "reason": "neutral"}
    
    excess = {}
    for bench, bb in benchmarks.items():
        be, _ = find_price(bb, entry_date)
        bx, _ = find_price(bb, exit_actual)
        if be and bx:
            bench_ret = (bx - be) / be * 100
            excess[bench] = {"excess_ret": raw_ret - bench_ret, "bench_ret": bench_ret, "raw_ret": raw_ret}
    
    if exit_actual == exit_target:
        status = "resolved"
    else:
        status = "pending"
    
    return {
        "resolved": True,
        "status": status,
        "ticker": c["ticker"],
        "direction": direction,
        "entry_date": entry_date,
        "exit_date_actual": exit_actual,
        "entry_px": e_px,
        "exit_px": x_px,
        "raw_ret": raw_ret,
        "excess": excess,
        "is_raw_loss": raw_ret < 0,
        "thesis": c.get("llm_thesis", ""),
        "attribution": c.get("attribution", "?"),
    }

benchmarks = {"SPY": load_bars("SPY"), "SOXX": load_bars("SOXX"), "QQQ": load_bars("QQQ")}
resolved = []
pending = []
unresolved = Counter()
for c in candidates:
    if c["llm_direction"] not in ("long", "short"): continue
    v = verify_one(c, benchmarks)
    if not v.get("resolved"):
        unresolved[v.get("reason", "?")] += 1
    elif v.get("status") == "pending":
        pending.append(v)
    else:
        resolved.append(v)

# 7. 报告
rm_res = {"n": len(resolved), "n_pos": sum(1 for v in resolved if v["raw_ret"] > 0), "n_neg": sum(1 for v in resolved if v["raw_ret"] < 0)}
if resolved:
    rm_res["hit_rate"] = rm_res["n_pos"] / rm_res["n"] * 100
    rm_res["med_raw"] = statistics.median([v["raw_ret"] for v in resolved])
else:
    rm_res["hit_rate"] = 0
    rm_res["med_raw"] = 0

em_soxx = {"n": 0, "med_excess": 0, "hit_rate": 0}
if resolved:
    sub = [v for v in resolved if "SOXX" in v["excess"]]
    if sub:
        em_soxx["n"] = len(sub)
        em_soxx["med_excess"] = statistics.median([v["excess"]["SOXX"]["excess_ret"] for v in sub])
        em_soxx["hit_rate"] = sum(1 for v in sub if v["excess"]["SOXX"]["excess_ret"] > 0) / len(sub) * 100

# 8. 保存
out = {
    "handle": "LinQingV",
    "n_raw": len(tweets),
    "n_us_tweets": len(candidates),
    "n_long": n_long, "n_short": n_short, "n_neutral": n_neutral, "n_err": n_err,
    "n_resolved": len(resolved),
    "n_pending": len(pending),
    "n_unresolved": dict(unresolved),
    "rm_resolved": rm_res,
    "em_soxx": em_soxx,
    "resolved": resolved,
    "pending": pending,
}
json.dump(out, open("/workspace/logs/p5_linqingv/reverify_v2.json", "w"), indent=2, ensure_ascii=False, default=str)
print(f"\n💾 saved reverify_v2.json")
print(f"  n_us_tweets: {len(candidates)}")
print(f"  LLM 方向: long={n_long} short={n_short} neutral={n_neutral} err={n_err}")
print(f"  已验证: {len(resolved)} / pending: {len(pending)}")
print(f"  raw_hit (resolved): {rm_res['hit_rate']:.1f}%")
print(f"  med_raw (resolved): {rm_res['med_raw']:+.1f}%")
print(f"  med_excess_soxx: {em_soxx['med_excess']:+.1f}%")
