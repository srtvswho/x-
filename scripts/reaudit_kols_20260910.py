"""Offline KOL audit from current saved interpretations; no model or paid API calls."""
import json,re,datetime,statistics,collections,sys,urllib.request,urllib.parse,concurrent.futures,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'/'kol_reaudit_20260910';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
input_path=OUT/'input_events.json'
if input_path.exists():
 EVENTS=json.load(open(input_path))
elif (OUT/'input_events.json.gz').exists():
 with gzip.open(OUT/'input_events.json.gz','rt') as f:EVENTS=json.load(f)
elif (OUT/'scored_events.json.gz').exists():
 with gzip.open(OUT/'scored_events.json.gz','rt') as f:EVENTS=json.load(f)
 EVENTS=[dict(e,direction=e.get('original_direction',e['direction'])) for e in EVENTS]
elif (ROOT.parent/'reaudit_events.json').exists():
 EVENTS=json.load(open(ROOT.parent/'reaudit_events.json'))
else:
 import gzip,shutil,tempfile,sqlite3
 from scripts.dashboard.common import query_call_performance_events
 with tempfile.TemporaryDirectory() as tmp:
  db=Path(tmp)/'snapshot.db'
  with gzip.open(ROOT/'data'/'signalboard.db.gz','rb')as src,open(db,'wb')as dest:shutil.copyfileobj(src,dest)
  with sqlite3.connect(f'file:{db}?mode=ro',uri=True)as con:EVENTS=query_call_performance_events(con)
input_path.write_text(json.dumps(EVENTS,ensure_ascii=False))
PRICE_DIR=OUT/'prices';PRICE_DIR.mkdir(exist_ok=True)
if not any(PRICE_DIR.glob('*.json')) and (OUT/'prices.json.gz').exists():
 with gzip.open(OUT/'prices.json.gz','rt') as f:archived_prices=json.load(f)
 for symbol,payload in archived_prices.items():
  (PRICE_DIR/(symbol+'.json')).write_text(json.dumps(payload))
 del archived_prices
# Explicit financial/price expectations. This subset intentionally excludes business-only praise.
FIN=re.compile(r'\b(buy(?:ing)?|bought|sell(?:ing)?|sold|long|short(?:ing)?|bullish|bearish|undervalued|overvalued|mispriced|overpriced|underpriced|upside|downside|breakout|break[ -]out|breakdown|buyback|accumulat\w*|load(?:ing)?\s+up|price\s+target|target\s+price|stock\s+pick|portfolio|position(?:s|ing)?|re[ -]?rat(?:e|ing)|market\s+cap|ATHs?|higher\s+high|lower\s+low|bottom|support|resistance|screaming\s+buy|dip(?:s)?|rall(?:y|ies)|\d+x|cheap|expensive|bargain|moon\w*|bagger|will\s+(?:go\s+up|rise|rally|fall|crash)|climb\s+imminent|ready\s+(?:for|to)|more\s+to\s+run|could\s+run|swing\s+trad\w*)\b|看多|看空|买入|做多|做空|低估|高估|加仓|减仓|目标价|仓位|\bach(?:at|eter|eteur)|\bvend(?:re|eur)|\bhaussi\w*|\bbaissi\w*|\bsous.valu\w*|\bsur.valu\w*|\bexplos\w*|\bperformer\b',re.I)
COND=re.compile(r'\bif\s+(?:true|it[’\']?s\s+true|this\s+is\s+true)|\bwait(?:ing)?\s+(?:for|until|to\s+buy)|\bwould\s+buy\s+(?:if|at)|\bwill\s+buy\s+(?:if|at)|\bj.attendrai\b|\bje\s+serai\s+acheteur\s+en\b|如果.*(?:买入|加仓)|等待.*(?:突破|买入)',re.I)
EXCLUDED_IDS={9:'business_only',17:'business_only',39:'business_only',58:'business_only',59:'business_only',77:'business_only',263:'business_only',313:'business_only',372:'not_short_is_not_buy',3883:'business_only',4139:'business_only',4323:'business_only',5409:'cheering',5410:'industry_forecast',5437:'industry_forecast',5439:'product_shipments',5557:'product_rumour',5563:'industry_commentary',5676:'industry_forecast',5677:'industry_forecast',5739:'quoted_third_party',5884:'industry_forecast',5999:'relayed_research',6000:'relayed_research',6062:'industry_commentary',6180:'unresolved_security',1763:'buy_consumer_ssd',2421:'buy_server_cpu',1838:'retrospective_wrong_nvda',1905:'quoted_third_party',2812:'cpo_adoption_not_nvda_stock',3538:'buy_dell_computer',1571:'quoted_interview',1572:'quoted_interview',4898:'direction_applies_to_dell_only',4844:'retrospective',5335:'retrospective',6391:'product_news',5626:'company_target_not_share_price',6111:'third_party_short',5678:'vix_as_indicator_not_vix_short'}
ALIASES={'BRKB':'BRK-B','BRK.B':'BRK-B','SPX':'^GSPC','NDX':'^NDX','DJI':'^DJI','DAX':'^GDAXI','CAC':'^FCHI','VIX':'^VIX'}
# Manual semantic review of every candidate for the three low-volume research authors.
AUSTIN_KEEP={69,370,777,1054,1574,1804,3327,3328,3329,5226}
JUKAN_KEEP={16,75,203,212,245,482,631,632,1109,1110,5740,5780,5867}
ZEPHYR_KEEP={18,19,20,21,22,23,24,25,26,213,250,1650,1659,1816,1821,1914,1915,1927,2620,2621,2622,2623,3549,3550,3607,5872}
EXCLUDED_IDS.update({4835:'third_party_or_ambiguous_buy',5895:'holding_disclosure',5930:'retrospective_bottom',2269:'conditional_entry',4601:'waiting_to_enter',5105:'conditional_entry',5151:'conditional_short',5209:'conditional_zone_and_sox_soxx_mismatch',5262:'conditional_zone',5301:'profit_taking',5572:'future_dated_entry',5610:'entry_date_only_in_unread_image',5971:'waiting_for_breakout',6242:'conditional_breakdown',6347:'future_event_exit'})
EXCLUDED_IDS.update({4720:'retrospective_self_praise',1604:'retrospective_profit',3106:'bandwidth_not_stock_price',5956:'explicitly_no_earnings_direction'})
EXCLUDED_IDS.update({449:'untriggered_price_condition',3696:'hedging_not_available',3256:'tighten_stop_not_short',4368:'explicitly_no_position_yet',4518:'preplanning_only',4519:'preplanning_only',4576:'conditional_future_sell',5123:'sector_comment_not_nvda_short',5200:'conditional_setup',5290:'conditional_sell_price',5481:'waiting_for_rebound',5852:'five_year_industry_cost_forecast'})
# Sarcasm/ambiguous "sold out" cannot be promoted to actual sell signals.
EXCLUDED_POSTS={EVENTS[i]['post_id']:'sarcasm_quote_or_sold_out_ambiguity' for i in [2994,3848,5497,5947]}
DIRECTION_OVERRIDES={2913:'long',1095:'long'}
AMBIG={'GOLD','SILVER','WTI','BRENT','BTC','ETH','SOL','XRP','TI','TORO','SIVE','SIVEF','SKHY','AI','NV','LCRX','AIXTRON','AMEC','NAURA','MACRONIX','NANYA','WINBOND','ASMPT','BESI','CXMT','YMTC','MONT'}
def prep():
 assert all(EVENTS[i]['published_at']<=EVENTS[i+1]['published_at'] for i in range(len(EVENTS)-1)), 'Frozen events must remain chronological; manual decisions use their original indices.'
 rows=[]
 for i,x in enumerate(EVENTS):
  x=dict(x,event_index=i);s=x['raw_text'];reason=EXCLUDED_IDS.get(i)or EXCLUDED_POSTS.get(x['post_id'])
  if i in DIRECTION_OVERRIDES:
   x['original_direction']=x['direction'];x['direction']=DIRECTION_OVERRIDES[i];x['manual_direction_reason']='Full original text explicitly states bullishness/bottom, contradicting saved short label.'
  if not reason and COND.search(s):reason='conditional_or_waiting'
  if not reason and not FIN.search(s):reason='no_explicit_financial_expression'
  manual={'tw_jukan05':JUKAN_KEEP,'tw_austinsemis':AUSTIN_KEEP,'tw_zephyr_z9':ZEPHYR_KEEP}
  if x['source_id'] in manual:
   reason=None if i in manual[x['source_id']] else reason or 'manual_business_or_nonactionable'
  x['strict_eligible']=reason is None;x['strict_exclusion']=reason
  x['price_symbol']=ALIASES.get(x['ticker'],x['ticker'])
  x['identity_exclusion']='ambiguous_security_identity' if x['ticker'] in AMBIG else None
  rows.append(x)
 (OUT/'events.json').write_text(json.dumps(rows,ensure_ascii=False))
 print('strict',collections.Counter(x['source_id'] for x in rows if x['strict_eligible']))
 print('strict exclusions',collections.Counter(x['strict_exclusion'] for x in rows if not x['strict_eligible']))
 symbols=sorted({x['price_symbol'] for x in rows if not x['identity_exclusion']}|{'SPY','SOXX','QQQ','IWM','^KS11','^TWII'})
 (OUT/'symbols.json').write_text(json.dumps(symbols));print('symbols',len(symbols))
def fetch_one(t):
 path=PRICE_DIR/(t.replace('/','_')+'.json')
 if path.exists():return t,'cached'
 url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(t,safe='')+'?period1=1672531200&period2=1788998400&interval=1d&events=splits%2Cdiv'
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as r:d=json.load(r)
  v=d['chart']['result'][0];path.write_text(json.dumps(v));return t,'ok'
 except Exception as ex:
  path.write_text(json.dumps({'error':str(ex)}));return t,'error'
def fetch():
 symbols=json.load(open(OUT/'symbols.json'));counts=collections.Counter()
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
  for i,(t,result) in enumerate(ex.map(fetch_one,symbols)):
   counts[result]+=1
   if (i+1)%50==0:print(i+1,dict(counts),flush=True)
 print('FINAL',dict(counts),flush=True)
def calculate():
 import bisect
 from zoneinfo import ZoneInfo
 rows=json.load(open(OUT/'events.json'));prices={};meta={};errors={}
 for f in PRICE_DIR.glob('*.json'):
  v=json.load(open(f));t=f.stem
  if 'error' in v:errors[t]=v['error'];continue
  try:
   q=v['indicators']['quote'][0];z=ZoneInfo(v['meta']['exchangeTimezoneName']);a=[]
   for i,ts in enumerate(v.get('timestamp',[])):
    date=datetime.datetime.fromtimestamp(ts,z).date().isoformat()
    if date>'2026-09-09' or not q['open'][i] or not q['close'][i]:continue
    a.append({'ts':ts,'date':date,'open':q['open'][i],'close':q['close'][i],'high':q['high'][i],'low':q['low'][i]})
   prices[t]=a;meta[t]=v['meta']
  except Exception as ex:errors[t]=str(ex)
 market_dates=[b['date']for b in prices.get('SPY',[])]
 if not market_dates or market_dates[-1]!='2026-09-09':raise RuntimeError('SPY reference calendar not current')
 lookup={t:{b['date']:b for b in a}for t,a in prices.items()}
 equity_etfs={'SPY','SOXX','SMH','QQQ','IWM','XLK','XBI','KWEB','FXI','EWY','DRAM'}
 for r in rows:
  t=r['price_symbol'];m=meta.get(t,{});a=prices.get(t,[]);r['results']={};r['price_status']='ok'
  r['group']='US_equity' if m.get('currency')=='USD' and (m.get('instrumentType')=='EQUITY' or t in equity_etfs) else 'other'
  if r['identity_exclusion']:r['price_status']=r['identity_exclusion'];continue
  if not a:r['price_status']='no_price_series';continue
  stamp=datetime.datetime.fromisoformat(r['published_at'].replace('Z','+00:00')).timestamp()
  pos=bisect.bisect_right([b['ts']for b in a],stamp)
  if pos==len(a):r['price_status']='not_started_or_stale';continue
  f=a[pos:];d=f[0]['date'];delay=(datetime.date.fromisoformat(d)-datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc).date()).days
  if delay>5:r['price_status']='entry_gap_or_prelisting';continue
  r['entry_date']=d;r['entry_open']=f[0]['open'];r['available_days']=len(f)
  sign=1 if r['direction']=='long'else -1
  for n in [5,20,60,120]:
   if len(f)<n:continue
   end=f[n-1]['date'];c=f[n-1]['close'];raw=c/f[0]['open']-1
   if r['group']=='US_equity':
    expected=[x for x in market_dates if d<=x<=end]
    if expected!=[x['date']for x in f[:n]]:continue
   ret={'underlying_return':raw,'direction_return':sign*raw,'exit_date':end,'exit_close':c,
        'adverse_close':min(0,min(sign*(x['close']/f[0]['open']-1)for x in f[:n])),'excess':{}}
   for b in ['SPY','SOXX','QQQ','IWM','^KS11','^TWII']:
    v=lookup.get(b,{})
    if d in v and end in v:
     br=v[end]['close']/v[d]['open']-1;ret['excess'][b]=sign*(raw-br)
   r['results'][str(n)]=ret
 (OUT/'price_coverage.json').write_text(json.dumps({'valid_series':len(prices),'errors':errors,'event_status':dict(collections.Counter(r['price_status']for r in rows))},indent=2))
 aggregate(rows)

def aggregate(rows):
 def select(strict=True,days=21,first=False):
  keep=[];last={}
  for r in rows:
   if strict and not r['strict_eligible']:continue
   k=(r['source_id'],r['price_symbol'],r['direction']);d=datetime.date.fromisoformat(r['published_at'][:10])
   if k in last and (first or (d-last[k]).days<days):continue
   last[k]=d;keep.append(r)
  return keep
 def summary(a,n):
  a=[r for r in a if str(n)in r['results']];v=[r['results'][str(n)]for r in a];vals=[r['direction_return']for r in v]
  bypost=collections.defaultdict(list)
  for r in a:bypost[r['post_id']].append(r['results'][str(n)]['direction_return'])
  pv=[statistics.mean(x)for x in bypost.values()]
  return {'n':len(a),'posts':len(bypost),'tickers':len(set(r['price_symbol']for r in a)),
    'wins':sum(x>0 for x in vals),'hit':sum(x>0 for x in vals)/len(vals)if vals else None,
    'median':statistics.median(vals)if vals else None,'mean':statistics.mean(vals)if vals else None,
    'post_equal_hit':sum(x>0 for x in pv)/len(pv)if pv else None,
    'adverse_20pct_fraction':sum(x['adverse_close']<=-.2 for x in v)/len(v)if v else None,
    'median_excess':{b:statistics.median(z)if(z:=[r['excess'][b]for r in v if b in r['excess']])else None for b in ['SPY','SOXX','IWM']},
    'excess_hit':{b:sum(x>0 for x in z)/len(z)if(z:=[r['excess'][b]for r in v if b in r['excess']])else None for b in ['SPY','SOXX','IWM']}}
 sources=sorted(set(r['source_id']for r in rows));stats={}
 semi={'MU','SNDK','WDC','STX','NVDA','AMD','AVGO','INTC','TSM','ASML','AMAT','LRCX','KLAC','MRVL','QCOM','SOXX','SMH','CRDO','ALAB','ARM','TXN','ADI','NXPI','ON','MPWR','STM','UMC','GFS','TSEM','AMKR','TER','MCHP','SWKS','QRVO','LSCC','POWI','AOSL','SMTC'}
 optics={'AAOI','LITE','COHR','AXTI','POET','AEHR','AEVA','TSEM','AOSL','GFS','POWI','SMTC','FN','MRVL','CRDO'}
 memory={'MU','SNDK','WDC','STX','DRAM'}
 metals={'GLD','SLV','SILJ','GDX','GDXJ'}
 indices={'SPY','QQQ','SOXX','SMH','^GSPC','^NDX','^GDAXI','^FCHI','^DJI'}
 for name,strict,days,first in [('strict21',True,21,False),('strict7',True,7,False),('strict_first',True,0,True),('system21',False,21,False)]:
  chosen=select(strict,days,first)
  stats[name]={}
  for source in sources:
   a=[r for r in chosen if r['source_id']==source and r['group']=='US_equity']
   top3=[x[0]for x in collections.Counter(r['price_symbol']for r in a).most_common(3)]
   all_post_count=collections.Counter(r['post_id']for r in rows if r['source_id']==source)
   stats[name][source]={'selected_all_markets':sum(r['source_id']==source for r in chosen),'selected_us':len(a),
     'horizons':{str(n):summary(a,n)for n in [5,20,60,120]},
     'long':{str(n):summary([r for r in a if r['direction']=='long'],n)for n in [20,60,120]},
     'short':{str(n):summary([r for r in a if r['direction']=='short'],n)for n in [20,60,120]},
     'recent':{str(n):summary([r for r in a if r['published_at']>='2026-06-01'],n)for n in [20,60]},
     'single_security_posts':{str(n):summary([r for r in a if all_post_count[r['post_id']]==1],n)for n in [20,60,120]},
     'removed_top3_tickers':top3,
     'without_top3':{str(n):summary([r for r in a if r['price_symbol']not in top3],n)for n in [20,60,120]},
     'semis':{str(n):summary([r for r in a if r['price_symbol']in semi],n)for n in [20,60,120]},
     'optics':{str(n):summary([r for r in a if r['price_symbol']in optics],n)for n in [20,60,120]},
     'memory':{str(n):summary([r for r in a if r['price_symbol']in memory],n)for n in [20,60,120]},
     'metals_etfs':{str(n):summary([r for r in chosen if r['source_id']==source and r['price_symbol']in metals],n)for n in [20,60,120]},
     'indices':{str(n):summary([r for r in chosen if r['source_id']==source and r['price_symbol']in indices],n)for n in [20,60,120]},
     'other_markets':{str(n):summary([r for r in chosen if r['source_id']==source and r['group']!='US_equity'],n)for n in [20,60,120]}}
 (OUT/'scored_events.json').write_text(json.dumps(rows,ensure_ascii=False))
 (OUT/'statistics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
 for s,v in stats['strict21'].items():
  print(s,[(n,v['horizons'][n]['n'],round(v['horizons'][n]['hit']*100,1)if v['horizons'][n]['hit']is not None else None,round(v['horizons'][n]['median_excess']['SPY']*100,1)if v['horizons'][n]['median_excess']['SPY']is not None else None)for n in ['20','60','120']],flush=True)
if __name__=='__main__':
 if sys.argv[1]=='prep':prep()
 if sys.argv[1]=='fetch':fetch()
 if sys.argv[1]=='calculate':calculate()
 if sys.argv[1]=='summarize':
  with gzip.open(OUT/'scored_events.json.gz','rt') as f:aggregate(json.load(f))
