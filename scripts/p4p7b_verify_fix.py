"""P4-7b 修 date bug 跑验证"""
import os, json, sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

PRICE_DIR = "/workspace/data/price_cache"
DB = "/workspace/data/signalboard_full.db"

with open("/workspace/logs/p4p7_predictions.json") as f:
    preds = json.load(f)

print(f"Total predictions: {len(preds)}")


def parse_date(s):
    """parse 多种日期格式。"""
    if not s:
        return None
    s10 = s[:10]
    try:
        return datetime.strptime(s10, "%Y-%m-%d").date()
    except ValueError:
        pass
    # Twitter 格式 "Mon Jun 08 13:45:23 +0000 2025"
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
    except (ValueError, TypeError):
        pass
    # ISO with T
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


def load_bars(t):
    p = f"{PRICE_DIR}/{t}_FULL_HISTORY.json"
    if not os.path.exists(p) and t == "SIVE":
        p = f"{PRICE_DIR}/SIVEF_FULL_HISTORY.json"
    if os.path.exists(p):
        return json.load(open(p))
    return []


def find_price(bars, target):
    for b in bars:
        if b["date"] >= target:
            return b["c"], b["date"]
    return None, None


spy = load_bars("SPY")
TODAY = "2026-06-12"


def verify(p):
    ticker = p["ticker"]
    pub = p.get("tweet_date", "")
    d = parse_date(pub)
    if not d:
        return {"resolved": False, "reason": "bad_date"}
    entry_date = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    horizon = min(int(p.get("horizon_days", 30) or 30), 180)
    exit_date = min((d + timedelta(days=horizon + 1)).strftime("%Y-%m-%d"), TODAY)

    bars = load_bars(ticker)
    if not bars:
        return {"resolved": False, "reason": f"no_bars_{ticker}"}

    e_px, _ = find_price(bars, entry_date)
    x_px, xd = find_price(bars, exit_date)
    if not e_px or not x_px:
        return {"resolved": False, "reason": "no_px"}

    se_px, _ = find_price(spy, entry_date)
    sx_px, _ = find_price(spy, exit_date)
    if not se_px or not sx_px:
        return {"resolved": False, "reason": "no_spy"}

    if p["direction"] == "long":
        raw = (x_px - e_px) / e_px
    elif p["direction"] == "short":
        raw = (e_px - x_px) / e_px
    else:
        return {"resolved": False, "reason": "neutral"}

    spy_ret = (sx_px - se_px) / se_px
    excess = raw - spy_ret
    hit = (excess > 0 and p["direction"] == "long") or (excess < 0 and p["direction"] == "short")
    return {
        "resolved": True,
        "hit": hit,
        "raw_ret": raw * 100,
        "excess_ret": excess * 100,
        "entry_px": e_px,
        "exit_px": x_px,
        "entry_date": entry_date,
        "exit_date": xd or exit_date,
        "horizon_days": horizon,
        "ticker": ticker,
    }


verified = []
for p in preds:
    v = verify(p)
    p["verification"] = v
    if v.get("resolved"):
        verified.append(p)

print(f"\nResolved: {len(verified)} / {len(preds)}")

# 统计
print(f"\n{'author':12s} {'#pred':6s} {'#resolved':10s} {'#hit':6s} {'hit_rate':10s} {'med_exc':10s} {'med_raw':10s} {'#long':6s} {'#short':6s} {'#won_long':10s} {'#won_short':10s}")
by_author = defaultdict(list)
for p in verified:
    by_author[p["author"]].append(p)

for a in ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]:
    ps = by_author.get(a, [])
    n = len(ps)
    n_hit = sum(1 for p in ps if p["verification"]["hit"])
    hr = n_hit/n*100 if n else 0
    med_exc = statistics.median([p["verification"]["excess_ret"] for p in ps]) if ps else 0
    med_raw = statistics.median([p["verification"]["raw_ret"] for p in ps]) if ps else 0
    n_long = sum(1 for p in ps if p["direction"] == "long")
    n_short = sum(1 for p in ps if p["direction"] == "short")
    won_long = sum(1 for p in ps if p["direction"] == "long" and p["verification"]["hit"])
    won_short = sum(1 for p in ps if p["direction"] == "short" and p["verification"]["hit"])
    n_all = len([p for p in preds if p["author"] == a])
    print(f"  @{a:11s} {n_all:6d} {n:10d} {n_hit:6d} {hr:8.1f}% {med_exc:+8.1f}% {med_raw:+8.1f}% {n_long:6d} {n_short:6d} {won_long:10d} {won_short:10d}")

# 排除 SNDK (survivorship bias fix)
print(f"\n=== 关键: 排除 SNDK 后的命中率 ===")
print(f"{'author':12s} {'#pred':6s} {'#resolved':10s} {'#hit':6s} {'hit_rate':10s} {'med_exc':10s} {'unique_tickers':30s}")
for a in ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]:
    ps_no_sndk = [p for p in verified if p["author"] == a and p["ticker"] != "SNDK"]
    n = len(ps_no_sndk)
    n_hit = sum(1 for p in ps_no_sndk if p["verification"]["hit"])
    hr = n_hit/n*100 if n else 0
    med_exc = statistics.median([p["verification"]["excess_ret"] for p in ps_no_sndk]) if ps_no_sndk else 0
    unique_t = sorted(set(p["ticker"] for p in ps_no_sndk))
    n_all = len([p for p in preds if p["author"] == a and p["ticker"] != "SNDK"])
    print(f"  @{a:11s} {n_all:6d} {n:10d} {n_hit:6d} {hr:8.1f}% {med_exc:+8.1f}% {','.join(unique_t[:10])}")

# 按 ticker 看 4 人在每个 ticker 上共识/分歧
print(f"\n=== 4 人共同提到的 ticker (cross-validation) ===")
ticker_authors = defaultdict(set)
for p in verified:
    ticker_authors[p["ticker"]].add(p["author"])
for t, authors in sorted(ticker_authors.items(), key=lambda x: -len(x[1])):
    if len(authors) >= 1:
        # show predictions
        ps = [p for p in verified if p["ticker"] == t]
        for p in ps:
            v = p["verification"]
            hit = "✅" if v["hit"] else "❌"
            print(f'  {t:10s} @{p["author"]:12s} {p["direction"]:6s} {p["tweet_date"][:10]} excess={v["excess_ret"]:+6.1f}% {hit}')

# 保存
with open("/workspace/logs/p4p7b_verified.json", "w") as f:
    json.dump({
        "all_predictions": preds,
        "verified": verified,
        "by_author": {a: [p for p in verified if p["author"] == a] for a in ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]},
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p7b_verified.json")