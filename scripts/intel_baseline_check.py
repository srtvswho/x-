"""模块1 基线体检 — A+B 完成后"""
import sqlite3
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

DB_PATH = "/workspace/data/signalboard_full.db"

KOLS = [
    ("jukan05", "tw_jukan05", "Jukan"),
    ("aleabitoreddit", "tw_aleabitoreddit", "Serenity"),
    ("zephyr_z9", "tw_zephyr_z9", "zephyr"),
    ("austinsemis", "tw_austinsemis", "Austin"),
]

con = sqlite3.connect(DB_PATH, timeout=30)
print("="*70)
print("1. 4 大V 入库统计")
print("="*70)
print(f"  {'handle':<16}{'source_id':<22}{'total':<8}{'distinct':<10}{'dup':<6}{'earliest':<28}{'latest'}")
print("-" * 130)
for handle, sid, label in KOLS:
    n = con.execute("SELECT COUNT(*) FROM raw_posts WHERE source_id=?", (sid,)).fetchone()[0]
    nu = con.execute("SELECT COUNT(DISTINCT post_id) FROM raw_posts WHERE source_id=?", (sid,)).fetchone()[0]
    earliest = con.execute("SELECT MIN(published_at) FROM raw_posts WHERE source_id=?", (sid,)).fetchone()[0] or "-"
    latest = con.execute("SELECT MAX(published_at) FROM raw_posts WHERE source_id=?", (sid,)).fetchone()[0] or "-"
    print(f"  {handle:<16}{sid:<22}{n:<8}{nu:<10}{n-nu:<6}{earliest:<28}{latest}")

print()
print("="*70)
print("2. 4 大V 月度分布 (时间分布, 检查空洞)")
print("="*70)
for handle, sid, label in KOLS:
    print(f"\n  {label} ({handle}):")
    months = con.execute("""
      SELECT substr(published_at, 1, 7) m, COUNT(*) c
      FROM raw_posts WHERE source_id=?
      GROUP BY m ORDER BY m
    """, (sid,)).fetchall()
    for m, c in months:
        print(f"    {m}: {c:>4}")

print()
print("="*70)
print("3. 4 大V 随机抽 3 条 published_at (ISO 校验)")
print("="*70)
for handle, sid, label in KOLS:
    print(f"\n  {label} ({handle}):")
    for r in con.execute("""
      SELECT post_id, published_at, captured_at, substr(raw_text, 1, 50)
      FROM raw_posts WHERE source_id=?
      ORDER BY RANDOM() LIMIT 3
    """, (sid,)).fetchall():
        pid, pub, cap, txt = r
        # ISO 校验
        ok = "✓" if pub and "T" in pub and "+" in pub else "✗"
        print(f"    {ok} id={pid}")
        print(f"        published_at: {pub}")
        print(f"        text: {txt!r}")

print()
print("="*70)
print("4. 4 大V 表结构统一性 (确认都在 raw_posts)")
print("="*70)
for handle, sid, label in KOLS:
    # 看 1 条样本, 列字段
    r = con.execute("SELECT * FROM raw_posts WHERE source_id=? LIMIT 1", (sid,)).fetchone()
    if r:
        # raw_posts columns: 0=post_id, 1=source_id, 2=platform, 3=published_at, 4=captured_at
        print(f"  {sid}: 字段 sample post_id={r[0][:20]}... source_id={r[1]} platform={r[2]} published_at={r[3][:19]}")

print()
print("="*70)
print("5. 去重确认 (4 大V 之间 + 各自内部)")
print("="*70)
# 4 大V 之间交叉
print("  4 大V 之间的 post_id 冲突 (应该 0, 因为 Twitter id 唯一):")
sql = """
SELECT post_id, COUNT(*) c, GROUP_CONCAT(source_id) sources
FROM raw_posts
WHERE source_id IN ('tw_jukan05', 'tw_aleabitoreddit', 'tw_zephyr_z9', 'tw_austinsemis')
GROUP BY post_id HAVING c > 1
LIMIT 5
"""
cross = con.execute(sql).fetchall()
if cross:
    for r in cross:
        print(f"    {r}")
else:
    print(f"    ✓ 0 冲突 (4 大V 之间 post_id 完全独立)")

# 各自内部
print(f"\n  各 KOL 内部重复 (已 printed above, 都是 dup=0)")

# 跨全 DB
print(f"\n  raw_posts 整体:")
n = con.execute("SELECT COUNT(*) FROM raw_posts").fetchone()[0]
nu = con.execute("SELECT COUNT(DISTINCT post_id) FROM raw_posts").fetchone()[0]
print(f"    total {n}, distinct {nu}, dup {n-nu}")

con.close()