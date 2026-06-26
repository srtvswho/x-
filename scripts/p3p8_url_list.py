"""P3-8b 为 top 50 亏 + top 50 盈的 100 条生成 X 推文 URL"""
import os, sqlite3, re, json
from datetime import datetime
from collections import defaultdict

DB = "/workspace/data/signalboard_full.db"
OUT_DIR = "/workspace/outputs"
conn = sqlite3.connect(DB, timeout=30)
c = conn.cursor()

# 拉 strict conditional 1m resolved
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

sql = """
SELECT p.prediction_id, p.ticker, p.direction, v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return
FROM predictions p
JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1
  AND v.h_1m_status IN ('resolved_hit', 'resolved_miss')
"""
all_v = c.execute(sql).fetchall()

strict = []
for r in all_v:
    pid, t, d, pub, ed, ep, s1m, e1m, r1m = r
    sql_t = 'SELECT rp.raw_text, rp.raw_url FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    tr = c.execute(sql_t, (pid,)).fetchone()
    if not tr: continue
    text, url = tr
    if not text: continue
    hits = []
    for pat, label in STRICT_CONDITIONAL:
        m = re.findall(pat, text, re.IGNORECASE)
        if m:
            hits.append(label)
    if hits:
        strict.append({
            "pid": pid, "ticker": t, "direction": d, "pub": pub, "edate": ed, "eprice": ep,
            "e1m": e1m, "r1m": r1m, "s1m": s1m, "url": url,
        })

print(f"Strict + 1m resolved: {len(strict)}")
losses = sorted(strict, key=lambda x: x['e1m'] if isinstance(x['e1m'], (int, float)) else 0)[:50]
wins = sorted(strict, key=lambda x: -x['e1m'] if isinstance(x['e1m'], (int, float)) else 0)[:50]

# 输出 markdown 链接列表
out_md = []
out_md.append("# P3-8 100 条原文 X 推文链接 (盈亏各 50)")
out_md.append("")
out_md.append(f"**生成时间**: {datetime.utcnow().isoformat()}Z")
out_md.append("")
out_md.append("**用法**: 直接点击链接看原推文+上下文(X 显示包括原推和回复)")
out_md.append("")
out_md.append("## Top 50 亏损 (按 1m excess 升序)")
out_md.append("")
out_md.append("| # | ticker | dir | pub | entry | px | 1m | excess | 链接 |")
out_md.append("|---|---|---|---|---|---|---|---|---|")
for i, c_ in enumerate(losses):
    e_val = c_['e1m']*100 if isinstance(c_['e1m'],(int,float)) else 0
    out_md.append(f"| {i+1} | {c_['ticker']} | {c_['direction']} | {c_['pub'][:10]} | {c_['edate']} | ${c_['eprice'] if isinstance(c_['eprice'],(int,float)) else 0:.2f} | {c_['s1m']} | {e_val:+.1f}% | [{c_['url']}]({c_['url']}) |")

out_md.append("")
out_md.append("## Top 50 盈利 (按 1m excess 降序)")
out_md.append("")
out_md.append("| # | ticker | dir | pub | entry | px | 1m | excess | 链接 |")
out_md.append("|---|---|---|---|---|---|---|---|---|")
for i, c_ in enumerate(wins):
    e_val = c_['e1m']*100 if isinstance(c_['e1m'],(int,float)) else 0
    out_md.append(f"| {i+1} | {c_['ticker']} | {c_['direction']} | {c_['pub'][:10]} | {c_['edate']} | ${c_['eprice'] if isinstance(c_['eprice'],(int,float)) else 0:.2f} | {c_['s1m']} | {e_val:+.1f}% | [{c_['url']}]({c_['url']}) |")

# 单独 URLs 文件(plain text,方便复制)
out_md.append("")
out_md.append("## 纯链接(便于批量打开)")
out_md.append("")
out_md.append("### 亏损 50")
for c_ in losses:
    out_md.append(c_['url'])
out_md.append("")
out_md.append("### 盈利 50")
for c_ in wins:
    out_md.append(c_['url'])

with open(os.path.join(OUT_DIR, "phase3_p8_url_list.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))
print(f"✅ 落 outputs/phase3_p8_url_list.md")

conn.close()
