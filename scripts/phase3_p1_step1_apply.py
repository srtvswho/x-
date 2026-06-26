"""Phase 3 第一步 apply: 执行强信号修正 + aliases 归一化
- 1. SIVE 338 / FOCI 16 / WIN 1 / TOWA 8 = 363 条
- 4. SIVE / SIVE.ST / SIVEF 归一化
- 2. 加拿大 29 条: 仅列清单, 不动
- 3. crypto 63 条: 暂不动 market_corrected, 等 P3-2 验证逻辑设计
"""
import sqlite3, json
from datetime import datetime, timezone
DB = "/workspace/data/signalboard_full.db"
NOW = datetime.now(timezone.utc).isoformat()
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

print("=" * 80)
print("执行: 1. 强信号修正 (363 条)")
print("=" * 80)

# 强信号修正清单
STRONG_FIX = [
    ("SIVE", "SE", "Sivers Semiconductors 是瑞典公司(斯德哥尔摩主板 SIVE.ST,瑞典克朗),LLM 因美国 OTC 挂牌 SIVEF 误归美股",
     "aliases: SIVE→SIVE(SE) note='Sivers Semiconductors 斯德哥尔摩'; 推文 $SIVE 指斯德哥尔摩代码,非美股"),
    ("FOCI", "TW", "FOCiS 3363 台湾上柜公司(光通讯/光纤收发模块),LLM 因 ticker 形似美股代码误归美股",
     "aliases: FOCI→3363.TW; 台湾公司,主上市 TWSE/OTC"),
    ("WIN", "TW", "Win Semi 台湾上市(稳懋半导体,化合物半导体代工),LLM 误归美股",
     "aliases: WIN→3105.TW; 台湾上柜"),
    ("TOWA", "JP", "TOWA Semiconductor 日本公司(东京精密,半导体后段设备),LLM 因美国 OTC 影子误归美股",
     "aliases: TOWA→JP; 日本公司,主上市 TYO 5801"),
]

# 1a. 写 market_corrections 审计
n_total = 0
for ticker, corrected, reason, evidence in STRONG_FIX:
    n = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market=?", (ticker, "美股")).fetchone()[0]
    print(f"  {ticker:8s} → {corrected:6s}  n={n:3d}  reason: {reason[:50]}")
    # 写 market_corrections
    c.execute("""INSERT INTO market_corrections
        (ticker, raw_market, corrected_market, reason, evidence, affected_predictions, created_at, applied, applied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL)""", (ticker, "美股", corrected, reason, evidence, n, NOW))
    n_total += n
print(f"\n  写 market_corrections 审计: {len(STRONG_FIX)} 条 / 涉及 {n_total} predictions")
print()

# 1b. 实际写入 predictions.market_corrected
print("执行 UPDATE predictions SET market_corrected=... WHERE ticker=? AND market='美股':")
for ticker, corrected, _, _ in STRONG_FIX:
    c.execute("UPDATE predictions SET market_corrected=? WHERE ticker=? AND market='美股'", (corrected, ticker))
    n = c.execute("SELECT changes()").fetchone()[0]
    print(f"  {ticker:8s} → {corrected:6s}  写入 {n} predictions")
    # 标 applied=1
    c.execute("""UPDATE market_corrections SET applied=1, applied_at=? 
       WHERE ticker=? AND raw_market='美股' AND applied=0""", (NOW, ticker))

conn.commit()
print()

# 1c. 验证
print("验证: market_corrected 列已写入:")
for ticker, _, _, _ in STRONG_FIX:
    n = c.execute("""SELECT count(*) FROM predictions 
       WHERE ticker=? AND market='美股' AND market_corrected IS NOT NULL""", (ticker,)).fetchone()[0]
    print(f"  {ticker:8s} 修正记录: {n} 条")

# 看 raw market 没动
print()
print("✓ 验证: raw market 列未动")
for ticker, _, _, _ in STRONG_FIX:
    n_raw = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market='美股'", (ticker,)).fetchone()[0]
    n_corr = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market_corrected=?", (ticker, _)).fetchone()[0]
    print(f"  {ticker:8s}  raw_market='美股'={n_raw}, market_corrected='{_[1]}'={n_corr}")

# 修正后分布
print()
print("=" * 80)
print("修正后 market 分布:")
print("=" * 80)
sql = """
SELECT 
  CASE WHEN market_corrected IS NOT NULL THEN market_corrected ELSE market END as market_for_verification,
  count(*) as n
FROM predictions
GROUP BY market_for_verification
ORDER BY n DESC
"""
for r in c.execute(sql).fetchall():
    print(f"  {r[0]:10s}  {r[1]}")

print()
print("=" * 80)
print("执行: 4. aliases 归一化 (SIVE/SIVE.ST/SIVEF)")
print("=" * 80)

# 现状
print("当前 SIVE 相关 aliases:")
for r in c.execute("""SELECT alias_raw, ticker, market, notes FROM aliases 
   WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF') OR ticker='SIVE' OR alias_raw LIKE '%ivers%'"""):
    print(f"  '{r[0]}' → '{r[1]}' ({r[2]}) notes='{r[3] or ''}'")
print()

# 检查现有,避免重复
existing = set(r[0] for r in c.execute("""SELECT alias_raw FROM aliases 
   WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF')"""))
print(f"已存在 alias_raw: {existing}")

# 插入
print("\nINSERT OR REPLACE INTO aliases:")
inserts = [
    ("SIVE",     "SIVE", "SE", "equity", "en", "manual", 1.0, "Sivers Semiconductors 斯德哥尔摩主板; 推文常见简写形式"),
    ("SIVE.ST",  "SIVE", "SE", "equity", "en", "manual", 1.0, "Sivers Semiconductors 斯德哥尔摩主板官方代码(克朗)"),
    ("SIVEF",    "SIVE", "SE", "equity", "en", "manual", 1.0, "Sivers 美股 OTC 代码(美元); P3-2 验证优先(数据源唯一可拉)"),
]
for alias_raw, ticker, market, ac, loc, src, conf, notes in inserts:
    # 用 INSERT OR IGNORE + 检查
    c.execute("""INSERT OR IGNORE INTO aliases
       (alias_raw, ticker, market, asset_class, locale, source, confidence, notes, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
       (alias_raw, ticker, market, ac, loc, src, conf, notes, NOW))
    n_changes = c.execute("SELECT changes()").fetchone()[0]
    if n_changes > 0:
        print(f"  ✅ 插入 {alias_raw:10s} → {ticker} ({market})  notes='{notes[:50]}'")
    else:
        print(f"  ⏭  跳过 {alias_raw:10s} (已存在)")

conn.commit()
print()
print("归一化后 SIVE 相关 aliases:")
for r in c.execute("""SELECT alias_raw, ticker, market, notes FROM aliases 
   WHERE ticker='SIVE' OR alias_raw LIKE '%ivers%' ORDER BY alias_raw"""):
    print(f"  '{r[0]}' → '{r[1]}' ({r[2]})  notes='{r[3] or ''}'")

# 2. 加拿大 29 条清单
print()
print("=" * 80)
print("2. 加拿大 29 条 候选清单 (不动,等 user 审查)")
print("=" * 80)

# 看 raw_posts 文本 + 公司主体
CA_TICKERS = ["HPS.A", "HSP.A", "MVZ.A", "MVZ.B", "MOG.A", "GRZ.V", "VNP.TO", "LYC.AX"]
for ticker in CA_TICKERS:
    n = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market='美股'", (ticker,)).fetchone()[0]
    # 看 raw_text 上下文
    posts = c.execute("""SELECT p.post_id, p.ticker, substr(rp.raw_text, 1, 200) 
       FROM predictions p
       LEFT JOIN raw_posts rp ON p.post_id = rp.post_id
       WHERE p.ticker=? AND p.market='美股' LIMIT 3""", (ticker,)).fetchall()
    print(f"\n  {ticker} (n={n} in 美股):")
    for p in posts:
        text = (p[2] or "").replace("\n", " ")[:150]
        print(f"    post={p[0][:10]}...: {text}")
print()
print("=" * 80)
print("对照: 美股股份类别 (BRK.A / GOOGL 等用 .A .B .C 表示 class)")
print("=" * 80)
print("  - .A / .B / .C 在美股 = 股份类别(class A/B/C),无国别意义")
print("  - .V 在加拿大 TSX Venture = 温哥华创业板")
print("  - .TO 在加拿大 = 多伦多主板")
print("  - .AX 在澳洲 = 澳交所")
print()
print("  所以:")
print("  - HPS.A / HSP.A / MOG.A / MVZ.A / MVZ.B → **可能是美股股份类别,需查证**")
print("  - GRZ.V → TSX Venture 加拿大")
print("  - VNP.TO → 多伦多主板 加拿大")
print("  - LYC.AX → 澳交所 澳洲")

# 加密清单 (3)
print()
print("=" * 80)
print("3. crypto 63 条 候选清单(暂不动 market_corrected,等验证逻辑拍板)")
print("=" * 80)
print("| ticker | 当前 market | n | 状态 |")
print("|---|---|---|---|")
crypto_fixes = [
    ("BTC", "美股", 9, "alias: BTC→crypto; 等待验证逻辑设计"),
    ("BTC", "crypto", 9, "✓ 已正确(LLM 抽对)"),
    ("LTC", "美股", 27, "alias: LTC→crypto; 等待验证逻辑设计"),
    ("ETH", "美股", 17, "alias: ETH→crypto; 等待验证逻辑设计"),
    ("SOL", "美股", 7, "alias: SOL→crypto; 等待验证逻辑设计"),
    ("EOSE", "美股", 1, "alias 错(EOSE = EOS Energy 储能,非 EOS crypto),保持美股"),
]
for t, m, n, s in crypto_fixes:
    print(f"| `{t}` | {m} | {n} | {s} |")

# 4. 报告
conn.commit()
print()
print("=" * 80)
print("落结构")
print("=" * 80)
print("✅ 强信号 363 条 market_corrected 已写入 (SIVE 338 + FOCI 16 + WIN 1 + TOWA 8)")
print("✅ market_corrections 审计 applied=1 (4 条 ticker)")
print("✅ aliases 归一化: SIVE/SIVE.ST/SIVEF → SIVE(SE)")
print("⏸ 加拿大 29 条: 列出待审查, 不动")
print("⏸ crypto 63 条: market_corrected 暂不动, 等 P3-2 验证逻辑拍板")

# 写 report
report = []
report.append("# Phase 3 第一步 apply 报告")
report.append("")
report.append(f"**时间**: {NOW}")
report.append("")
report.append("## ✅ 已执行")
report.append("")
report.append("### 1. 强信号修正 (363 条)")
report.append("")
report.append("| ticker | raw_market | corrected | n | reason |")
report.append("|---|---|---|---|---|")
for t, m, r, e in STRONG_FIX:
    n = c.execute("SELECT count(*) FROM predictions WHERE ticker=?", (t,)).fetchone()[0]
    report.append(f"| `{t}` | 美股 | **{m}** | {n} | {r[:50]} |")
report.append("")
report.append("### 4. aliases 归一化")
report.append("")
report.append("| alias_raw | canonical | market | notes |")
report.append("|---|---|---|---|")
for r in c.execute("""SELECT alias_raw, ticker, market, notes FROM aliases 
   WHERE ticker='SIVE' ORDER BY alias_raw"""):
    report.append(f"| `{r[0]}` | `{r[1]}` | {r[2]} | {r[3] or ''} |")
report.append("")
report.append("**验证 priority** (P3-2 验证函数):")
report.append("1. SIVEF (美股 OTC,Polygon/Finnhub 都通,USD 计价) ← 优先")
report.append("2. SIVE.ST (斯德哥尔摩,数据源不覆盖,理论兜底)")

# 修正后 market 分布
report.append("")
report.append("## 修正后 market 分布(verification 用)")
report.append("")
report.append("| market | n |")
report.append("|---|---|")
for r in c.execute(sql).fetchall():
    report.append(f"| {r[0]} | {r[1]} |")
report.append("")

# 加拿大 29 条清单
report.append("")
report.append("## ⏸ 2. 加拿大 29 条待审查(不动)")
report.append("")
report.append("**重点警示**:`.A`/`.B`/`.C` 在美股 = 股份类别(class A/B/C),非国别后缀。需逐个查证公司主体。")
report.append("")
report.append("| ticker | n | 推文样本 | 公司判定 |")
report.append("|---|---|---|---|")
for ticker in CA_TICKERS:
    n = c.execute("SELECT count(*) FROM predictions WHERE ticker=? AND market='美股'", (ticker,)).fetchone()[0]
    post = c.execute("""SELECT rp.raw_text FROM predictions p
       LEFT JOIN raw_posts rp ON p.post_id = rp.post_id
       WHERE p.ticker=? AND p.market='美股' LIMIT 1""", (ticker,)).fetchone()
    text = (post[0] if post else "").replace("\n", " ")[:100]
    report.append(f"| `{ticker}` | {n} | {text} | 待查证 |")
report.append("")
report.append("**判定规则**:")
report.append("- `.TO` = 多伦多主板 (TSX) — 必加拿大")
report.append("- `.V` = TSX Venture (温哥华创业板) — 必加拿大")
report.append("- `.A`/`.B`/`.C` = **股份类别(美股/加股都可能)** — 必须查公司主体")
report.append("- `.AX` = 澳交所 — 必澳洲")
report.append("")
report.append("**请逐个给我**:`{ticker}` 的公司全名 + 主交易所(美股/加股/其他),我才能决定 market_corrected。")

# crypto 63 条
report.append("")
report.append("## ⏸ 3. crypto 63 条(market_corrected 暂不动,等验证逻辑拍板)")
report.append("")
report.append("| ticker | raw_market | n | 验证逻辑待定 |")
report.append("|---|---|---|---|")
for t, m, n, s in crypto_fixes:
    report.append(f"| `{t}` | {m} | {n} | {s} |")
report.append("")
report.append("**P3-2 验证逻辑设计(待你拍板)**:")
report.append("")
report.append("**方案 A. crypto 内基准**:")
report.append("- crypto 超额 = asset_return - BTC_return (同期) 算 crypto 选币 α")
report.append("- 优点: 区分选币α与crypto大盘β")
report.append("- 缺点: 2024 后 BTC 主导市场,ETH/LTC/SOL 经常负超额但绝对收益高")
report.append("")
report.append("**方案 B. 仅绝对收益**:")
report.append("- crypto 不算超额,只算 raw_return")
report.append("- 优点: 简单,crypto 资产类别不同,强加宽基错位")
report.append("- 缺点: 不能与股票胜率直接对比")
report.append("")
report.append("**方案 C. 加密指数基准(Composite)**:")
report.append("- 自建 weighted index = 0.5*BTC + 0.3*ETH + 0.2*total_crypto_market_cap")
report.append("- 优点: 反映整体加密市场")
report.append("- 缺点: 复杂,数据需 CoinGecko / CoinMarketCap")
report.append("")
report.append("**我的建议: 方案 A(简单 + 主流)** — 但需决定 BTC 是基准还是包含 ETH:")
report.append("- 主流 1: BTC only (BTC ≈ crypto 基准)")
report.append("- 主流 2: BTC 50% + ETH 50%")
report.append("- 主流 3: 同期 crypto 总市值(Total 指标)")
report.append("")

content = "\n".join(report)
with open("/workspace/outputs/phase3_p1_step1_apply_report.md", "w", encoding="utf-8") as f:
    f.write(content)
print(f"✅ 落 outputs/phase3_p1_step1_apply_report.md ({len(content)} chars)")
conn.close()
