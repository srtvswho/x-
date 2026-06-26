import sqlite3
import re
conn = sqlite3.connect('/workspace/data/signalboard_full.db')
c = conn.cursor()
sql = "SELECT p.prediction_id, p.ticker, p.direction, v.published_at, v.entry_date_actual, v.entry_price, v.h_1m_status, v.h_1m_excess_return, v.h_1m_raw_return FROM predictions p JOIN verifications v ON p.prediction_id=v.prediction_id WHERE p.price_source_available=1 AND p.direction='short' AND p.ticker='AAOI' ORDER BY v.published_at"
for r in c.execute(sql):
    pid, t, d, pub, ed, ep, s, e, rr = r
    sql_t = 'SELECT rp.raw_text FROM predictions p JOIN raw_posts rp ON p.post_id = rp.post_id WHERE p.prediction_id = ?'
    text = c.execute(sql_t, (pid,)).fetchone()[0]
    print("text length:", len(text))
    print("First 200:", text[:200])
    print()
    parts = re.split(r'[.!?\n]+', text)
    print("Parts count:", len(parts))
    if_parts = [p for p in parts if re.search('if', p, re.IGNORECASE)]
    print("IF parts count:", len(if_parts))
    if if_parts:
        for ip in if_parts[:3]:
            print(" |", ip[:120])
    break
