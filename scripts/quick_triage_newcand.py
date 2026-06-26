"""6 候选体检 (attribution + market + 4 维度)"""
import json, re
from collections import Counter
from email.utils import parsedate_to_datetime

CANDS = ["clausaasholm", "siliconomy", "bepresearch", "chipstrat", "austinsemis", "kermankohli"]

# 启发式
RELAYED_MARKERS = ["Goldman", "Morgan Stanley", "JP Morgan", "Bernstein", "Wedbush", "Piper", "Evercore", "Jefferies", "Susquehanna", "Raymond James", "TrendForce", "Counterpoint", "IDC", "Gartner", "Canalys", "Nikkei", "Reuters", "Bloomberg", "WSJ", "研报", "据彭博", "据路透", "TREND", "checks indicate", "checks suggest", "sources say"]
ORIGINAL_MARKERS = ["I think", "in my view", "my view", "my take", "in my opinion", "I believe", "I expect", "I'll buy", "I'll sell", "I am buying", "I am selling", "I'm buying", "I'm selling", "I'm long", "I'm short", "不推荐", "推荐", "I would add", "But I", "However, I", "I disagree", "I see it differently", "I however", "I see ", "I'd say", "I think ", "I want to", "I am going", "I expect", "my view", "I expect ", "I expect "]
RC_MARKERS = ["However, I", "But I think", "I disagree", "I see it differently", "My view is different", "不过我认为", "不过我", "我不同意", "I would add", "I'd add", "That said, I", "I however"]
NEWS_MARKERS = ["BREAKING:", "JUST IN:", "REPORT:", "WSJ:", "Reuters:", "Bloomberg:", "Nikkei:", "TrendForce:", "TSMC said", "Samsung said", "Intel said", "according to ", "is reportedly", "is said to"]
COMMENTARY_MARKERS = ["Looking forward to", "Interesting", "Thoughts?", "Thoughts on", "What do you think", "fwiw", "imo", "imho", "thread", "long thread", "My two cents"]

def attr(text):
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

# market
A_SHARE_RE = re.compile(r"\b[0-9]{6}\.(?:SH|SZ|SS)\b")
HK_RE = re.compile(r"\b[0-9]{4,5}\.HK\b")
KR_RE = re.compile(r"\b[0-9]{6}\.(?:KS|KQ)\b")
TW_RE = re.compile(r"\b[0-9]{4}\.(?:TW|TWO)\b")
US_TICKER_RE = re.compile(r"\$([A-Z]{1,5})\b")
TW_COMPANIES = ["TSMC", "UMC", "MediaTek", "Realtek", "ASSpeed", "Win Semi", "Nuvoton", "Macronix", "Nanya", "Powerchip", "Vanguard"]

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

# 已知 Polygon 可验美股 (扩充, 加更多)
POLYGON_US_OK = {"NVDA", "AAPL", "INTC", "AMD", "AVGO", "MU", "GOOGL", "QCOM", "AMZN", "AMAT", "MSFT", "META", "KLAC", "LRCX", "TER", "ENTG", "ON", "MPWR", "SWKS", "NVMI", "MRVL", "ASML", "TXN", "ADI", "CRM", "ORCL", "IBM", "CSCO", "PLTR", "CRWD", "PANW", "FTNT", "NOW", "DDOG", "NET", "SNOW", "SHOP", "UBER", "LYFT", "ARM", "DELL", "HPQ", "HPE", "ANET", "FICO", "APH", "TEL", "JBL", "ADI", "MSCI", "PWR", "ETN", "ROK", "IR", "EMR", "PH", "CMI", "DE", "CAT", "URI", "FAST", "WSC"}

for cand in CANDS:
    fp = f"/workspace/logs/p5_newcandidates/raw_{cand}.json"
    tweets = json.load(open(fp))
    print("=" * 70)
    print(f"@{cand}: {len(tweets)} tweets")

    # attribution
    attr_count = Counter()
    orig_market = Counter()
    orig_tickers = Counter()
    orig_polygon = 0
    orig_tickers_polygon = set()

    for t in tweets:
        text = t.get("text") or t.get("fullText") or ""
        if not text: continue
        a = attr(text)
        attr_count[a] += 1
        if a == "ORIGINAL":
            dollar_t = US_TICKER_RE.findall(text)
            for tk in dollar_t:
                orig_tickers[tk] += 1
                if tk in POLYGON_US_OK:
                    orig_tickers_polygon.add(tk)
                    orig_polygon += 1
            market = market_of(text, dollar_t)
            orig_market[market] += 1

    print(f"  attribution:")
    for k, c in attr_count.most_common():
        print(f"    {k}: {c} ({c/len(tweets)*100:.1f}%)")

    print(f"  ORIGINAL 推文: {attr_count.get('ORIGINAL', 0)}")
    print(f"  ORIGINAL 推文市场分布:")
    total_o = sum(orig_market.values()) or 1
    for m, c in orig_market.most_common():
        print(f"    {m}: {c}")
    print(f"  ORIGINAL 推文含 US Polygon 可验 ticker: {orig_polygon} (tickers: {sorted(orig_tickers_polygon)})")
    print(f"  ORIGINAL 推文 US ticker top 10: {[(t, c) for t, c in orig_tickers.most_common(10)]}")

    # 简介 + name
    if tweets:
        first = tweets[0]
        au = first.get("author", {})
        print(f"  name: {au.get('name', '')}")
        print(f"  description: {(au.get('description') or '')[:200]}")
