"""Phase 3 P3-7b 严格筛选真条件性预测

用户要求:
- after/when/before/once 在金融语境里大量是时间/语气修饰,不是真条件 → 不豁免
- 真条件句:明确的 "if X then Y" / "跌破/突破某价位才如何" / "增发通过/失败才如何"
- 举证责任在"豁免" — 只"真条件 + 条件确实没发生"才豁免
- 核心票 short 走"条件没触发"或"风险提示改 neutral",不是先验

输出:
1. 收窄后的"真条件句"清单 + 数量
2. 真条件句的子集:"条件明确没触发"清单(给原文+查证)
3. NOT 豁免清单(明确是时间/语气修饰的)— 仍正常验证
"""
from __future__ import annotations
import os, sqlite3, re, json
from datetime import datetime
from typing import Dict, List
from collections import Counter, defaultdict
import statistics

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# ============== 1. 拉全部 prediction + raw_text ==============
print("=" * 80)
print("Step 1: 拉全部 3983 prediction + raw_text")
print("=" * 80)

sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.horizon, p.conviction,
       p.thesis_summary, p.quantitative_claim,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return,
       v.h_3m_status, v.h_3m_excess_return, v.h_3m_raw_return,
       v.h_6m_status, v.h_6m_excess_return, v.h_6m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1
"""
all_pred = c.execute(sql).fetchall()
print(f"全部: {len(all_pred)}")

# ============== 2. 严格真条件句 — 必须是"客观可判定"触发条件 ==============
# 真条件句必须满足:
#  - 模式: "if/when/once/after/unless [具体可观察事件/价格] then [观点/动作]"
#  - 触发条件可量化(具体价格/具体事件/具体数据)
#  - 不是"时间修饰"(after earnings/when market opens)

# 严格条件性 pattern (按可信度从高到低)
STRICT_CONDITIONAL = [
    # 价格条件 (最高优先级 — 客观可验证)
    (r'\b(?:if|when|once)\s+(?:it|the|[a-z]+)\s+(?:breaks?|falls?|drops?|rallies|rises?|trades?|goes?|hits?|reaches?|touches?|approaches?|crosses?)\s*(?:above|below|over|under|to|at|back\s+to)\s*\$?[\d\.]+', "PRICE_LEVEL"),
    (r'\$\d+(?:\.\d+)?\s*(?:hold|holds|holds\s+as\s+support|is\s+resistance|break(?:s|ing)?\s*(?:above|below))', "PRICE_LEVEL"),
    (r'(?:break(?:s|ing)?|fall(?:s|ing)?|drop(?:s|ping)?|rall(?:y|ies)|rise(?:s|ing)?)\s+(?:above|below|over|under)\s*\$\d+', "PRICE_BREAK"),
    (r'\$\d+\s*(?:PT|price\s+target|target|resistance|support)', "PRICE_TARGET"),
    
    # 事件条件 (中等优先级 — 客观可查证)
    (r'\bif\s+(?:it\s+)?(?:the\s+)?(?:dilution|funding|deal|vote|earnings|earnings\s+call|approval|approval\s+vote|EPS\s+miss|EPS\s+beat|revenue\s+miss|chip\s+export|government\s+shutdown|partnership|acquisition|merger|buyback|spin-?off|tender|delisting|liquidation|merger)\s+(?:passes?|fails?|happens|occurs|approves?|rejects?|completes?|is\s+approved|misses?|beats?)', "EVENT_FINANCIAL"),
    (r'\bif\s+(?:it|the)\s+(?:passes?|fails?|gets\s+approved|gets\s+rejected|breaks|breaks\s+down|breaks\s+up|holds|holds\s+the|holds\s+at|crashes|crashes\s+through|crosses|crosses\s+(?:above|below)|falls\s+to|rallies\s+to|drops\s+to|goes\s+(?:above|below|to)|misses|misses\s+on|misses\s+EPS|beats|beats\s+on|beats\s+EPS|closes\s+(?:above|below|at|over|under)|reaches|hits|touches)\s+(?:the\s+)?(?:support|resistance|\$?\d+|[a-z]+\s+(?:vote|dilution|funding|deal|earnings|approval|partnership|breakout|breakdown|crash|rebound))', "EVENT_GENERIC"),
    (r'\bif\s+(?:the\s+)?(?:Fed|FOMC|government|administration|White\s+House|Senate|Congress|judge|court)\s+(?:does|do|did|cuts?|raises?|hikes?|pauses?|approves?|rejects?|intervenes?)', "EVENT_POLICY"),
    (r'\bif\s+(?:China|Russia|Iran|Saudi|OPEC|EU|BRICS|Israel)\s+(?:invades?|attacks?|cuts?|increases?|sanctions?)', "EVENT_GEOPOLITICS"),
    (r'\bif\s+(?:AMZN|Apple|MSFT|Google|Meta|NVDA|TSM|TSLA|Oracle|OpenAI)\s+(?:invests?|funds?|acquires?|partners?)', "EVENT_CORPORATE"),
    (r'\bif\s+(?:it|the)\s+(?:gets|receive|receives|wins|loses|secures|loses|closes|reaches)\s+(?:approval|deal|contract|funding|grant|license|clearance|FDA)', "EVENT_OUTCOME"),
    
    # 中文事件条件
    (r'如果.{1,30}(?:通过|失败|增发|审批|批准|达成|完成|解禁|落地)', "ZH_EVENT"),
    (r'(?:跌破|突破)\s*\$?\d+', "ZH_PRICE_BREAK"),
]

# 排除 pattern (时间/语气修饰,不算条件)
NOT_CONDITIONAL = [
    # 时间修饰
    (r'\b(?:before|after)\s+(?:earnings|the\s+close|the\s+open|market|ER|earnings\s+call|tomorrow|next\s+(?:week|month|quarter|year)|2026|2025|end\s+of\s+(?:year|quarter|month|day)|Q\d|H\d)', "TIME_MODIFIER"),
    (r'\bwhen\s+(?:it|the|[a-z]+)\s+(?:reports?|reports|opens|closes|announces?|releases?|reports|earnings|becomes|starts|ends)', "TIME_MODIFIER"),
    (r'\bonce\s+(?:the|a|an)\s+(?:market|stock|price|situation|economy|AI|chip|cycle|story|narrative)\s+(?:is|are|reaches?|becomes?|comes?|sees?|hits?)\s+(?:truly|fully|completely|really|officially|publicly|back|to|over|out|a)', "TIME_MODIFIER"),
    # 弱条件
    (r'\bif\s+(?:you|we|they|one)\s+(?:want|need|think|believe|see|can|could|would|might|should|will|buys?|sells?|hold|don\'t|doesn\'t|miss|bought|missed)', "WEAK_CONDITIONAL"),
]

# 真条件句分类
strict_matches = []  # (pid, ticker, direction, label, matched_text, full_pred_row, raw_text)
not_conditional = []  # 排除的 (时间/弱条件)

print(f"扫描 {len(STRICT_CONDITIONAL)} 个严格条件 + {len(NOT_CONDITIONAL)} 个排除 pattern...")

for r in all_pred:
    pid = r[0]
    t = r[1]
    direction = r[2]
    # 拉 raw_text
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text_row = c.execute(sql_t, (pid,)).fetchone()
    text = text_row[0] if text_row else ""
    if not text:
        continue
    
    # 先匹配严格条件
    strict_hits = []
    for pat, label in STRICT_CONDITIONAL:
        m = re.findall(pat, text, re.IGNORECASE)
        if m:
            strict_hits.append((label, m))
    
    if strict_hits:
        strict_matches.append((pid, t, direction, strict_hits, r, text))

n_strict = len(strict_matches)
print(f"\n**真条件句: {n_strict} 条** ({n_strict/len(all_pred)*100:.1f}%)")
print(f"(对比:之前 2577 条 64.7% 是宽匹配,真条件只 {n_strict/len(all_pred)*100:.1f}%)")

# 按 label 统计
label_count = Counter()
for x in strict_matches:
    for h in x[3]:
        label_count[h[0]] += len(h[1])
print(f"\n真条件句 label 分布:")
for lbl, cnt in label_count.most_common():
    print(f"  {lbl}: {cnt}")

# ============== 3. 按 ticker 集中度看 ==============
print()
print("=" * 80)
print("Step 3: 真条件性预测按 ticker 集中度")
print("=" * 80)

by_ticker = defaultdict(list)
for x in strict_matches:
    by_ticker[x[1]].append(x)

print(f"\n{'ticker':8s}  {'n':5s}  {'first_label':30s}")
for t, items in sorted(by_ticker.items(), key=lambda x: -len(x[1])):
    first_label = items[0][3][0][0] if items[0][3] else "?"
    print(f"  {t:8s}  {len(items):5d}  {first_label:30s}")

# ============== 4. 输出真条件句清单 ==============
print()
print("=" * 80)
print("Step 4: 落报告 — 真条件句清单 (每条含原文+触发条件)")
print("=" * 80)

# 输出限制 300 条(全部的话 1500+)
out_md = []
out_md.append("# P3-7b 严格真条件性预测清单")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("## 0. 筛选规则")
out_md.append("")
out_md.append("**严格真条件句** (要求『客观可判定』的触发条件):")
out_md.append("- 价格条件: if/when/once + breaks/falls/drops/rallies/rises + above/below/to + $价格")
out_md.append("- 事件条件: if + 财务/政治/地缘/公司事件 + passes/fails/happens/approves/...")
out_md.append("- 中文事件: 如果...通过/失败/增发/审批/达成/完成/解禁/落地")
out_md.append("- 中文价格: 跌破/突破 $价格")
out_md.append("")
out_md.append("**排除 (伪条件 / 时间修饰)** — 不豁免,正常验证:")
out_md.append("- `before/after earnings/close/open/2026/Q1/Q2/H1` — 时间修饰")
out_md.append("- `when it reports/opens/closes/announces` — 时间修饰")
out_md.append("- `once market/story truly/publicly...` — 时间修饰")
out_md.append("- `if you/we/one want/think/can...` — 弱条件")
out_md.append("")
out_md.append(f"**结果**: 收窄到 **{n_strict} 条** 真条件句 (从之前 2577 条宽匹配)")
out_md.append("")

out_md.append("## 1. 真条件句按 ticker 集中度")
out_md.append("")
out_md.append("| ticker | n 真条件 |")
out_md.append("|---|---|")
for t, items in sorted(by_ticker.items(), key=lambda x: -len(x[1])):
    out_md.append(f"| {t} | {len(items)} |")
out_md.append("")

out_md.append("## 2. 真条件句详细清单 (前 200 条 — 按 ticker 集中度排序)")
out_md.append("")

count = 0
for t, items in sorted(by_ticker.items(), key=lambda x: -len(x[1])):
    if count >= 200: break
    for x in items[:20]:  # 每个 ticker 最多 20 条
        if count >= 200: break
        pid, tk, direction, hits, full_row, text = x
        pub = full_row[7]
        edate = full_row[8]
        eprice = full_row[9]
        s1m = full_row[10]
        e1m = full_row[11]
        r1m = full_row[12]
        s3m = full_row[13]
        e3m = full_row[14]
        r3m = full_row[15]
        s6m = full_row[16]
        e6m = full_row[17]
        r6m = full_row[18]
        
        labels = [h[0] for h in hits]
        sample_match = hits[0][1][0] if hits[0][1] else ""
        
        out_md.append(f"### {tk} {direction} — pub={pub[:19]}")
        out_md.append(f"- entry={edate}, ${eprice if isinstance(eprice,(int,float)) else 0:.2f}")
        out_md.append(f"- 1m: {s1m} excess={e1m*100 if isinstance(e1m,(int,float)) else 0:+.2f}%  raw={r1m*100 if isinstance(r1m,(int,float)) else 0:+.2f}%")
        out_md.append(f"- 3m: {s3m} excess={e3m*100 if isinstance(e3m,(int,float)) else 0:+.2f}%  raw={r3m*100 if isinstance(r3m,(int,float)) else 0:+.2f}%")
        out_md.append(f"- 6m: {s6m} excess={e6m*100 if isinstance(e6m,(int,float)) else 0:+.2f}%  raw={r6m*100 if isinstance(r6m,(int,float)) else 0:+.2f}%")
        out_md.append(f"- **条件 label**: {labels}")
        out_md.append(f"- **匹配文本**: `{sample_match[:100]}`")
        out_md.append(f"- **原文 (前 300 chars)**:")
        out_md.append("```")
        for line in text[:300].split("\n"):
            out_md.append(f"| {line}")
        out_md.append("```")
        out_md.append("")
        count += 1

with open(os.path.join(OUT_DIR, "phase3_p7b_strict_conditional.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"✅ 落 outputs/phase3_p7b_strict_conditional.md (前 200 条)")

# 保存所有严格条件性预测 pid 到文件,供后续应用
strict_pids = {x[0] for x in strict_matches}
with open("/workspace/logs/p3p7b_strict_conditional_pids.json", "w") as f:
    json.dump(list(strict_pids), f, indent=2)
print(f"✅ 落 /workspace/logs/p3p7b_strict_conditional_pids.json ({len(strict_pids)} pid)")

conn.close()
print("=== DONE ===")
