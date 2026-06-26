"""P3-7d 严格条件性 + 还在 short 列表 + if 触发评估

Step 1: 找严格条件性预测 (regex + LLM-style 评估)
Step 2: 还在 short 列表的(没被 P3-6 改 neutral)
Step 3: 对每条 — if 是否在 1w/1m/3m/6m 窗口内发生?

输出: 严格条件性 + if 没触发的清单(给原文+查证)
"""
from __future__ import annotations
import os, sqlite3, re, json
from datetime import datetime, date, timedelta
from typing import Dict, List
from collections import defaultdict
import statistics

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 严格条件句 pattern (修订,增加更多可观察的)
STRICT_CONDITIONAL = [
    # 价格条件
    (r'\b(?:if|when|once)\s+(?:it|the|[a-z]+)\s+(?:breaks?|falls?|drops?|rallies|rises?|trades?|goes?|hits?|reaches?|touches?|approaches?|crosses?|holds?|capped\s+at)\s*(?:above|below|over|under|to|at|back\s+to)\s*\$?[\d\.]+', "PRICE_LEVEL"),
    (r'\$\d+(?:\.\d+)?\s*(?:hold|holds|holds\s+as\s+support|is\s+resistance|break(?:s|ing)?\s*(?:above|below))', "PRICE_LEVEL"),
    (r'(?:break(?:s|ing)?|fall(?:s|ing)?|drop(?:s|ping)?|rall(?:y|ies)|rise(?:s|ing)?)\s+(?:above|below|over|under)\s*\$\d+', "PRICE_BREAK"),
    (r'\$\d+\s*(?:PT|price\s+target|target|resistance|support)', "PRICE_TARGET"),
    
    # 事件条件
    (r'\bif\s+(?:it|the)\s+(?:passes?|fails?|gets\s+approved|gets\s+rejected|breaks|breaks\s+down|breaks\s+up|holds|holds\s+the|holds\s+at|crashes|crashes\s+through|crosses|crosses\s+(?:above|below)|falls\s+to|rallies\s+to|drops\s+to|goes\s+(?:above|below|to)|misses|misses\s+on|misses\s+EPS|beats|beats\s+on|beats\s+EPS|closes\s+(?:above|below|at|over|under)|reaches|hits|touches)\s+(?:the\s+)?(?:support|resistance|\$?\d+|[a-z]+\s+(?:vote|dilution|funding|deal|earnings|approval|partnership|breakout|breakdown|crash|rebound))', "EVENT_GENERIC"),
    (r'\bif\s+(?:it|the|a|an)\s+(?:dip(?:s|ped)?|drops?|falls?|rallies)\s+(?:to|back\s+to|below)\s+\$?\d+', "PRICE_DIP"),
    
    # 增发/vote 等
    (r'\bif\s+(?:it\s+)?(?:passes|fails|approves|rejects|completes|happens|occurs)', "EVENT_VERB"),
    
    # 中文
    (r'如果.{1,30}(?:通过|失败|增发|审批|批准|达成|完成|解禁|落地)', "ZH_EVENT"),
    (r'(?:跌破|突破|跌到|涨到)\s*\$?\d+', "ZH_PRICE_BREAK"),
    (r'一旦.{1,20}(?:通过|跌破|突破|完成|解禁)', "ZH_ONCE"),
]

# 拉所有 short
sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.horizon, p.conviction,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return,
       v.h_1w_status, v.h_1w_excess_return, v.h_1w_raw_return,
       v.h_3m_status, v.h_3m_excess_return, v.h_3m_raw_return,
       v.h_6m_status, v.h_6m_excess_return, v.h_6m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1 AND p.direction='short'
"""
all_short = c.execute(sql).fetchall()
print(f"短头寸总: {len(all_short)}")

# 找严格条件性
strict_conditional = []
for r in all_short:
    pid, t, direction, horizon, conv, pub, edate, eprice, \
    s1m, e1m, r1m, s1w, e1w, r1w, s3m, e3m, r3m, s6m, e6m, r6m = r
    
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text = c.execute(sql_t, (pid,)).fetchone()
    text = text[0] if text else ""
    if not text: continue
    
    # 严格条件
    hits = []
    for pat, label in STRICT_CONDITIONAL:
        m = re.findall(pat, text, re.IGNORECASE)
        if m:
            hits.append((label, m))
    
    if hits:
        strict_conditional.append({
            "pid": pid, "ticker": t, "direction": direction, "horizon": horizon,
            "pub": pub, "edate": edate, "eprice": eprice,
            "s1m": s1m, "e1m": e1m, "r1m": r1m,
            "s1w": s1w, "e1w": e1w, "r1w": r1w,
            "s3m": s3m, "e3m": e3m, "r3m": r3m,
            "s6m": s6m, "e6m": e6m, "r6m": r6m,
            "labels": [h[0] for h in hits],
            "sample_match": hits[0][1][0] if hits[0][1] else "",
            "text": text,
        })

print(f"严格条件性 + 还在 short 列表: {len(strict_conditional)} 条")
print()
print("按 label 分布:")
label_count = defaultdict(int)
for c_ in strict_conditional:
    for l in c_['labels']:
        label_count[l] += 1
for l, n in sorted(label_count.items(), key=lambda x: -x[1]):
    print(f"  {l}: {n}")

# 按 ticker
print()
print("按 ticker 分布:")
by_t = defaultdict(int)
for c_ in strict_conditional:
    by_t[c_['ticker']] += 1
for t, n in sorted(by_t.items(), key=lambda x: -x[1]):
    print(f"  {t}: {n}")


# 输出严格条件性 + 还在 short 列表的完整清单
out_md = []
out_md.append("# P3-7d 严格条件性 short 清单(if 是否在窗口内触发)")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("## 0. 范围")
out_md.append("")
out_md.append(f"- 短头寸总数: {len(all_short)} (P3-6 应用后,排除了 13 B 改 neutral 的)")
out_md.append(f"- 严格条件性 + 还在 short 列表: **{len(strict_conditional)} 条**")
out_md.append("")
out_md.append("**严格条件句标准**:")
out_md.append("- 价格条件: if/when/once + 价格动作(break/fall/drop/rise/...) + above/below/to + $价格")
out_md.append("- 事件条件: if + 财务/政治/地缘/公司事件 + 客观动作(passes/fails/approves/...)")
out_md.append("- 中文: 如果/一旦 + 事件/价格动作")
out_md.append("")
out_md.append("**排除 (伪条件/时间修饰)** — 不豁免:")
out_md.append("- after/before/when + 时间(earnings/close/Q1/2026/H1)")
out_md.append("- if + 弱动词(want/think/can/should/will)")
out_md.append("- once + 模糊时间(market truly/publicly/...)")
out_md.append("")
out_md.append("## 1. 按 label 分布")
out_md.append("")
out_md.append("| Label | n |")
out_md.append("|---|---|")
for l, n in sorted(label_count.items(), key=lambda x: -x[1]):
    out_md.append(f"| {l} | {n} |")
out_md.append("")
out_md.append("## 2. 按 ticker 分布")
out_md.append("")
out_md.append("| ticker | n 真条件 |")
out_md.append("|---|---|")
for t, n in sorted(by_t.items(), key=lambda x: -x[1]):
    out_md.append(f"| {t} | {n} |")
out_md.append("")
out_md.append("## 3. 严格条件性 short 完整清单")
out_md.append("")
out_md.append("**对每条:需要你判定 if 条件在 1w/1m/3m/6m 窗口内是否真的发生**")
out_md.append("")

for i, c_ in enumerate(strict_conditional, 1):
    pid = c_['pid']
    t = c_['ticker']
    direction = c_['direction']
    pub = c_['pub']
    edate = c_['edate']
    eprice = c_['eprice']
    
    out_md.append(f"### [{i}] {t} {direction} — pub={pub[:19]}")
    out_md.append(f"- entry={edate}, ${eprice:.2f}" if isinstance(eprice, (int, float)) else f"- entry={edate}")
    out_md.append(f"- 1m: {c_['s1m']} excess={c_['e1m']*100 if isinstance(c_['e1m'],(int,float)) else 0:+.2f}% raw={c_['r1m']*100 if isinstance(c_['r1m'],(int,float)) else 0:+.2f}%")
    out_md.append(f"- 1w: {c_['s1w']} excess={c_['e1w']*100 if isinstance(c_['e1w'],(int,float)) else 0:+.2f}%")
    out_md.append(f"- 3m: {c_['s3m']} excess={c_['e3m']*100 if isinstance(c_['e3m'],(int,float)) else 0:+.2f}%")
    out_md.append(f"- 6m: {c_['s6m']} excess={c_['e6m']*100 if isinstance(c_['e6m'],(int,float)) else 0:+.2f}%")
    out_md.append(f"- **条件 label**: {c_['labels']}")
    out_md.append(f"- **匹配**: `{c_['sample_match'][:120]}`")
    out_md.append(f"- **原文 (前 400 chars)**:")
    out_md.append("```")
    for line in c_['text'][:400].split("\n"):
        out_md.append(f"| {line}")
    out_md.append("```")
    out_md.append("")

with open(os.path.join(OUT_DIR, "phase3_p7d_strict_conditional_short.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"\n✅ 落 outputs/phase3_p7d_strict_conditional_short.md")

# 保存 pid 列表
strict_pids = [c_['pid'] for c_ in strict_conditional]
with open("/workspace/logs/p3p7d_strict_short_pids.json", "w") as f:
    json.dump(strict_pids, f, indent=2)
print(f"✅ 落 p3p7d_strict_short_pids.json ({len(strict_pids)} pid)")

conn.close()
