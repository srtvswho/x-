"""Phase 3 第一步 buckets: 加拿大/委内瑞拉修正 + price_source_available 标记 + 分桶统计

执行:
1. market_corrected 修正:
   - HPS.A → CA
   - MVZ.A → VE
   - MVZ.B → VE
   - HSP.A → CA (low_confidence, 单独标)
   - GRZ.V → CA
   - VNP.TO → CA
   - LYC.AX → ASX
   - MOG.A 不动 (真美股)

2. 加 price_source_available 列(0/1)
   - true: 美股 + SIVE/SIVEF (走美股 OTC 数据源)
   - false: SE/TW/JP/KR/A股/欧洲/CA/ASX/未上市/commodity/crypto (数据源不覆盖或验证逻辑待定)
   - VE: 委内瑞拉 (新增,数据源不覆盖)

3. 分桶统计
"""
import sqlite3, json
from datetime import datetime, timezone
from collections import Counter, defaultdict
DB = "/workspace/data/signalboard_full.db"
NOW = datetime.now(timezone.utc).isoformat()
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# ============== 1. 加拿大/委内瑞拉 market_corrected 修正 ==============
print("=" * 80)
print("1. 加拿大/委内瑞拉修正")
print("=" * 80)

CORRECTIONS = [
    # (ticker, corrected, reason, evidence, low_confidence)
    ("HPS.A", "CA", "Hammond Power Solutions 加拿大(TSX,加元)",
     "用户查证: 加拿大 TSX 主板 .A 优先股", 0),
    ("MVZ.A", "VE", "Mercantil Servicios Financieros 委内瑞拉(加拉加斯 BVC,玻利瓦尔)",
     "用户查证: 委内瑞拉 BVC,玻利瓦尔", 0),
    ("MVZ.B", "VE", "Mercantil Servicios Financieros B 类股 委内瑞拉(加拉加斯 BVC,玻利瓦尔)",
     "用户查证: 委内瑞拉 BVC,玻利瓦尔", 0),
    ("HSP.A", "CA", "Hammond Power Solutions 关联(可能 A 类,样本仅 1 条存疑)",
     "用户查证: 存疑,样本 1 条,low_confidence", 1),
    ("GRZ.V", "CA", "GreenRise Foods 加拿大(TSX Venture,加元)",
     "用户查证: 加拿大 TSX Venture,委内瑞拉资产", 0),
    ("VNP.TO", "CA", "5N Plus 加拿大(TSX 主板,加元)",
     "用户查证: 多伦多主板,5TP 资源股", 0),
    ("LYC.AX", "ASX", "Lynas Rare Earths 澳洲(ASX,澳元)",
     "用户查证: 澳交所,澳洲稀土", 0),
]

for ticker, corrected, reason, evidence, low_conf in CORRECTIONS:
    n = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market='美股' AND market_corrected IS NULL", (ticker,)).fetchone()[0]
    if n == 0:
        print(f"  ⏭  {ticker:8s} 已有修正, 跳过")
        continue
    c.execute("""INSERT INTO market_corrections
       (ticker, raw_market, corrected_market, reason, evidence, affected_predictions, created_at, applied, applied_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""", (ticker, "美股", corrected, reason, evidence, n, NOW, NOW))
    c.execute("UPDATE predictions SET market_corrected=? WHERE ticker=? AND market='美股'", (corrected, ticker))
    n_done = c.execute("SELECT changes()").fetchone()[0]
    lc_mark = " [low_confidence]" if low_conf else ""
    print(f"  ✅ {ticker:8s} → {corrected:6s}  n={n_done}{lc_mark}")

# 不动的(MOG.A)不写 market_corrections
print()
n_mog = c.execute("SELECT count(*) FROM predictions WHERE ticker='MOG.A' AND market='美股'").fetchone()[0]
print(f"  ⏸  MOG.A   不动 (真美股 Moog Inc NYSE 双类股)  n={n_mog}")

conn.commit()
print()

# ============== 2. price_source_available 标记 ==============
print("=" * 80)
print("2. price_source_available 标记")
print("=" * 80)

# 2a. 加列
try:
    c.execute("ALTER TABLE predictions ADD COLUMN price_source_available INTEGER")
    print("✅ 加 price_source_available 列")
except Exception as e:
    if "duplicate column" in str(e):
        print("⏭  price_source_available 列已存在")
    else:
        raise

# 2b. 定义规则
# 可验证(price_source_available=1): 美股 + SIVE/SIVEF (走美股 OTC 路径)
# 不可验证(=0): 其他所有 market
DATA_AVAILABLE = {"美股"}
# 特例 ticker (market_corrected 不是 '美股' 但 SIVEF 走美股 OTC):
SPECIAL_TICKERS_AVAILABLE = {"SIVE", "SIVEF"}  # SIVE 在 raw_market=SE 时也可(8 条 SE)

# 不可验证 market
NOT_AVAILABLE_MARKETS = {
    "SE", "TW", "KR", "JP", "A股", "欧洲", "CA", "ASX", "LSE", "HK", "SG",
    "VE", "未上市", "crypto", "commodity",
}

# 2c. UPDATE
# 实际可用 = market_for_verification == '美股' OR ticker in SPECIAL_TICKERS_AVAILABLE
# market_for_verification = COALESCE(NULLIF(market_corrected, ''), market)
c.execute("""
UPDATE predictions 
SET price_source_available = CASE
  WHEN COALESCE(NULLIF(market_corrected, ''), market) = '美股' THEN 1
  WHEN ticker IN ('SIVE', 'SIVEF') THEN 1
  ELSE 0
END
""")
n_updated = c.execute("SELECT changes()").fetchone()[0]
print(f"  ✅ UPDATE 完成, 影响 {n_updated} 行")
conn.commit()

# 2d. 验证
print()
print("price_source_available 状态:")
for r in c.execute("""
SELECT price_source_available, 
       COALESCE(NULLIF(market_corrected, ''), market) as m,
       count(*) as n
FROM predictions
GROUP BY price_source_available, m
ORDER BY price_source_available, n DESC
"""):
    print(f"  available={r[0]}  market={r[1]:10s}  n={r[2]}")

# ============== 3. 分桶统计 ==============
print()
print("=" * 80)
print("3. 可验证 vs 不可验证 分桶统计")
print("=" * 80)

# 3a. 可验证集
avail = c.execute("""
SELECT p.ticker, count(*) as n,
       COALESCE(NULLIF(p.market_corrected, ''), p.market) as m
FROM predictions p
WHERE p.price_source_available = 1
GROUP BY p.ticker, m
""").fetchall()
n_avail_pred = sum(n for _, n, _ in avail)
n_avail_ticker = len(avail)
print(f"\n### ✅ 可验证集 (price_source_available=1)")
print(f"   predictions: {n_avail_pred}")
print(f"   unique ticker: {n_avail_ticker}")
# 按 market
avail_market = Counter(m for _, _, m in avail)
print(f"   market 分布:")
for m, n in avail_market.most_common():
    print(f"     {m:10s}  {n:4d} predictions")

# 3b. 不可验证集
unavail = c.execute("""
SELECT p.ticker, count(*) as n,
       COALESCE(NULLIF(p.market_corrected, ''), p.market) as m
FROM predictions p
WHERE p.price_source_available = 0
GROUP BY p.ticker, m
""").fetchall()
n_unavail_pred = sum(n for _, n, _ in unavail)
n_unavail_ticker = len(unavail)
print(f"\n### ⏸ 不可验证集 (price_source_available=0)")
print(f"   predictions: {n_unavail_pred}")
print(f"   unique ticker: {n_unavail_ticker}")
unavail_market = Counter(m for _, _, m in unavail)
print(f"   market 分布:")
for m, n in unavail_market.most_common():
    print(f"     {m:10s}  {n:4d} predictions")

# 3c. 总计
print()
print(f"### 总计: {n_avail_pred + n_unavail_pred} predictions (期望 4470)")
n_total = c.execute("SELECT count(*) FROM predictions").fetchone()[0]
print(f"   实际 predictions 总数: {n_total}")

# 3d. 不可验证集的细分原因
print()
print("### 不可验证集细分(按不可达原因)")
unavail_groups = defaultdict(list)
for ticker, n, m in unavail:
    if m in ("SE",) and ticker in ("SIVE", "SIVEF"):
        reason = "已通过美股 OTC 走可验证(price_source_available=1)— 此条不会到这里"
    elif m in ("crypto",):
        reason = "验证逻辑待拍板(方案 A/B/C)"
    elif m in ("commodity",):
        reason = "商品期货代码(GC=F 等),需单独处理"
    elif m in ("TW", "JP", "KR", "A股", "欧洲", "CA", "ASX", "LSE", "HK", "SG"):
        reason = f"Polygon/Finnhub 免费源不覆盖 {m} 交易所"
    elif m in ("SE",) and ticker not in ("SIVE", "SIVEF"):
        reason = "SIVE.ST 斯德哥尔摩数据源不覆盖(无替代)"
    elif m in ("未上市",):
        reason = "私募/未上市,无公开行情"
    elif m in ("VE",):
        reason = "委内瑞拉 BVC,玻利瓦尔,数据源不覆盖"
    else:
        reason = f"未知 market={m}"
    unavail_groups[reason].append((ticker, n, m))

for reason, items in sorted(unavail_groups.items(), key=lambda x: -sum(t[1] for t in x[1])):
    n_pred = sum(t[1] for t in items)
    n_ticker = len(items)
    print(f"  {reason}: {n_pred} pred / {n_ticker} ticker")

# 3e. 第一版记分牌范围建议
print()
print("=" * 80)
print("第一版记分牌范围建议")
print("=" * 80)
print(f"""
# 可验证集 = {n_avail_pred} predictions / {n_avail_ticker} unique ticker
# 第一版记分牌: 跑可验证集 (价格可拉到)
# 不可验证集: 列入 v2 backlog, 标 validation_status=skipped

# 注意: 第一版不是 100%, 因为美股里还有 Finnhub 报 no_quote_data 的 ticker (P3-1 报告里 60 个)
# 实际可拉到日线的, 取决于 Polygon 的覆盖 (P3-1 Finnhub quote 是必要不充分条件)
# 预计 Polygon 美股日线覆盖率 ~95% (即美股 3722 拉 3540 实际可拉)
# P3-2 实际拉日线时会再筛一次
""")

# 写报告
report = []
report.append("# Phase 3 第一步 buckets 报告")
report.append("")
report.append(f"**时间**: {NOW}")
report.append("")
report.append("## 1. 加拿大/委内瑞拉修正(已执行)")
report.append("")
report.append("| ticker | corrected | n | reason | low_confidence |")
report.append("|---|---|---|---|---|")
for ticker, corrected, reason, evidence, low_conf in CORRECTIONS:
    n = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market_corrected=?", (ticker, corrected)).fetchone()[0]
    lc = "✓" if low_conf else ""
    report.append(f"| `{ticker}` | **{corrected}** | {n} | {reason[:50]} | {lc} |")
n_mog = c.execute("SELECT count(*) FROM predictions WHERE ticker='MOG.A' AND market='美股'").fetchone()[0]
report.append(f"| `MOG.A` | (美股,不动) | {n_mog} | Moog Inc NYSE 双类股,真美股 | |")
report.append("")
report.append("## 2. price_source_available 标记")
report.append("")
report.append("### 规则")
report.append("```")
report.append("UPDATE predictions ")
report.append("SET price_source_available = CASE")
report.append("  WHEN COALESCE(NULLIF(market_corrected, ''), market) = '美股' THEN 1")
report.append("  WHEN ticker IN ('SIVE', 'SIVEF') THEN 1")
report.append("  ELSE 0")
report.append("END;")
report.append("```")
report.append("")
report.append("### 状态")
report.append("")
report.append("| available | market | n |")
report.append("|---|---|---|")
for r in c.execute("""
SELECT price_source_available, 
       COALESCE(NULLIF(market_corrected, ''), market) as m,
       count(*) as n
FROM predictions
GROUP BY price_source_available, m
ORDER BY price_source_available, n DESC
"""):
    label = "✅ 可验证" if r[0] == 1 else "⏸ 不可验证"
    report.append(f"| {label} | {r[1]} | {r[2]} |")
report.append("")
report.append("## 3. 分桶统计")
report.append("")
report.append("### ✅ 可验证集 (price_source_available=1)")
report.append("")
report.append(f"**predictions: {n_avail_pred}**")
report.append(f"**unique ticker: {n_avail_ticker}**")
report.append("")
report.append("| market | predictions |")
report.append("|---|---|")
for m, n in avail_market.most_common():
    report.append(f"| {m} | {n} |")
report.append("")
report.append("**全部 ticker 清单** (n_avail_ticker 个):")
report.append("")
tickers_avail = sorted([(t, m) for t, _, m in avail], key=lambda x: -sum(n for tt, n, mm in avail if tt == x[0]))
report.append("```")
for ticker, _ in tickers_avail[:50]:
    n = next(c2 for t, c2, m in avail if t == ticker)
    report.append(f"  {ticker:10s}  n={n}")
report.append(f"  ... (还有 {n_avail_ticker - 50} 个)")
report.append("```")
report.append("")
report.append("### ⏸ 不可验证集 (price_source_available=0)")
report.append("")
report.append(f"**predictions: {n_unavail_pred}**")
report.append(f"**unique ticker: {n_unavail_ticker}**")
report.append("")
report.append("**细分原因**:")
report.append("")
report.append("| 原因 | predictions | ticker |")
report.append("|---|---|---|")
for reason, items in sorted(unavail_groups.items(), key=lambda x: -sum(t[1] for t in x[1])):
    n_pred = sum(t[1] for t in items)
    n_ticker = len(items)
    report.append(f"| {reason} | {n_pred} | {n_ticker} |")
report.append("")
report.append("## 4. 第一版记分牌范围")
report.append("")
report.append(f"- **跑**: {n_avail_pred} predictions / {n_avail_ticker} ticker (price_source_available=1)")
report.append(f"- **跳过(v2 backlog)**: {n_unavail_pred} predictions, validation_status=skipped")
report.append("")
report.append("**注意**:第一版不是 100% 覆盖,美股 3722 预测里还有 Finnhub 报 no_quote_data 的 60 个 ticker (P3-1 报告),Polygon 日线覆盖率预计 ~95%。P3-2 实际拉日线时会再筛一次,具体到单 ticker 不可拉就再 skip。")
report.append("")

content = "\n".join(report)
with open("/workspace/outputs/phase3_p1_step1_buckets_report.md", "w", encoding="utf-8") as f:
    f.write(content)
print(f"✅ 落 outputs/phase3_p1_step1_buckets_report.md ({len(content)} chars)")

# 5. 最终汇总(全 phase3 p3-1 完成状态)
print()
print("=" * 80)
print("Phase 3 第一步最终状态:")
print("=" * 80)
print(f"✅ market_corrected 修正总数: 359 (强信号) + {sum(c.execute('SELECT count(*) FROM predictions WHERE market_corrected IS NOT NULL').fetchone()[0] - 359 for _ in [1])} = 实际={c.execute('SELECT count(*) FROM predictions WHERE market_corrected IS NOT NULL').fetchone()[0]}")
print(f"✅ aliases 归一化: SIVE/SIVE.ST/SIVEF")
print(f"✅ price_source_available 标记完成")
print(f"✅ 可验证集: {n_avail_pred} pred / {n_avail_ticker} ticker")
print(f"⏸ 不可验证集: {n_unavail_pred} pred (v2 backlog)")
conn.close()
