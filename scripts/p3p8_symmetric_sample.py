"""P3-8 条件性预测对称性抽样 — 盈亏各 50 条原文全文

铁律: 判定 if 条件是否触发必须独立于盈亏
- 客观可查证已触发 → 留分母
- 客观可查证未触发 → condition_not_triggered,移出(无论盈亏)
- 不可客观判定 → unverifiable_conditional,移出(无论盈亏,单独统计)

第一步: 严格条件性 1m resolved 的预测,按 excess 排序
- 负超额 top 50
- 正超额 top 50
两组都列 原文全文,让用户核对触发判定对称性
"""
from __future__ import annotations
import os, sqlite3, re, json
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 严格条件性 pattern (P3-7b)
STRICT_CONDITIONAL = [
    (r'\b(?:if|when|once)\s+(?:it|the|[a-z]+)\s+(?:breaks?|falls?|drops?|rallies|rises?|trades?|goes?|hits?|reaches?|touches?|approaches?|crosses?|holds?|capped\s+at)\s*(?:above|below|over|under|to|at|back\s+to)\s*\$?[\d\.]+', "PRICE_LEVEL"),
    (r'\$\d+(?:\.\d+)?\s*(?:hold|holds|holds\s+as\s+support|is\s+resistance|break(?:s|ing)?\s*(?:above|below))', "PRICE_LEVEL"),
    (r'(?:break(?:s|ing)?|fall(?:s|ing)?|drop(?:s|ping)?|rall(?:y|ies)|rise(?:s|ing)?)\s+(?:above|below|over|under)\s*\$\d+', "PRICE_BREAK"),
    (r'\$\d+\s*(?:PT|price\s+target|target|resistance|support)', "PRICE_TARGET"),
    (r'\bif\s+(?:it|the)\s+(?:passes?|fails?|gets\s+approved|gets\s+rejected|breaks|breaks\s+down|breaks\s+up|holds|holds\s+the|holds\s+at|crashes|crashes\s+through|crosses|crosses\s+(?:above|below)|falls\s+to|rallies\s+to|drops\s+to|goes\s+(?:above|below|to)|misses|misses\s+on|misses\s+EPS|beats|beats\s+on|beats\s+EPS|closes\s+(?:above|below|at|over|under)|reaches|hits|touches)\s+(?:the\s+)?(?:support|resistance|\$?\d+|[a-z]+\s+(?:vote|dilution|funding|deal|earnings|approval|partnership|breakout|breakdown|crash|rebound))', "EVENT_GENERIC"),
    (r'\bif\s+(?:it|the|a|an)\s+(?:dip(?:s|ped)?|drops?|falls?|rallies)\s+(?:to|back\s+to|below)\s+\$?\d+', "PRICE_DIP"),
    (r'\bif\s+(?:it\s+)?(?:passes|fails|approves|rejects|completes|happens|occurs)', "EVENT_VERB"),
    (r'如果.{1,30}(?:通过|失败|增发|审批|批准|达成|完成|解禁|落地)', "ZH_EVENT"),
    (r'(?:跌破|突破|跌到|涨到)\s*\$?\d+', "ZH_PRICE_BREAK"),
    (r'一旦.{1,20}(?:通过|跌破|突破|完成|解禁)', "ZH_ONCE"),
]

# 拉全部 1m resolved 的预测
sql = """
SELECT p.prediction_id, p.ticker, p.direction, p.horizon, p.conviction,
       v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return,
       v.h_1m_benchmark_return,
       v.h_3m_status, v.h_3m_excess_return, v.h_3m_raw_return,
       v.h_6m_status, v.h_6m_excess_return, v.h_6m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1
  AND v.h_1m_status IN ('resolved_hit', 'resolved_miss')
"""
all_v = c.execute(sql).fetchall()
print(f"1m resolved: {len(all_v)}")

# 找严格条件性 + 1m resolved
strict_resolved = []
for r in all_v:
    pid, t, d, h, conv, pub, ed, ep, \
    s1m, e1m, r1m, b1m, \
    s3m, e3m, r3m, \
    s6m, e6m, r6m = r
    
    # 拉 raw_text
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text_row = c.execute(sql_t, (pid,)).fetchone()
    text = text_row[0] if text_row else ""
    if not text: continue
    
    # 严格条件性匹配
    hits = []
    for pat, label in STRICT_CONDITIONAL:
        m = re.findall(pat, text, re.IGNORECASE)
        if m:
            hits.append((label, m))
    
    if hits:
        # 提取 if 句
        if_sentences = []
        sentences = re.split(r'[.!?\n]+', text)
        for sent in sentences:
            if re.search(r'\bif\b', sent, re.IGNORECASE):
                if_sentences.append(sent.strip())
        
        strict_resolved.append({
            "pid": pid, "ticker": t, "direction": d, "horizon": h,
            "pub": pub, "edate": ed, "eprice": ep,
            "e1m": e1m, "r1m": r1m, "b1m": b1m,
            "s1m": s1m,
            "e3m": e3m, "r3m": r3m,
            "e6m": e6m, "r6m": r6m,
            "labels": [h[0] for h in hits],
            "if_sentences": if_sentences[:3],
            "text": text,
        })

print(f"严格条件性 + 1m resolved: {len(strict_resolved)}")
print()

# 排序: top 50 负超额 + top 50 正超额
losses = sorted(strict_resolved, key=lambda x: x['e1m'] if isinstance(x['e1m'], (int, float)) else 0)[:50]
wins = sorted(strict_resolved, key=lambda x: -x['e1m'] if isinstance(x['e1m'], (int, float)) else 0)[:50]

print(f"Top 50 亏损: {len(losses)}")
print(f"Top 50 盈利: {len(wins)}")

# 落报告
out_md = []
out_md.append("# P3-8 条件性预测对称性抽样 — 盈亏各 50 条原文全文")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("## 铁律")
out_md.append("")
out_md.append("**判定 if 条件是否触发必须独立于这条预测的盈亏结果**。")
out_md.append("- 客观可查证已触发 → 留分母正常验证")
out_md.append("- 客观可查证未触发 → condition_not_triggered,移出(无论盈亏)")
out_md.append("- 不可客观判定 → unverifiable_conditional,移出(无论盈亏,单独统计)")
out_md.append("")
out_md.append("## 范围")
out_md.append("")
out_md.append(f"- 总 1m resolved: {len(all_v)}")
out_md.append(f"- 严格条件性 + 1m resolved: **{len(strict_resolved)}**")
out_md.append("")

def render_pred(idx, c_, group):
    pid = c_['pid']
    t = c_['ticker']
    d = c_['direction']
    h = c_['horizon']
    pub = c_['pub']
    ed = c_['edate']
    ep = c_['eprice']
    e1m = c_['e1m']
    r1m = c_['r1m']
    b1m = c_['b1m']
    s1m = c_['s1m']
    e3m = c_['e3m']
    e6m = c_['e6m']
    labels = c_['labels']
    if_sents = c_['if_sentences']
    text = c_['text']
    
    out_md.append(f"### [{group} #{idx+1}] {t} {d} hz={h} — pub={pub[:19]}")
    out_md.append(f"- entry={ed}, ${ep if isinstance(ep, (int, float)) else 0:.2f}")
    out_md.append(f"- 1m: **{s1m}** raw={r1m*100 if isinstance(r1m,(int,float)) else 0:+.2f}% bench={b1m*100 if isinstance(b1m,(int,float)) else 0:+.2f}% excess={e1m*100 if isinstance(e1m,(int,float)) else 0:+.2f}%")
    out_md.append(f"- 3m: excess={e3m*100 if isinstance(e3m,(int,float)) else 0:+.2f}%  6m: excess={e6m*100 if isinstance(e6m,(int,float)) else 0:+.2f}%")
    out_md.append(f"- **条件 label**: {labels}")
    if if_sents:
        out_md.append(f"- **if 句**: {if_sents}")
    out_md.append(f"- **原文 (全文)**:")
    out_md.append("```")
    out_md.append(text)  # 原文全文
    out_md.append("```")
    out_md.append("")


out_md.append("## Top 50 亏损(按 1m excess 从负到正)")
out_md.append("")
out_md.append("**铁律测试**: 这 50 条的 if 条件触发判定,跟我用同样规则判 top 50 盈利,应该一致")
out_md.append("")
for i, c_ in enumerate(losses):
    render_pred(i, c_, "亏损")


out_md.append("## Top 50 盈利(按 1m excess 从正到负)")
out_md.append("")
out_md.append("**铁律测试**: 这 50 条的 if 条件触发判定,跟我用同样规则判 top 50 亏损,应该一致")
out_md.append("")
for i, c_ in enumerate(wins):
    render_pred(i, c_, "盈利")

with open(os.path.join(OUT_DIR, "phase3_p8_symmetric_sample.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"✅ 落 outputs/phase3_p8_symmetric_sample.md ({len(content) if (content := open(os.path.join(OUT_DIR, 'phase3_p8_symmetric_sample.md')).read()) else 0} chars)")

# 同时输出更短的 summary
summary = []
summary.append("# P3-8 对称性抽样摘要")
summary.append("")
summary.append(f"严格条件性 1m resolved: {len(strict_resolved)}")
summary.append(f"  亏损(负 excess): {sum(1 for c_ in strict_resolved if isinstance(c_['e1m'], (int, float)) and c_['e1m'] < 0)}")
summary.append(f"  盈利(正 excess): {sum(1 for c_ in strict_resolved if isinstance(c_['e1m'], (int, float)) and c_['e1m'] > 0)}")
summary.append("")
summary.append("## 亏损 top 50 摘要 (excess 升序)")
summary.append("| # | ticker | dir | pub | e1m | 条件 label | if 句摘要 |")
summary.append("|---|---|---|---|---|---|---|")
for i, c_ in enumerate(losses):
    if_summ = c_['if_sentences'][0][:80] if c_['if_sentences'] else "(no if)"
    summary.append(f"| {i+1} | {c_['ticker']} | {c_['direction']} | {c_['pub'][:10]} | {c_['e1m']*100 if isinstance(c_['e1m'],(int,float)) else 0:+.1f}% | {c_['labels']} | `{if_summ}` |")
summary.append("")
summary.append("## 盈利 top 50 摘要 (excess 降序)")
summary.append("| # | ticker | dir | pub | e1m | 条件 label | if 句摘要 |")
summary.append("|---|---|---|---|---|---|---|")
for i, c_ in enumerate(wins):
    if_summ = c_['if_sentences'][0][:80] if c_['if_sentences'] else "(no if)"
    summary.append(f"| {i+1} | {c_['ticker']} | {c_['direction']} | {c_['pub'][:10]} | {c_['e1m']*100 if isinstance(c_['e1m'],(int,float)) else 0:+.1f}% | {c_['labels']} | `{if_summ}` |")

with open(os.path.join(OUT_DIR, "phase3_p8_summary.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(summary))
print(f"✅ 落 outputs/phase3_p8_summary.md")
conn.close()
