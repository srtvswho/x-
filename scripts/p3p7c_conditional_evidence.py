"""手动核对 AAOI/AXTI/IREN/CRCL/CRWV/MU/POET/ARM 全部 short 条件性"""
import sqlite3, re
conn = sqlite3.connect('/workspace/data/signalboard_full.db')
c = conn.cursor()
sql = '''
SELECT p.prediction_id, p.ticker, p.direction, v.published_at, v.entry_date_actual, v.entry_price,
       v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return
FROM predictions p JOIN verifications v ON p.prediction_id=v.prediction_id
WHERE p.price_source_available=1 AND p.direction='short' AND p.ticker IN ('AAOI','AXTI','IREN','CRCL','CRWV','MU','POET','ARM','PLTR','ALAB','RKLB','AMD','HIMS','RDDT','PL','NVDA')
ORDER BY p.ticker, v.published_at
'''
total = 0
cond_yes = 0
cond_no = 0
mixed = 0
for r in c.execute(sql):
    pid, t, d, pub, ed, ep, s, e, rr = r
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text = c.execute(sql_t, (pid,)).fetchone()[0]
    sentences = re.split(r'[.!?\n]+', text)
    if_sentences = [sent.strip() for sent in sentences if re.search(r'\bif\b', sent, re.IGNORECASE)][:3]
    has_condition = bool(if_sentences)
    if has_condition:
        ifs = ' / '.join(s[:120] for s in if_sentences if s)
        e_val = e*100 if isinstance(e,(int,float)) else 0
        print(f"\n[{t} {d}] pub={pub[:10]} entry={ed} 1m: {s} exc={e_val:+.1f}%")
        print(f"  IF: {ifs}")
        total += 1

print(f"\n\n总带 if 的 short: {total}")
