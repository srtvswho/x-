"""P4-7c 从 raw timelines 重新拿 full createdAt 修 verify"""
import os, json, sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

PRICE_DIR = "/workspace/data/price_cache"
TODAY = "2026-06-12"


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


def parse_twitter_date(s):
    """parse 'Fri Jun 12 00:34:13 +0000 2026' 完整格式。"""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y").date()
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None


spy = load_bars("SPY")


def verify(ticker, pub_date, direction, horizon):
    d = pub_date
    if not d:
        return {"resolved": False, "reason": "no_date"}
    entry_date = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    horizon = min(int(horizon or 30), 180)
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
    if direction == "long":
        raw = (x_px - e_px) / e_px
    elif direction == "short":
        raw = (e_px - x_px) / e_px
    else:
        return {"resolved": False, "reason": "neutral"}
    spy_ret = (sx_px - se_px) / se_px
    excess = raw - spy_ret
    hit = (excess > 0 and direction == "long") or (excess < 0 and direction == "short")
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


# 重新加载 predictions
with open("/workspace/logs/p4p7_predictions.json") as f:
    preds = json.load(f)
# 加载 raw timelines (有完整 createdAt)
with open("/workspace/logs/p4p7_timelines_raw.json") as f:
    timelines = json.load(f)

# 用 tweet_id 找 full createdAt
tweet_id_to_date = {}
for author, items in timelines.items():
    for it in items:
        tid = it.get("id")
        cd_full = it.get("createdAt", "")
        d = parse_twitter_date(cd_full)
        if d:
            tweet_id_to_date[tid] = d

print(f"Total tweet_id with parsed date: {len(tweet_id_to_date)}")

# 重新跑 verify
verified = []
unresolved_reasons = Counter()
for p in preds:
    tid = p.get("tweet_id")
    d = tweet_id_to_date.get(tid)
    if d is None:
        # fallback: 直接 parse p['tweet_date']
        d = parse_twitter_date(p.get("tweet_date", ""))
    if d is None:
        p["verification"] = {"resolved": False, "reason": "no_date"}
        unresolved_reasons["no_date"] += 1
        continue
    v = verify(p["ticker"], d, p["direction"], p.get("horizon_days", 30))
    p["verification"] = v
    p["tweet_date_iso"] = d.isoformat()
    if v.get("resolved"):
        verified.append(p)
    else:
        unresolved_reasons[v.get("reason", "?")] += 1

print(f"Resolved: {len(verified)} / {len(preds)}")
print(f"Unresolved reasons: {dict(unresolved_reasons)}")

# Stats
print(f"\n{'author':12s} {'#pred':6s} {'#resolved':10s} {'#hit':6s} {'hit_rate':10s} {'med_exc':10s} {'med_raw':10s} {'#long':6s} {'#short':6s}")
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
    n_all = len([p for p in preds if p["author"] == a])
    print(f"  @{a:11s} {n_all:6d} {n:10d} {n_hit:6d} {hr:8.1f}% {med_exc:+8.1f}% {med_raw:+8.1f}% {n_long:6d} {n_short:6d}")

# 排除 SNDK
print(f"\n=== 关键: 排除 SNDK 后的命中率 (其他票) ===")
print(f"{'author':12s} {'#pred':6s} {'#resolved':10s} {'#hit':6s} {'hit_rate':10s} {'med_exc':10s} {'unique_tickers':50s}")
for a in ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]:
    ps = [p for p in verified if p["author"] == a and p["ticker"] != "SNDK"]
    n = len(ps)
    n_hit = sum(1 for p in ps if p["verification"]["hit"])
    hr = n_hit/n*100 if n else 0
    med_exc = statistics.median([p["verification"]["excess_ret"] for p in ps]) if ps else 0
    unique_t = sorted(set(p["ticker"] for p in ps))
    n_all = len([p for p in preds if p["author"] == a and p["ticker"] != "SNDK"])
    print(f"  @{a:11s} {n_all:6d} {n:10d} {n_hit:6d} {hr:8.1f}% {med_exc:+8.1f}% {','.join(unique_t[:12])}")

# 按 ticker 详细 (4 人表现)
print(f"\n=== 4 人在每个 ticker 上的逐条表现 (resolved only) ===")
for a in ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]:
    print(f"\n--- @{a} ---")
    for p in verified:
        if p["author"] == a:
            v = p["verification"]
            hit = "✅" if v["hit"] else "❌"
            print(f"  {p['tweet_date_iso']} {p['ticker']:12s} {p['direction']:6s} h={v['horizon_days']:3d}d entry=${v['entry_px']:7.2f} exit=${v['exit_px']:7.2f} excess={v['excess_ret']:+7.1f}% {hit} | {p.get('thesis','')[:60]}")

# 保存
with open("/workspace/logs/p4p7c_verified.json", "w") as f:
    json.dump({
        "all_predictions": preds,
        "verified": verified,
        "by_author": {a: [p for p in verified if p["author"] == a] for a in ["oopsguess", "jukan05", "wmhuo168", "lokoyacap"]},
    }, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p7c_verified.json")