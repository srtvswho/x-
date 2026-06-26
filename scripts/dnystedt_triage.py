"""dnystedt attribution v2 + market + ORIGINAL 样本"""
import json, re
from collections import Counter

tweets = json.load(open("/workspace/logs/p5_dnystedt/raw_all.json"))
print(f"总推文: {len(tweets)}")

RELAYED_MARKERS = ["Goldman", "Morgan Stanley", "JP Morgan", "Bernstein", "Wedbush", "Piper", "Evercore", "Jefferies", "Susquehanna", "Raymond James", "TrendForce", "Counterpoint", "IDC", "Gartner", "Canalys", "Nikkei", "Reuters", "Bloomberg", "WSJ", "研报", "据彭博", "据路透", "TREND", "checks indicate", "according to", "checks suggest", "checks show", "sources say", "supply chain check"]
ORIGINAL_MARKERS = ["I think", "in my view", "my view", "my take", "in my opinion", "I believe", "I expect", "I estimate", "I'll buy", "I'll sell", "I am buying", "I am selling", "I'm buying", "I'm selling", "I'm long", "I'm short", "不推荐", "推荐", "I would add", "I'd add", "But I", "However, I", "I disagree", "I see it differently", "I however", "I see ", "I expect", "I'd say"]
RC_MARKERS = ["However, I", "But I think", "I disagree", "I see it differently", "My view is different", "不过我认为", "不过我", "我不同意", "I would add", "I'd add", "That said, I", "I however"]
NEWS_MARKERS = ["BREAKING:", "JUST IN:", "REPORT:", "WSJ:", "Reuters:", "Bloomberg:", "Nikkei:", "TrendForce:", "TSMC said", "Samsung said", "Intel said", "according to ", "TSMC will", "TSMC plans", "is reportedly", "is said to"]
COMMENTARY_MARKERS = ["Looking forward to", "Interesting", "Thoughts?", "Thoughts on", "What do you think", "fwiw", "imo", "imho", "thread", "long thread", "My two cents"]

def attr_v2(text):
    has_r = any(m in text for m in RELAYED_MARKERS)
    has_o = any(m in text for m in ORIGINAL_MARKERS)
    has_rc = any(m in text for m in RC_MARKERS)
    has_news = any(m in text for m in NEWS_MARKERS)
    has_comment = any(m in text for m in COMMENTARY_MARKERS)
    if has_r and (has_o or has_rc): return "RELAYED+COMMENT"
    if has_r and not has_o: return "RELAYED"
    if has_o and not has_r and not has_news: return "ORIGINAL"
    if has_news and not has_o: return "news"
    if has_comment and not has_o: return "commentary"
    if has_r and has_o: return "RELAYED+COMMENT"
    if has_o and not has_r: return "ORIGINAL"
    return "?"

attr_count = Counter()
for t in tweets:
    text = t.get("text") or t.get("fullText") or ""
    if not text: continue
    attr_count[attr_v2(text)] += 1

print(f"\n=== attribution v2 分布 ===")
for k, c in attr_count.most_common():
    print(f"  {k}: {c} ({c/len(tweets)*100:.1f}%)")

# ORIGINAL 样本
print(f"\n=== ORIGINAL 推文样本 ===")
n = 0
for t in tweets:
    text = t.get("text") or t.get("fullText") or ""
    if not text: continue
    if attr_v2(text) == "ORIGINAL":
        n += 1
        if n <= 8:
            ca = t.get("createdAt", "?")
            print(f"\n  [{ca[:10]}] {text[:300]}")

# 市场
A_SHARE_RE = re.compile(r"\b[0-9]{6}\.(?:SH|SZ|SS)\b")
HK_RE = re.compile(r"\b[0-9]{4,5}\.HK\b")
KR_RE = re.compile(r"\b[0-9]{6}\.(?:KS|KQ)\b")
TW_RE = re.compile(r"\b[0-9]{4}\.(?:TW|TWO)\b")
US_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
TW_COMPANIES = ["TSMC", "UMC", "MediaTek", "ASpeed", "Realtek", "Win Semi", "Nuvoton", "Macronix", "Nanya", "Powerchip", "Vanguard International"]

# dnystedt 大部分台股标的 (美股 ADR 或 OTC)
# 已知可 Polygon 验的: NVDA/AAPL/INTC/AMD/AVGO/MU/GOOGL/QCOM/AMZN/AMAT/MSFT/META/KLAC/LRCX/TER/ENTG/ON/MPWR/SWKS/NVMI
POLYGON_US_OK = {"NVDA", "AAPL", "INTC", "AMD", "AVGO", "MU", "GOOGL", "QCOM", "AMZN", "AMAT", "MSFT", "META", "KLAC", "LRCX", "TER", "ENTG", "ON", "MPWR", "SWKS", "NVMI", "MRVL", "ASML", "TXN", "ADI", "TXN", "CRM", "ORCL", "IBM", "CSCO", "PLTR", "CRWD", "PANW", "FTNT", "NOW", "DDOG", "NET", "SNOW", "SHOP", "UBER", "LYFT"}

def market_of(text, dollar_t):
    if KR_RE.search(text): return "KR"
    if TW_RE.search(text): return "TW"
    if HK_RE.search(text): return "HK"
    if A_SHARE_RE.search(text): return "A_share"
    if dollar_t:
        for t in dollar_t:
            if t == "TSM": return "TW"
            if t in ("SSNLF", "HXSCL", "TOELY"): return "KR/TW OTC (不可验)"
        return "US"
    for c in TW_COMPANIES:
        if c in text: return "TW"
    return "?"

# ORIGINAL + ticker 分布
print(f"\n=== ORIGINAL 推文市场分布 (启发式 v2) ===")
orig_market = Counter()
for t in tweets:
    text = t.get("text") or t.get("fullText") or ""
    if not text: continue
    if attr_v2(text) != "ORIGINAL": continue
    dollar_t = US_TICKER_RE.findall(text)
    market = market_of(text, dollar_t)
    orig_market[market] += 1
total_o = sum(orig_market.values())
for m, c in orig_market.most_common():
    print(f"  {m}: {c} ({c/total_o*100:.1f}%)")

# ORIGINAL + US + 可 Polygon 验
us_polygon = 0
us_other = 0
for t in tweets:
    text = t.get("text") or t.get("fullText") or ""
    if not text: continue
    if attr_v2(text) != "ORIGINAL": continue
    dollar_t = US_TICKER_RE.findall(text)
    for tk in dollar_t:
        if tk in POLYGON_US_OK:
            us_polygon += 1
        else:
            us_other += 1
print(f"\n=== ORIGINAL 推文中 US ticker 分布 ===")
print(f"  US ticker (Polygon 可验): {us_polygon}")
print(f"  US ticker (其他 / OTC): {us_other}")
