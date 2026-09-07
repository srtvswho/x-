#!/usr/bin/env python3
"""Refresh explicit exchange-qualified listings in their native currency."""
import argparse
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import sqlite3
import time
from zoneinfo import ZoneInfo
import requests
from common import select_call_performance_targets, group_targets_by_ticker, price_currency
from refresh_prices_polygon import ensure_tables, upsert_price


def parse_chart(payload,ticker):
    root=payload.get('chart',{})
    if root.get('error') or not root.get('result'):
        raise ValueError('No chart for explicit listing')
    result=root['result'][0];meta=result['meta']
    if meta.get('symbol','').upper()!=ticker.upper() or meta.get('currency')!=price_currency(ticker):
        raise ValueError('Listing/currency mismatch')
    zone=ZoneInfo(meta['exchangeTimezoneName'])
    bars=[]
    closes=result['indicators']['quote'][0]['close']
    for stamp,close in zip(result.get('timestamp',[]),closes):
        if close is not None and close>0:
            bars.append((datetime.fromtimestamp(stamp,zone).date().isoformat(),close))
    return sorted(bars)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='/workspace/data/signalboard_full.db')
    args=p.parse_args();report={'source':'Yahoo Finance chart','listings':{}}
    with sqlite3.connect(args.db) as con:
        ensure_tables(con)
        targets=group_targets_by_ticker(select_call_performance_targets(con))
        for ticker,rows in targets.items():
            if price_currency(ticker)=='USD':continue
            first=min(r['call_date'] for r in rows)
            start=datetime.fromisoformat(first).replace(tzinfo=timezone.utc)-timedelta(days=10)
            try:
                response=requests.get('https://query1.finance.yahoo.com/v8/finance/chart/'+ticker,
                    params={'period1':int(start.timestamp()),'period2':int(datetime.now(timezone.utc).timestamp()),'interval':'1d'},
                    headers={'User-Agent':'Mozilla/5.0'},timeout=30)
                response.raise_for_status();bars=parse_chart(response.json(),ticker)
                if not bars:raise ValueError('No valid closing prices')
                for row in rows:
                    earlier=[b for b in bars if b[0]<=row['call_date']]
                    call=earlier[-1][1] if earlier else None
                    upsert_price(con,ticker,row['call_date'],call,bars[-1][1],bars[-1][0],authoritative_call=True)
                con.commit()
                report['listings'][ticker]={'currency':price_currency(ticker),'latest_date':bars[-1][0],'rows':len(rows),'status':'saved'}
            except Exception as exc:
                report['listings'][ticker]={'status':'missing','reason':f'{type(exc).__name__}: {exc}'}
            time.sleep(1)
    Path('outputs/international_price_refresh.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
