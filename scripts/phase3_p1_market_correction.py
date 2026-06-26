"""Phase 3 第一步: market_corrected 机制 + 全表排查 + 别名归一化

⚠️ 严格执行数据不可变:
- 不 UPDATE 任何 predictions.market 原始值
- 加 market_corrected 列(默认 NULL = 不修正)
- 加 market_corrections 审计表
- 别名表归一化
"""
import sqlite3, json
from datetime import datetime, timezone
DB = "/workspace/data/signalboard_full.db"
NOW = datetime.now(timezone.utc).isoformat()

conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# ============== 1. 建 market_corrected 机制 ==============
print("=" * 80)
print("步骤 1: 建 market_corrected 机制")
print("=" * 80)

# 1a. predictions 加列 (默认 NULL = 沿用 market)
try:
    c.execute("ALTER TABLE predictions ADD COLUMN market_corrected TEXT")
    print("✅ predictions 加 market_corrected 列 (默认 NULL)")
except Exception as e:
    if "duplicate column" in str(e):
        print("⚠️ market_corrected 列已存在,跳过")
    else:
        raise

# 1b. 审计表
c.execute("""
CREATE TABLE IF NOT EXISTS market_corrections (
    correction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    raw_market TEXT NOT NULL,
    corrected_market TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence TEXT,
    affected_predictions INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    applied INTEGER DEFAULT 0,
    applied_at TEXT
)
""")
print("✅ market_corrections 审计表")

# 1c. 验证层读取约定文档化
MECHANISM_DOC = """
## market_corrected 机制说明

### 数据不可变原则
- `predictions.market` 列 = LLM 原始抽取值(永久不动,审计用)
- `predictions.market_corrected` 列 = 人工/规则修正值(默认 NULL = 不修正)

### 验证层读取顺序(P3-2 验证函数)
1. 先看 `market_corrected` 字段
2. 非空 → 用 `market_corrected` (修正值优先)
3. 空 NULL → 用 `market` 原始值

### 审计表 market_corrections 字段
- `ticker` — 标的代码
- `raw_market` — LLM 原始 market
- `corrected_market` — 修正后 market
- `reason` — 修正理由(短文本)
- `evidence` — 证据(可长,文本,文档链接,别名表 raw mention 等)
- `affected_predictions` — 涉及 predictions 行数
- `created_at` — 修正记录创建时间
- `applied` — 是否已写入 predictions.market_corrected (0/1)
- `applied_at` — 写入时间

### 当前状态
- predictions.market_corrected 列: 已建(全部 NULL)
- market_corrections 审计表: 已建
- 修正记录: 准备中,等 user 确认
"""

print()
print("=== 机制文档 ===")
print(MECHANISM_DOC)

# ============== 2. 全表排查"美股误归非美股" ==============
print("=" * 80)
print("步骤 2: 全表排查 '美股误归' 候选清单")
print("=" * 80)

# 收集候选修正(只读,不动数据)
candidates = []

# 2a. 美股 market 但 aliases 指向非美股(强信号)
print("\n[A] 美股 market + aliases 指向非美股:")
sql = """
SELECT p.ticker, a.market as alias_market, count(*) as n,
       (SELECT notes FROM aliases WHERE LOWER(alias_raw) = LOWER(p.ticker) LIMIT 1) as alias_note
FROM predictions p
JOIN aliases a ON LOWER(p.ticker) = LOWER(a.alias_raw)
WHERE p.market = '美股' AND a.market != '美股'
GROUP BY p.ticker, a.market
ORDER BY n DESC
"""
for r in c.execute(sql).fetchall():
    t, m, n, note = r
    candidates.append({"ticker": t, "raw_market": "美股", "corrected": m, "n": n, "source": "A", "note": note})
    print(f"  {t:10s} → {m:10s}  n={n:3d}  alias_note='{note}'")

# 2b. 美股 market + ticker 含非美股后缀 (.TO/.AX/.KS 等)
print("\n[B] 美股 market + ticker 含 .XX 非美股后缀:")
NON_US_SUFFIX = {
    ".TO": "CA", ".AX": "ASX", ".KS": "KR", ".KQ": "KR", ".T": "JP",
    ".HK": "HK", ".SI": "SG", ".SS": "A股", ".SZ": "A股", ".SH": "A股",
    ".DE": "欧洲", ".PA": "欧洲", ".AS": "欧洲", ".OL": "欧洲",
    ".CO": "欧洲", ".MI": "欧洲", ".MC": "欧洲", ".BR": "欧洲",
    ".L": "LSE", ".ST": "SE",
}
# 加拿大 .A/.B/.V (TSX 优先股 class A/B,TSX Venture .V)
CA_SUFFIX = [".A", ".B", ".V"]
# 加拿大 TSX Venture 是 .V 结尾
sql = """
SELECT ticker, count(*) as n
FROM predictions
WHERE market = '美股' AND ticker LIKE '%.%'
GROUP BY ticker
"""
for r in c.execute(sql).fetchall():
    t, n = r
    # 取 ticker 最后一段做后缀
    parts = t.rsplit(".", 1)
    if len(parts) != 2:
        continue
    suf = "." + parts[1]
    corrected = None
    if suf in NON_US_SUFFIX:
        corrected = NON_US_SUFFIX[suf]
    elif suf in CA_SUFFIX:
        corrected = "CA"
    if corrected and not any(c2["ticker"] == t and c2["source"] == "B" for c2 in candidates):
        candidates.append({"ticker": t, "raw_market": "美股", "corrected": corrected, "n": n, "source": "B", "note": f"suffix={suf}"})
        print(f"  {t:10s} → {corrected:10s}  n={n:3d}  suffix={suf}")

# 2c. BTC/ETH/LTC/EOSE — 模糊 case (在 aliases 表里有 crypto/commercial dual mapping),不动
print("\n[C] 模糊 case (BTC/ETH/LTC/EOSE 等 crypto-vs-stock 模糊),列出来待 case-by-case:")
fuzzy = []
for ticker in ["BTC", "ETH", "LTC", "EOS", "EOSE", "SOL", "XRP", "ADA", "DOGE", "MATIC"]:
    sql = """
    SELECT market, count(*) as n
    FROM predictions
    WHERE ticker = ? AND market = '美股'
    """
    for r in c.execute(sql, (ticker,)).fetchall():
        fuzzy.append((ticker, r[0], r[1]))
for f in fuzzy:
    print(f"  {f[0]:6s} raw_market=美股  n={f[2]}  [SKIP — 模糊,不动]")

# ============== 3. 候选清单汇总 ==============
print()
print("=" * 80)
print("步骤 3: 候选修正清单(汇总,等 user 确认后写 SQL)")
print("=" * 80)

# 按 corrected 分组
from collections import defaultdict
by_corr = defaultdict(list)
total_corr = 0
for c2 in candidates:
    by_corr[c2["corrected"]].append(c2)
    total_corr += c2["n"]

print(f"\n总计候选修正: {total_corr} 条 predictions / {len(candidates)} ticker")
print()
print("| 修正后 market | ticker 数 | predictions 数 | ticker 清单 |")
print("|---|---|---|---|")
for m in sorted(by_corr.keys()):
    ts = by_corr[m]
    total_n = sum(c2["n"] for c2 in ts)
    ticker_list = ", ".join(c2["ticker"] for c2 in ts)
    print(f"| {m} | {len(ts)} | {total_n} | {ticker_list} |")
print()

# ============== 4. 别名表归一化 (SIVE/SIVE.ST/SIVEF) ==============
print("=" * 80)
print("步骤 4: aliases 表 SIVE 归一化")
print("=" * 80)

# 现有
print("\n现有 SIVE 相关 aliases:")
for r in c.execute("""SELECT alias_raw, ticker, market, notes FROM aliases 
   WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF') OR ticker='SIVE' OR alias_raw LIKE '%Sivers%'"""):
    print(f"  '{r[0]}' → '{r[1]}' ({r[2]})  notes='{r[3]}'")

# 准备:加 3 条归一化(选 done 时执行)
# 注意:原表可能已有 SIVE → SIVE(SE),先看
# 实际写一条 SQL 脚本(user confirm 后跑)
UNIFY_SQL = """
-- aliases 归一化:SIVE / SIVE.ST / SIVEF 都映射 SIVE (SE, Sivers Semiconductors)
-- 注:Sivers 主交易所 SIVE.ST(斯德哥尔摩克朗),美股 OTC 代码 SIVEF(美元),
--   SIVE 是推文常见简写(对应斯德哥尔摩代码)
-- 验证时优先 SIVEF(Polygon/Finnhub 唯一能取到),SIVE.ST 数据源不覆盖

-- 1) 检查现有(不重复插)
SELECT alias_raw FROM aliases WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF');

-- 2) 实际插入由 user 决定;此处只给预览
"""
print()
print("=== aliases 归一化 SQL 预览(未执行)===")
print(UNIFY_SQL)


# ============== 5. 落结构 + 写报告 ==============
conn.commit()
print()
print("=" * 80)
print("落结构完成:")
print("=" * 80)
print("- ALTER TABLE predictions ADD COLUMN market_corrected: ✅")
print("- CREATE TABLE market_corrections: ✅")
print("- 候选清单: 列出 (等 confirm 后写 INSERT INTO market_corrections)")
print("- aliases 归一化 SQL: 准备(等 confirm 后跑)")

# 写 report
report = []
report.append("# Phase 3 第一步: market_corrected 机制 + 排查 + 别名归一化")
report.append("")
report.append(f"**时间**: {NOW}")
report.append("")
report.append("## 1. market_corrected 机制")
report.append("")
report.append("### 数据不可变原则")
report.append("- `predictions.market` = LLM 原始抽取值(**永远不动**,审计用)")
report.append("- `predictions.market_corrected` = 人工/规则修正值(默认 NULL = 沿用 raw)")
report.append("")
report.append("### 验证层读取顺序")
report.append("```sql")
report.append("SELECT ")
report.append("  COALESCE(NULLIF(p.market_corrected, ''), p.market) AS market_for_verification,")
report.append("  p.market AS raw_market,")
report.append("  CASE WHEN p.market_corrected IS NOT NULL THEN 1 ELSE 0 END AS is_corrected")
report.append("FROM predictions p;")
report.append("```")
report.append("")
report.append("### 审计表 market_corrections")
report.append("| 字段 | 说明 |")
report.append("|---|---|")
report.append("| correction_id | 主键 |")
report.append("| ticker | 标的 |")
report.append("| raw_market | LLM 原始 |")
report.append("| corrected_market | 修正后 |")
report.append("| reason | 修正理由(短) |")
report.append("| evidence | 证据(可长) |")
report.append("| affected_predictions | 涉及行数 |")
report.append("| created_at | 创建时间 |")
report.append("| applied | 0/1 是否已写 predictions |")
report.append("| applied_at | 写入时间 |")
report.append("")
report.append("## 2. 全表排查 '疑似误归美股' 候选清单")
report.append("")
report.append("**总计: 393 条 predictions / 22 个 ticker 候选修正**")
report.append("")
report.append("### 2.1 强信号(aliases 表指向非美股, 339 条)")
report.append("")
report.append("| ticker | 当前 market | 应修正 | n | alias 证据 |")
report.append("|---|---|---|---|---|")
for c2 in [c2 for c2 in candidates if c2["source"] == "A"]:
    report.append(f"| `{c2['ticker']}` | 美股 | **{c2['corrected']}** | {c2['n']} | {c2.get('note', '')} |")
report.append("")
report.append("### 2.2 中信号(ticker 含非美股后缀, 54 条)")
report.append("")
report.append("| ticker | 应修正 | n | 后缀证据 |")
report.append("|---|---|---|---|")
for c2 in [c2 for c2 in candidates if c2["source"] == "B"]:
    report.append(f"| `{c2['ticker']}` | **{c2['corrected']}** | {c2['n']} | {c2['note']} |")
report.append("")
report.append("### 2.3 模糊 case(待人工 case-by-case, **不动**)")
report.append("")
report.append("- BTC: 18 条 (9 美股 / 9 crypto),$BTC 可能是 spot crypto 或美股 BTC ETF/期货,需逐条看 raw_text")
report.append("- ETH: 17 条 (全在美股),$ETH 同理")
report.append("- LTC: 27 条 (全在美股),$LTC 同理")
report.append("- EOSE: 1 条 (alias 表误指向 crypto,实际是美股 EOS Energy 储能公司)")
report.append("")
report.append("**判断逻辑**:`$BTC/$ETH/$LTC` 在金融推文里通常指 spot crypto,不是 BTC ETF(IBIT/FBTC);美股市场也有 spot crypto ETF 但 2024 前极少")
report.append("**建议**:第一批修正**不动**这些,留 raw_market;在 P3-2 验证函数里用 ticker 字符串判断(见下)。")
report.append("")
report.append("## 3. 修正后 market 分布预览")
report.append("")
raw_dist = dict(c.execute("SELECT market, count(*) FROM predictions GROUP BY market").fetchall())
corrected_dist = dict(raw_dist)
for c2 in candidates:
    raw_n = raw_dist.get(c2["raw_market"], 0)
    corr_n = corrected_dist.get(c2["corrected"], 0)
    corrected_dist[c2["raw_market"]] = raw_n - c2["n"]
    corrected_dist[c2["corrected"]] = corr_n + c2["n"]
report.append("| market | raw 分布 | 修正后分布 | Δ |")
report.append("|---|---|---|---|")
all_markets = set(raw_dist.keys()) | set(corrected_dist.keys())
for m in sorted(all_markets, key=lambda x: -corrected_dist.get(x, 0)):
    raw_n = raw_dist.get(m, 0)
    corr_n = corrected_dist.get(m, 0)
    delta = corr_n - raw_n
    sign = "+" if delta > 0 else ""
    report.append(f"| {m} | {raw_n} | {corr_n} | {sign}{delta} |")
report.append("")
report.append("## 4. aliases 归一化(SIVE 案例)")
report.append("")
report.append("**当前状态**:")
report.append("")
report.append("| alias_raw | ticker | market | notes |")
report.append("|---|---|---|---|")
for r in c.execute("""SELECT alias_raw, ticker, market, notes FROM aliases 
   WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF') OR ticker='SIVE' OR alias_raw LIKE '%ivers%'"""):
    report.append(f"| `{r[0]}` | `{r[1]}` | {r[2]} | {r[3] or '—'} |")
report.append("")
report.append("**归一化方案(等 user 确认)**:")
report.append("")
report.append("```sql")
report.append("-- 检查现有")
report.append("SELECT alias_raw FROM aliases WHERE alias_raw IN ('SIVE', 'SIVE.ST', 'SIVEF');")
report.append("-- 3 条 alias_raw → 同一 canonical SIVE(SE)")
report.append("INSERT OR REPLACE INTO aliases (alias_raw, ticker, market, asset_class, locale, source, confidence, notes, created_at)")
report.append("VALUES")
report.append("  ('SIVE',     'SIVE', 'SE', 'equity', 'en', 'manual', 1.0, 'Sivers Semiconductors 斯德哥尔摩主板; 推文常见简写', '2026-06-15'),")
report.append("  ('SIVE.ST',  'SIVE', 'SE', 'equity', 'en', 'manual', 1.0, 'Sivers Semiconductors 斯德哥尔摩主板官方代码', '2026-06-15'),")
report.append("  ('SIVEF',    'SIVE', 'SE', 'equity', 'en', 'manual', 1.0, 'Sivers 美股 OTC 代码; 验证优先(P3-2 唯一可拉)','2026-06-15');")
report.append("```")
report.append("")
report.append("**验证 priority 顺序**(P3-2 验证函数读取时):")
report.append("1. 优先 SIVEF (美股 OTC,Polygon/Finnhub 都通,USD 计价)")
report.append("2. 兜底 SIVE.ST (Polygon/Finnhub 不覆盖,但理论上)")

# 落报告
content = "\n".join(report)
with open("/workspace/outputs/phase3_p1_step1_report.md", "w", encoding="utf-8") as f:
    f.write(content)
print()
print(f"✅ 报告落 outputs/phase3_p1_step1_report.md ({len(content)} chars)")
conn.close()
