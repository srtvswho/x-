"""
refresh_prices_connector.py — 用金融数据库 (恒生聚源) connector 刷新 ticker_prices cache.

★ 这个脚本是给 agent 跑的 (不能用 Python 调 MCP). agent 跑的时候:
  1. 调 connector__hengsheng__resolve_entity 把 ticker 名称 → 聚源内码
  2. 调 connector__hengsheng__call_api USStockDailyQuotes 拉区间数据
  3. 解析返回 → 写 ticker_prices 表

build_dashboard.py 仍然读 ticker_prices cache (秒级, 不限速).

用法 (agent):
  python3 refresh_prices_connector.py
  → 输出: 待 agent 调 connector 调用的 JSON 列表 (ticker + pub_date + 区间)
  → agent 拿到 JSON, 调 connector, 写 cache
"""
import sqlite3, json, sys, datetime
from pathlib import Path

DB = "/workspace/data/signalboard_full.db"


def main():
    con = sqlite3.connect(DB, timeout=30)
    # 1. 收集所有需要的价格 (ticker, pub_date) - 从 extractions_intel 拉
    rows = con.execute("""
        SELECT DISTINCT e.ticker, r.published_at
        FROM extractions_intel e
        JOIN raw_posts r ON r.post_id = e.post_id
        WHERE e.direction IN ('long','short')
          AND e.is_retrospective = 0 AND e.is_disclosure = 0
          AND e.ticker IS NOT NULL
    """).fetchall()
    tasks = []
    for ticker_json, pub in rows:
        if not isinstance(ticker_json, str): continue
        pub_date = pub[:10] if pub else None
        if not pub_date: continue
        # parse_json_arr logic
        s = ticker_json.strip()
        if s.startswith('['):
            try: tk_list = json.loads(s)
            except: continue
        else:
            tk_list = [s] if s else []
        for tk in tk_list:
            tasks.append({"ticker": tk, "pub_date": pub_date})

    # 去重
    seen = set()
    unique = []
    for t in tasks:
        k = (t['ticker'], t['pub_date'])
        if k in seen: continue
        seen.add(k)
        unique.append(t)

    print(f"总任务: {len(tasks)}, 去重: {len(unique)}", flush=True)

    # 2. 查 cache 哪些已存在 (避免重复)
    need = []
    for t in unique:
        row = con.execute("SELECT call_price, now_price, now_date FROM ticker_prices WHERE ticker=? AND pub_date=?",
                          (t['ticker'], t['pub_date'])).fetchone()
        if row and row[0] and row[1] and row[2]:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            if row[2] >= today or (datetime.datetime.fromisoformat(today) - datetime.datetime.fromisoformat(row[2])).days <= 1:
                continue  # 已 cache, 跳过
        need.append(t)

    print(f"待查 (cache miss / 过期): {len(need)}", flush=True)

    # 3. 按 ticker 分组 (一次查 ticker 所有日期)
    by_ticker = {}
    for t in need:
        by_ticker.setdefault(t['ticker'], set()).add(t['pub_date'])

    # 4. 输出 connector 调用任务清单
    out = []
    for tk, dates in by_ticker.items():
        if not dates: continue
        # 区间 = min/max + 一点 buffer
        d_min = min(dates)
        d_max = max(dates)
        # 给 call_price 留 7 天 buffer
        d_min_buf = (datetime.datetime.fromisoformat(d_min) - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        # 给 now_price 取最新 (今天)
        d_today = datetime.datetime.now().strftime("%Y-%m-%d")
        out.append({
            "ticker": tk,
            "begin": d_min_buf,
            "end": d_today,
            "pub_dates": sorted(dates),
        })

    out.sort(key=lambda x: x['ticker'])
    print(f"\n===== 待 agent 调 connector =====", flush=True)
    print(f"  唯一 ticker: {len(out)}", flush=True)
    for o in out[:5]:
        print(f"  sample: {o}", flush=True)
    print(f"  ... ({len(out)} total)", flush=True)

    # 写 tasks.json 让 agent 后续读
    Path("/tmp/connector_tasks.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n→ 写 /tmp/connector_tasks.json ({len(out)} ticker)", flush=True)
    con.close()


if __name__ == "__main__":
    main()