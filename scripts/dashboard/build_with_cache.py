"""build_with_cache.py — 只用 cache 跑 dashboard (跳过 Polygon).

用于验证 dashboard.html 生成 OK. 真正 cron 跑 build_dashboard.py (会查 Polygon 填 cache).
"""
import sys, sqlite3, json, pathlib
sys.path.insert(0, '/workspace/scripts/dashboard')
import build_dashboard as bd

con = sqlite3.connect('/workspace/data/signalboard_full.db', timeout=30)
bd.init_price_cache(con)
bd.refresh_sector_snapshots(con)  # 1 个 API call (1y SOXX)

data = bd.query_extractions(con)
print(f"extractions: {len(data)}", flush=True)

# query_tickers 但**绕过 Polygon** (用 cache, 没 cache 的 ticker 标 None)
def query_tickers_cached_only(con):
    rows = con.execute("""
        SELECT e.source_id, e.ticker, e.direction, e.bottleneck, r.published_at
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE e.direction IN ('long','short')
          AND e.is_retrospective = 0 AND e.is_disclosure = 0
          AND e.ticker IS NOT NULL
        ORDER BY r.published_at DESC
    """).fetchall()
    seen=set(); out=[]
    for src,ticker_json,direction,bk,pub in rows:
        kol = bd.SRC2KOL.get(src, src.replace("tw_",""))
        for tk in bd.parse_json_arr(ticker_json):
            key=(kol,tk)
            if key in seen: continue
            seen.add(key)
            pub_date = pub[:10] if pub else None
            call_price, now_price, raw_pct, excess_pct = (None, None, None, None)
            if pub_date:
                # 只查 cache, 不调 Polygon
                cached = bd.get_cached_price(con, tk, pub_date)
                if cached is not None:
                    cp, np_, nd, sec = cached
                    if cp and np_ and cp > 0:
                        call_price = cp; now_price = np_
                        raw_pct = round((np_ - cp) / cp * 100, 1)
                        excess_pct = round(raw_pct - sec, 1) if sec is not None else None
            in_field = bool(bk) and any(s in bk or bk in s for s in bd.KOLS.get(kol,{}).get("strong",[]))
            out.append({
                "ticker":tk,"kol":kol,"direction":direction,"called_at":pub,
                "call_price":call_price,"now_price":now_price,
                "raw_pct":raw_pct,"excess_pct":excess_pct,"in_field":in_field,
            })
    out.sort(key=lambda d:d["called_at"], reverse=True)
    return out[:30]

tickers = query_tickers_cached_only(con)
print(f"tickers: {len(tickers)} (cache hit, 无 API call)", flush=True)
hit = sum(1 for t in tickers if t['raw_pct'] is not None)
print(f"  price hit: {hit}/{len(tickers)}", flush=True)
con.close()

summaries = bd.load_summaries()
html = bd.TEMPLATE.read_text(encoding="utf-8")
html = html.replace("__RECORDS__",   json.dumps(data, ensure_ascii=False))
html = html.replace("__KOLS__",      json.dumps(bd.KOLS, ensure_ascii=False))
html = html.replace("__TICKERS__",   json.dumps(tickers, ensure_ascii=False))
html = html.replace("__SUMMARIES__", json.dumps(summaries, ensure_ascii=False))
bd.OUT.write_text(html, encoding="utf-8")
print(f"\n✓ dashboard.html: {len(html):,} chars", flush=True)
print(f"  占位符剩余: __RECORDS__={html.count('__RECORDS__')} __TICKERS__={html.count('__TICKERS__')} __SUMMARIES__={html.count('__SUMMARIES__')}", flush=True)