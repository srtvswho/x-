"""P3-13 增量更新 — 只重算 h_3m 状态,不动其他 horizon。

逻辑:
- 拉所有 h_3m_status='pending' 但 h_3m_exit_date <= 2026-06-22 的 prediction
- 重新算 h_3m_excess_return / h_3m_raw_return / h_3m_status
- 更新 DB
- 打印 SIVE 3m 新数据
"""
import os, sqlite3, json
from datetime import date, datetime

DB = "/workspace/data/signalboard_full.db"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

TODAY = "2026-06-22"
print(f"增量更新 h_3m 状态 (TODAY={TODAY})")

# 拉所有 h_3m pending 但 exit_date <= TODAY
rows = c.execute("""
    SELECT prediction_id, h_3m_exit_date, ticker
    FROM verifications
    WHERE h_3m_status='pending' AND h_3m_exit_date <= ?
""", (TODAY,)).fetchall()
print(f"待重算: {len(rows)} 条 (h_3m pending 但 exit_date <= {TODAY})")

# 拉这些 prediction 的 ticker + entry_date_actual + entry_price + direction
sive_updates = []
updated = 0
for pid, xd3m, ticker in rows:
    # 拉 prediction
    pr = c.execute("SELECT ticker, published_at, direction FROM predictions WHERE prediction_id=?", (pid,)).fetchone()
    vr = c.execute("""
        SELECT entry_date_actual, entry_price, h_3m_exit_price
        FROM verifications WHERE prediction_id=?
    """, (pid,)).fetchone()
    if not pr or not vr:
        continue
    p_ticker, pub, direction = pr
    edate, eprice, xprice = vr
    if not edate or not isinstance(eprice, (int, float)) or not xd3m:
        continue

    # 读 price_cache
    bars_path = f"/workspace/data/price_cache/{p_ticker}_FULL_HISTORY.json"
    if p_ticker == "SIVE":
        bars_path = f"/workspace/data/price_cache/SIVEF_FULL_HISTORY.json"
    if not os.path.exists(bars_path):
        continue
    with open(bars_path) as f:
        bars = json.load(f)
    if not bars:
        continue

    # 找 exit_date 的 bar
    exit_bar = None
    for b in bars:
        if b["date"] >= xd3m:
            exit_bar = b
            break
    if not exit_bar:
        exit_bar = bars[-1]

    xprice = exit_bar.get("c") or exit_bar.get("adjClose")
    if not isinstance(xprice, (int, float)):
        continue

    # 算 raw_return
    if direction == "long":
        raw_ret = (xprice - eprice) / eprice
    elif direction == "short":
        raw_ret = (eprice - xprice) / eprice
    else:
        raw_ret = 0

    # 找 SPY 同期 (用 entry_date_actual 和 exit_date)
    spy_path = "/workspace/data/price_cache/SPY_FULL_HISTORY.json"
    if not os.path.exists(spy_path):
        continue
    with open(spy_path) as f:
        spy_bars = json.load(f)

    # spy entry bar (entry_date 或之后第一个)
    spy_entry = None
    for b in spy_bars:
        if b["date"] >= edate:
            spy_entry = b
            break
    spy_exit = None
    for b in spy_bars:
        if b["date"] >= xd3m:
            spy_exit = b
            break
    if not spy_entry or not spy_exit:
        continue

    spy_ret = (spy_exit["c"] - spy_entry["c"]) / spy_entry["c"]
    exc_ret = raw_ret - spy_ret

    # 判定 hit / miss
    if direction == "long":
        hit = exc_ret > 0
    elif direction == "short":
        hit = exc_ret < 0  # short 做空,excess < 0 算 hit
    else:
        hit = False

    status = "resolved_hit" if hit else "resolved_miss"

    # 更新 DB
    c.execute("""
        UPDATE verifications SET
            h_3m_status=?, h_3m_exit_date=?, h_3m_exit_price=?,
            h_3m_raw_return=?, h_3m_excess_return=?
        WHERE prediction_id=?
    """, (status, xd3m, xprice, raw_ret, exc_ret, pid))
    updated += 1

    if p_ticker == "SIVE":
        sive_updates.append({
            "pid": pid, "pub": pub, "edate": edate, "eprice": eprice,
            "xd3m": xd3m, "xprice": xprice, "raw": raw_ret, "exc": exc_ret, "status": status
        })

conn.commit()
print(f"\n更新了 {updated} 条")

print(f"\n=== SIVE 3m 更新 ({len(sive_updates)} 条) ===")
print(f"{'pub':12s} {'edate':12s} {'entry':8s} {'exit_date':12s} {'exit':8s} {'raw':8s} {'exc':8s} {'status':12s}")
for u in sive_updates[:20]:
    print(f"  {u['pub'][:10]} {u['edate']} ${u['eprice']:.4f} {u['xd3m']} ${u['xprice']:.4f} {u['raw']*100:+6.1f}% {u['exc']*100:+6.1f}% {u['status']}")

if sive_updates:
    import statistics
    raws = [u['raw']*100 for u in sive_updates]
    excs = [u['exc']*100 for u in sive_updates]
    hits = sum(1 for u in sive_updates if u['status'] == 'resolved_hit')
    print(f"\nSIVE 3m 已 resolve: n={len(sive_updates)} hit={hits} hit_rate={hits/len(sive_updates)*100:.1f}%")
    print(f"  raw median: {statistics.median(raws):+.2f}% / avg: {statistics.mean(raws):+.2f}%")
    print(f"  excess median: {statistics.median(excs):+.2f}% / avg: {statistics.mean(excs):+.2f}%")
    print(f"  max: {max(excs):+.2f}% / min: {min(excs):+.2f}%")

conn.close()
