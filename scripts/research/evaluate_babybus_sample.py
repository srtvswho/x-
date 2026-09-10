import json,datetime,statistics,csv
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
from pathlib import Path
p=json.load(open('combined_posts.json'))
spec=[(16,'NVDA',1),(17,'INTC',-1),(18,'MU',1),(23,'CRWV',1),(31,'CRWV',-1),(31,'NBIS',-1),(55,'SOXX',1),(84,'GOOGL',-1),(90,'LITE',-1),(109,'NFLX',-1),(131,'MU',-1),(136,'INTC',-1),(138,'LITE',1),(142,'000660.KS',1),(153,'MU',-1),(162,'NVDA',-1),(163,'SOXX',-1),(169,'SPY',-1),(203,'SNDK',-1),(258,'SOXX',-1),(264,'NVDA',-1),(269,'MU',1),(274,'GLD',1),(274,'SLV',1),(276,'SPY',1),(336,'META',1),(347,'GDXU',-1),(414,'AAOI',1),(414,'LITE',1),(414,'NVDA',1),(421,'SOXX',1),(434,'MU',1),(449,'AVGO',1),(460,'CBRS',1),(465,'SLV',1),(487,'SLV',-1),(492,'GLD',-1),(515,'RKLB',1),(516,'CRWV',1)]
# Exclude pure waiting, leveraged-profit-taking and retrospectively disclosed rotation.
excluded={90:'wait to add, no fresh directional trade',347:'profit-taking, not a bearish call',465:'retrospective rotation'}
spec=[s for s in spec if s[0] not in excluded]
prices=json.load(open('audit_prices.json'))
bars={}
for t,v in prices.items():
 if 'quote' not in v:continue
 q=v['quote'];z=ZoneInfo(v['timezone']);adj=v.get('adjclose')
 vals=[]
 for i,ts in enumerate(v['timestamp']):
  if not q['open'][i] or not q['close'][i]:continue
  dt=datetime.datetime.fromtimestamp(ts,z)
  if dt.date()>datetime.date(2026,9,9):continue
  # Directional price returns: split-adjusted OHLC, dividends excluded, matching old audit.
  vals.append({'ts':ts,'date':dt.date().isoformat(),**{k:q[k][i] for k in ['open','high','low','close']}})
 bars[t]=vals
rows=[]
for i,t,sign in spec:
 x=p[i];dt=parsedate_to_datetime(x['createdAt']);f=[b for b in bars.get(t,[]) if b['ts']>dt.timestamp()]
 group='Korea' if t.endswith('.KS') else 'metals' if t in ('GLD','SLV','GDXU') else 'US equities'
 row={'i':i,'id':x['id'],'date_utc':dt.date().isoformat(),'timestamp_utc':dt.isoformat(),'ticker':t,'direction':sign,'group':group,'url':x['url'],'text':x['text'],'context':(x.get('quote')or{}).get('text',''),'entry_date':f[0]['date'] if f else None,'entry_open':f[0]['open'] if f else None,'available_days':len(f),'returns':{}}
 benchmark='^KS11' if group=='Korea' else 'SPY'
 for n in [5,20,60,120]:
  if len(f)<n:continue
  raw=f[n-1]['close']/f[0]['open']-1
  bv={b['date']:b for b in bars.get(benchmark,[])}
  br=bv[f[n-1]['date']]['close']/bv[f[0]['date']]['open']-1 if f[n-1]['date'] in bv and f[0]['date'] in bv else None
  sv={b['date']:b for b in bars.get('SOXX',[])}
  sr=sv[f[n-1]['date']]['close']/sv[f[0]['date']]['open']-1 if f[n-1]['date'] in sv and f[0]['date'] in sv else None
  row['returns'][str(n)]={'raw_price_return':raw,'direction_return':sign*raw,'exit_date':f[n-1]['date'],'exit_close':f[n-1]['close'],'benchmark_price_return':br,'excess_direction':sign*(raw-br) if br is not None else None,'soxx_excess_direction':sign*(raw-sr) if sr is not None else None,'adverse_close':min(sign*(b['close']/f[0]['open']-1) for b in f[:n])}
 rows.append(row)
def dedup(days):
 out=[];last={}
 for r in rows:
  key=(r['ticker'],r['direction']);d=datetime.date.fromisoformat(r['date_utc'])
  if key in last and (d-last[key]).days<days:continue
  last[key]=d;out.append(r)
 return out
summ={}
for days in [7,21]:
 keep=dedup(days)
 summ[days]={}
 for group in ['US equities','Korea','metals']:
  summ[days][group]={}
  for n in [5,20,60,120]:
   a=[r for r in keep if r['group']==group and str(n) in r['returns']]
   rets=[r['returns'][str(n)] for r in a]
   vals=[r['direction_return'] for r in rets];exc=[r['excess_direction'] for r in rets if r['excess_direction'] is not None]
   sx=[r['soxx_excess_direction'] for r in rets if r['soxx_excess_direction'] is not None]
   summ[days][group][n]={'n':len(a),'wins':sum(v>0 for v in vals),'hit':sum(v>0 for v in vals)/len(a) if a else None,'median':statistics.median(vals) if vals else None,'median_excess':statistics.median(exc) if exc else None,'median_soxx_excess':statistics.median(sx) if sx else None}
json.dump({'excluded':excluded,'spec_count':len(rows),'dedup_7_count':len(dedup(7)),'dedup_21_count':len(dedup(21)),'summary':summ,'rows':rows},open('evaluation.json','w'),ensure_ascii=False,indent=2)
print(json.dumps(summ,ensure_ascii=False,indent=2))
for r in dedup(21):
 print(r['i'],r['date_utc'],r['ticker'],r['direction'],r['entry_date'],{k:round(v['direction_return']*100,2) for k,v in r['returns'].items()})
