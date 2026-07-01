"""强制 since=2026-06-30 until=2026-07-01, 看 jukan 6-30 23:19 之后推文."""
import sys
sys.path.insert(0, '/workspace')
from signalboard.scraper import _call_actor, build_run_input
from datetime import date
import os, json
from apify_client import ApifyClient

token = os.environ['APIFY_TOKEN']
client = ApifyClient(token)

handle = 'jukan05'
# 强制 since=6-30 until=7-1 (跟当前 cron 行为一样)
run_input = build_run_input(
    handle=handle,
    start=date(2026, 6, 30),
    end=date(2026, 7, 1),
    max_per_month=50,
    sort='Latest',
    disable_maximization=True,
)
print('searchTerms:', run_input['searchTerms'])

# 直接调 actor (用 _call_actor)
items = _call_actor(run_input, token, client=client)
print(f'\nApify 返 {len(items)} 条:')
for it in items:
    pub = it.get('createdAt') or it.get('date') or ''
    txt = (it.get('text') or '')[:80].replace('\n', ' ')
    print(f'  {pub}  {txt}')
