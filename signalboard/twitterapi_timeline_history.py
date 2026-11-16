"""OFFLINE candidate; injected transport/store only. One frozen first capture or supplied cached page; never retries.

Opaque cursors cannot prove snapshot consistency: monotone timestamps, no cursor
cycles and no conflicting IDs reject visible drift, but undetectable omissions
remain a provider limitation. Completion is provider traversal coverage only.
"""
from copy import deepcopy
import hashlib
import json
from datetime import datetime, timezone
from .twitterapi_timeline import accumulate, TimelineError
from .twitterapi_timeline_daily import utc, HANDLES, EXPIRES

PAGE_CREDITS = 315
DAILY_FLOOR = 15120
HISTORY_CAP = 11460
END = '2026-11-15T16:00:00+00:00'  # Nov 16 midnight Shanghai
OPERATION = 'timeline-historical-catchup-20261116'
BOUNDARIES = {'aleabitoreddit': '2026-11-12T07:44:39Z', 'austinsemis': '2026-11-12T07:44:40Z', 'zephyr_z9': '2026-11-12T07:44:39Z', 'jukan05': '2026-11-12T07:44:37Z', 'feroceresearch': '2026-11-12T07:44:40Z', 'dgretta_author': '2026-11-12T07:44:38Z', 'gsmferrari': '2026-11-12T07:44:36Z', 'tradexwhisperer': '2026-11-12T07:44:40Z'}
BASE_DB_SHA256 = '608b99610336647620cc60d2c7218536651d8c1950926dfcf617f4ab1d701226'


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def history_reserved_credits(state):
    history=state.get('timeline_history')
    if history is None:return 0
    if (history.get('operation')!=OPERATION or history.get('daily_floor')!=DAILY_FLOOR or
        history.get('history_cap')!=HISTORY_CAP or history.get('end')!=END or
        set(history.get('accounts',{}))!=set(HANDLES)):
        raise ValueError('invalid_history_policy')
    if history.get('legacy_digest')!=_fingerprint({k:state.get(k) for k in ('config','windows','one_time_observation','timeline_feasibility')}):
        raise ValueError('legacy_state_changed')
    total=0
    for handle,account in history['accounts'].items():
        if account['seed_hash']!=_fingerprint(account['seed_pages']):raise ValueError('history_seed_changed')
        start=utc(account['start'])
        if start != utc(BOUNDARIES[handle]):
            raise ValueError('history_scope_invalid')
        events=account['events'];claimed=False;page=len(account['seed_pages']);pages=list(account['seed_pages'])
        for e in events:
            if e['kind']=='reserved':
                if claimed or e['credits']!=PAGE_CREDITS or e['page']!=page+1 or (page > 0 and not e['cursor']) or (page == 0 and e['cursor'] != ''):
                    raise ValueError('invalid_history_reservation')
                previous=accumulate(pages,handle,start,utc(END))
                if previous.complete or previous.reason not in ('not_started','continuation_required') or e['cursor']!=previous.next_cursor:
                    raise ValueError('invalid_history_cursor_chain')
                claimed=True;total+=PAGE_CREDITS
            elif e['kind']=='response':
                if not claimed or e['page']!=page+1:raise ValueError('invalid_history_response')
                pages.append(e['payload']);claimed=False;page+=1
            else:raise ValueError('invalid_history_event')
        if claimed and account['status']!='uncertain':raise ValueError('history_pending_not_blocked')
        if account['status'] in ('ready','complete'):
            verified=accumulate(pages,handle,start,utc(END))
            if account['status']=='complete' and not verified.complete:raise ValueError('history_false_completion')
            if account['status']=='ready' and (verified.complete or verified.reason not in ('not_started','continuation_required')):raise ValueError('history_false_ready')
    if total//PAGE_CREDITS>36 or total>HISTORY_CAP:raise ValueError('history_cap_exceeded')
    return total


def _check(state):
    from .twitterapi_paging import _check_state
    _check_state(state,state['config'])  # Requires the companion accounting patch.
    c=state['config']
    if (c.get('grant_id')!='bonus-recovery-20261115-7d-30000' or c.get('credit_limit')!=30000 or
        utc(c['expires_at'])!=EXPIRES or c.get('bonus_only') is not True or
        c.get('no_payment_instrument_verified') is not True or c.get('recharge_credits')!=0):
        raise ValueError('invalid_history_grant')


def initialize_history(store, seeds, boundaries):
    """Create an independent frozen history operation, never an old search retry.

    seeds: {canonical_handle: [] or [full_raw_first_response]}; boundaries: exact per
    account database last_fetched UTC strings. Empty seeds authorize a first capture.
    Existing history must never be reset, even when it is stopped or uncertain.
    """
    state,revision=store.load();_check(state)
    if 'timeline_history' in state:raise ValueError('history_already_exists')
    if set(seeds)!=set(HANDLES) or set(boundaries)!=set(HANDLES):raise ValueError('history_accounts_missing')
    accounts={}
    for handle in HANDLES:
        pages=seeds[handle]
        if not isinstance(pages,list) or len(pages)>1:raise ValueError('full_cached_first_page_required')
        if utc(boundaries[handle])!=utc(BOUNDARIES[handle]):raise ValueError('history_anchor_mismatch')
        start=utc(boundaries[handle]);window=accumulate(pages,handle,start,utc(END))
        if not window.complete and window.reason not in ('continuation_required','not_started'):raise ValueError('unusable_cached_first_page')
        accounts[handle]={'start':start.isoformat(),'seed_pages':deepcopy(pages),
                         'seed_hash':_fingerprint(pages),'events':[],
                         'status':'complete' if window.complete else 'ready'}
    state=deepcopy(state)
    state['timeline_history']={'operation':OPERATION,'daily_floor':DAILY_FLOOR,
                              'history_cap':HISTORY_CAP,'end':END,'accounts':accounts,
                              'legacy_digest':_fingerprint({k:state.get(k) for k in ('config','windows','one_time_observation','timeline_feasibility')})}
    _check(state);store.save(state,revision)


def advance_history(client,store,handle,*,now,clock=None):
    """At most one continuation request; reserve before call, save before validate.

    Transport/save uncertainty blocks automatic retry. Any invalid response is
    retained for diagnosis and never reused as permission for a fresh request.
    """
    clock=clock or (lambda: datetime.now(timezone.utc).replace(microsecond=0))
    state,revision=store.load();_check(state)
    if handle not in HANDLES:raise ValueError('history_account_invalid')
    if utc(now)>=EXPIRES or utc(clock())>=EXPIRES:return {'status':'expired'}
    state=deepcopy(state);history=state['timeline_history'];account=history['accounts'][handle]
    if account['status'] not in ('ready','complete'):return {'status':account['status']}
    if any(a['status'] not in ('ready','complete') for a in history['accounts'].values()):
        return {'status':'blocked_previous_attempt'}
    pages=account['seed_pages']+[e['payload'] for e in account['events'] if e['kind']=='response']
    window=accumulate(pages,handle,utc(account['start']),utc(END))
    if window.complete:return {'status':'complete','tweets':window.tweets,'reason':window.reason}
    if window.reason not in ('continuation_required','not_started'):return {'status':'incomplete'}
    if history_reserved_credits(state)+PAGE_CREDITS>HISTORY_CAP:return {'status':'history_budget_stop'}
    if state['reserved_credits']+PAGE_CREDITS+DAILY_FLOOR>30000:return {'status':'daily_reserve_stop'}
    if utc(clock())>=EXPIRES:return {'status':'expired'}
    cursor=window.next_cursor
    claim={'kind':'reserved','page':len(pages)+1,'cursor':cursor,'credits':PAGE_CREDITS}
    account['events'].append(claim);account['status']='uncertain'
    state['reserved_credits']+=PAGE_CREDITS
    revision=store.save(state,revision)
    client.deadline=EXPIRES
    if utc(clock())>=EXPIRES:
        account['status']='uncertain';account['reason']='expired_after_reservation';store.save(state,revision)
        return {'status':'expired_after_reservation'}
    try:
        payload=client.get('/twitter/user/last_tweets',{'userName':handle,'cursor':cursor,'includeReplies':'true'})
    except Exception:
        return {'status':'uncertain'}
    account['events'].append({'kind':'response','page':len(pages)+1,'payload':deepcopy(payload)})
    revision=store.save(state,revision)  # failure leaves durable uncertain claim
    try:
        window=accumulate(pages+[payload],handle,utc(account['start']),utc(END))
    except TimelineError as error:
        account['status']='invalid_response';account['reason']=error.code
        store.save(state,revision)
        return {'status':'invalid_response','reason':error.code}
    prior_ids={row['id'] for previous in pages for row in previous['data']['tweets']}
    new_rows=payload['data']['tweets']
    if not window.complete and new_rows and all(row['id'] in prior_ids for row in new_rows):
        account['status']='incomplete';account['reason']='pagination_no_progress'
        store.save(state,revision)
        return {'status':'incomplete','reason':'pagination_no_progress'}
    account['status']='complete' if window.complete else ('ready' if window.reason=='continuation_required' else 'incomplete')
    store.save(state,revision)
    return {'status':account['status'],'reason':window.reason,'tweets':window.tweets}


def run_history(client,store,*,now,clock=None,max_steps=36):
    """Independent bounded runner, global fail-stop; no ingest or publication."""
    if type(max_steps) is not int or not 1<=max_steps<=36:raise ValueError('invalid_step_cap')
    steps=0
    for handle in HANDLES:
        while True:
            state,_=store.load();_check(state)
            account=state['timeline_history']['accounts'][handle]
            if account['status']=='complete':break
            if steps>=max_steps:return {'status':'invocation_cap','steps':steps}
            result=advance_history(client,store,handle,now=now,clock=clock)
            steps+=1
            if result['status']=='complete':break
            if result['status']!='ready':return dict(result,handle=handle,steps=steps)
    return {'status':'complete','steps':steps,'ready_for_offline_ingest':True}


def completed_attempts(state):
    """Return all-eight fully revalidated historical windows, never partials."""
    _check(state);history=state['timeline_history'];attempts=[]
    for handle in HANDLES:
        account=history['accounts'][handle]
        if account['status']!='complete':raise ValueError('history_incomplete')
        pages=account['seed_pages']+[e['payload'] for e in account['events'] if e['kind']=='response']
        window=accumulate(pages,handle,utc(account['start']),utc(END))
        if not window.complete:raise ValueError('history_incomplete')
        attempts.append({'handle':handle,'start':account['start'],'end':END,
                         'complete':True,'reason':window.reason,'tweets':window.tweets,
                         'pages':pages,'credits':sum(e.get('credits',0) for e in account['events'])})
    return attempts
