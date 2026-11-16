"""Durable one-page reader; store is injected and must provide durable CAS.

No file, network client, grants, retries or production jobs are created here.
Store.load() -> (JSON state, revision); store.save(state, revision) -> revision.
A failed/uncertain save or API request never permits automatic replay. The caller
must persist a single journal across runs, and never recreate it to reset quota.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
from .twitterapi_io import Budget, FetchError, Window, search


def _utc(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value,str) else value
    if not isinstance(value,datetime) or not value.tzinfo or value.microsecond:
        raise ValueError('whole-second timezone-aware timestamp required')
    return value.astimezone(timezone.utc)


def _policy(policy):
    required={'grant_id','credit_limit','expires_at','max_pages_per_window','mode','windows'}
    optional={'bonus_only','no_payment_instrument_verified','bonus_expires_at','verified_bonus_credits','max_balance_reads','balance_read_credits','balance_pricing_verified','preflight_mode','recharge_credits'}
    if not isinstance(policy,dict) or not required <= set(policy) or set(policy)-required-optional:
        raise ValueError('explicit exact grant policy required')
    if not isinstance(policy['grant_id'],str) or not policy['grant_id']:
        raise ValueError('grant ID required')
    if type(policy['credit_limit']) is not int or policy['credit_limit'] < 300:
        raise ValueError('positive page credit allowance required')
    if type(policy['max_pages_per_window']) is not int or not 1 <= policy['max_pages_per_window'] <= 100:
        raise ValueError('window cap must be 1..100 pages')
    if policy['mode'] not in ('daily','catchup','recovery') or not isinstance(policy['windows'],list) or not policy['windows']:
        raise ValueError('mode and authorized windows required')
    if 'max_balance_reads' in policy and (type(policy['max_balance_reads']) is not int or not 0 <= policy['max_balance_reads'] <= 16):
        raise ValueError('bounded balance reads required')
    if 'balance_read_credits' in policy and (type(policy['balance_read_credits']) is not int or policy['balance_read_credits'] < 0):
        raise ValueError('nonnegative verified balance tariff required')
    if 'balance_pricing_verified' in policy and policy['balance_pricing_verified'] is not True:
        raise ValueError('balance pricing verification required')
    if 'preflight_mode' in policy and policy['preflight_mode'] != 'dashboard_evidence':
        raise ValueError('unsupported preflight evidence mode')
    if 'recharge_credits' in policy and (type(policy['recharge_credits']) is not int or policy['recharge_credits'] != 0):
        raise ValueError('bonus-only evidence requires zero recharge credits')
    result=deepcopy(policy);result['expires_at']=_utc(result['expires_at']).isoformat()
    normalized=[]
    for window in result['windows']:
        if not isinstance(window,dict) or set(window)!={'handle','start','end'}:
            raise ValueError('exact authorized window required')
        _,scope,_,_=_scope(window['handle'],window['start'],window['end'])
        normalized.append(dict(zip(('handle','start','end'),scope)))
    if len({json.dumps(w,sort_keys=True) for w in normalized}) != len(normalized):
        raise ValueError('duplicate authorized windows')
    result['windows']=normalized
    for flag in ('bonus_only','no_payment_instrument_verified'):
        if flag in result and result[flag] is not True:
            raise ValueError('bonus-only no-payment proof required')
    if 'verified_bonus_credits' in result and (type(result['verified_bonus_credits']) is not int or result['verified_bonus_credits'] < result['credit_limit']):
        raise ValueError('grant exceeds verified bonus allowance')
    if 'bonus_expires_at' in result:
        result['bonus_expires_at']=_utc(result['bonus_expires_at']).isoformat()
        if _utc(result['expires_at']) > _utc(result['bonus_expires_at']):
            raise ValueError('grant outlives bonus proof')
    return result


def select_windows(policy, selected_windows):
    """Validate an explicit invocation subset without changing the lifetime grant.

    One exact window per account, at most eight accounts. A caller must retain
    the complete policy when loading/saving the journal, not initialize a subset
    journal. Dates are normalized instants, including Shanghai UTC+08 offsets.
    """
    policy=_policy(policy)
    if not isinstance(selected_windows,list) or not 1 <= len(selected_windows) <= 8:
        raise ValueError('explicit invocation requires 1..8 windows')
    selected=[];handles=set()
    for window in selected_windows:
        if not isinstance(window,dict) or set(window)!={'handle','start','end'}:
            raise ValueError('exact invocation window required')
        _,scope,_,_=_scope(window['handle'],window['start'],window['end'])
        normalized=dict(zip(('handle','start','end'),scope))
        if normalized not in policy['windows'] or scope[0] in handles:
            raise ValueError('unauthorized window or repeated invocation account')
        handles.add(scope[0]);selected.append(normalized)
    return selected


def initialize_state(policy):
    """Explicit provisioning only; caller must never overwrite an existing journal."""
    return {'schema':'twitterapi-page-journal-v1','config':_policy(policy),'reserved_credits':0,'windows':{}}


def _scope(handle,start,end):
    if not isinstance(handle,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,15}',handle):
        raise ValueError('invalid handle')
    start,end=_utc(start),_utc(end)
    if start >= end:
        raise ValueError('ordered window required')
    scope=(handle.lower(),start.isoformat(),end.isoformat())
    key=hashlib.sha256(json.dumps(scope,separators=(',',':')).encode()).hexdigest()
    return key,scope,start,end


def _check_state(state,policy):
    if not isinstance(state,dict) or state.get('schema')!='twitterapi-page-journal-v1' or state.get('config')!=_policy(policy):
        raise FetchError('journal/policy mismatch; no quota reset or renewal')
    if type(state.get('reserved_credits')) is not int or state['reserved_credits'] < 0 or not isinstance(state.get('windows'),dict):
        raise FetchError('invalid durable journal')
    reads=state.get('balance_reads',[])
    if not isinstance(reads,list) or len(reads)>state['config'].get('max_balance_reads',0) or any(r not in ('pending','zero_recharge') for r in reads) or 'pending' in reads[:-1]:
        raise FetchError('invalid balance request journal')
    pages=0
    for key,entry in state['windows'].items():
        if not isinstance(entry,dict) or not isinstance(entry.get('pages'),list):
            raise FetchError('invalid window journal')
        try:
            scope=tuple(entry['scope'])
            computed,normalized,start,end=_scope(*scope)
            if computed!=key or normalized!=scope or dict(zip(('handle','start','end'),scope)) not in state['config']['windows']:
                raise ValueError()
            cursor='';seen=set();total=0
            for page in entry['pages']:
                if page['request_cursor']!=cursor or cursor in seen:
                    raise ValueError()
                seen.add(cursor)
                rows=_validated_rows(page,scope[0],start,end)
                total+=len(rows)
                cursor=page['next_cursor'] if page['has_next_page'] else ''
                if not page['has_next_page'] and page is not entry['pages'][-1]:
                    raise ValueError()
            if entry['cursor']!=cursor or len(entry['pages'])>state['config']['max_pages_per_window']:
                raise ValueError()
            if entry.get('pending'):
                pending=entry['pending']
                if entry['status']!='uncertain' or pending['page']!=len(entry['pages'])+1 or pending['cursor']!=cursor or pending['credits']!=300:
                    raise ValueError()
            elif entry['pages']:
                expected=('search_exhausted' if total else 'empty_unverified') if not entry['pages'][-1]['has_next_page'] else (
                    'page_cap_partial' if len(entry['pages'])>=state['config']['max_pages_per_window'] else 'continuation_ready')
                if entry['status']!=expected:raise ValueError()
            elif entry['status']!='not_started':raise ValueError()
        except (KeyError,TypeError,ValueError,FetchError):
            raise FetchError('invalid cached scope/page state') from None
        pages += len(entry['pages']) + (1 if entry.get('pending') else 0)
    extra=state.get('one_time_observation')
    extra_reserved=0
    if extra is not None:
        if (not isinstance(extra,dict) or extra.get('operation')!='page2-observation-once-20261115' or
            extra.get('credits')!=300 or extra.get('prior_reserved_credits')!=600 or
            extra.get('original_revision')!='550f29844c8fc676cc922945dad9bd13255890de' or
            extra.get('status') not in ('reserved_uncertain','failed','observed') or
            not any(e.get('pending')==extra.get('original_pending') and e.get('scope')==extra.get('scope') and
                    e.get('cursor')==extra.get('request_cursor') for e in state['windows'].values())):
            raise FetchError('invalid one-time observation accounting')
        extra_reserved=300
    timeline=state.get('timeline_feasibility')
    if timeline is not None:
        allowed=('jukan05','aleabitoreddit','zephyr_z9','austinsemis','DGretta_Author','FeroceResearch','TradexWhisperer','gsmferrari')
        attempts=timeline.get('attempts') if isinstance(timeline,dict) else None
        if (extra is None or timeline.get('operation')!='timeline-feasibility-20261116' or
            timeline.get('historical_gap_preserved') is not True or
            timeline.get('start')!='2026-11-15T16:00:00+00:00' or
            not isinstance(attempts,list) or not 1<=len(attempts)<=8 or
            any(a.get('handle')!=allowed[i] or a.get('credits')!=315 or a.get('endpoint')!='last_tweets' or
                a.get('cursor')!='' or a.get('status') not in ('pending','observed','failed') for i,a in enumerate(attempts))):
            raise FetchError('invalid timeline observation accounting')
        extra_reserved+=315*len(attempts)
    if 'timeline_daily' in state:
        from .twitterapi_timeline_daily import daily_reserved_credits
        extra_reserved+=daily_reserved_credits(state)
    balance_reserved=len(reads)*state['config'].get('balance_read_credits',0)+extra_reserved
    if pages*300 + balance_reserved != state['reserved_credits'] or state['reserved_credits']>state['config']['credit_limit']:
        raise FetchError('reservation accounting mismatch')


def balance_preflight(client,store,*,expected_policy,now=None):
    """No unknown-price requests; known cost joins the same lifetime allowance.

    Legacy policies remain readable but cannot initiate unpriced balance calls.
    Even a verified zero-price read requires explicit policy proof and expiry.
    """
    state,revision=store.load();_check_state(state,expected_policy)
    config=state['config']
    if config.get('balance_pricing_verified') is not True or 'balance_read_credits' not in config:
        raise FetchError('balance request pricing unverified; no call')
    if now is None or _utc(now) >= _utc(config['expires_at']):
        raise FetchError('current time required within credit grant')
    state=deepcopy(state);reads=state.setdefault('balance_reads',[])
    cap=config.get('max_balance_reads',0);cost=config['balance_read_credits']
    if not isinstance(reads,list) or any(r != 'zero_recharge' for r in reads):
        raise FetchError('uncertain balance read requires reconciliation')
    if len(reads)>=cap:raise FetchError('balance request cap reached')
    if state['reserved_credits']+cost > config['credit_limit']:
        raise FetchError('durable credit allowance exhausted')
    reads.append('pending');state['reserved_credits']+=cost
    revision=store.save(state,revision)
    try:
        if client.credits()!=0:raise FetchError('bonus-only candidate refuses paid balance')
        reads[-1]='zero_recharge';store.save(state,revision)
    except Exception:
        raise FetchError('balance response or persistence uncertain; no automatic retry') from None


class _Response:
    def __init__(self,data):self.data=data
    def get(self,path,params):return self.data


def _validated_rows(data,handle,start,end):
    # Reuse strict schema/author/time/string-ID validation without network.
    return search(_Response(data),handle,start,end,Budget(1),1).tweets


def _window(entry,scope):
    rows={}
    for page in entry['pages']:
        for row in page['tweets']:
            old=rows.get(row['id'])
            if old and (old['text'] != row['text'] or old['createdAt'] != row['createdAt']):
                raise FetchError('conflicting repeated post across pages')
            rows.setdefault(row['id'],deepcopy(row))
    status=entry['status']
    return Window(list(rows.values()),status=='search_exhausted',status,len(entry['pages']),request_scope=scope)


def cached_window(store,handle,start,end,*,expected_policy):
    key,scope,_,_=_scope(handle,start,end)
    state,_=store.load();_check_state(state,expected_policy)
    entry=state['windows'].get(key)
    if entry is None:return Window(request_scope=scope)
    if tuple(entry.get('scope',())) != scope:raise FetchError('cached scope mismatch')
    return _window(entry,scope)


def _current_time():
    return datetime.now(timezone.utc)


def advance_page(client,store,handle,start,end,*,now,expected_policy):
    """At most ONE official search call, only after durable reservation succeeds.

    On timeout/provider/schema/save failure the durable pending record is an
    uncertain attempt. It consumes quota permanently and blocks automatic retry.
    A returned page is cached before completion can be used for DB ingestion.
    """
    key,scope,start,end=_scope(handle,start,end)
    now=_utc(now);policy=_policy(expected_policy)
    if dict(zip(('handle','start','end'),scope)) not in policy['windows']:
        raise FetchError('window not authorized by grant')
    state,revision=store.load();_check_state(state,policy);state=deepcopy(state)
    if now >= _utc(policy['expires_at']):raise FetchError('credit grant expired')
    entry=state['windows'].get(key)
    if entry is None:
        entry={'scope':list(scope),'pages':[],'cursor':'','status':'not_started','pending':None}
        state['windows'][key]=entry
    if tuple(entry.get('scope',())) != scope:raise FetchError('cached scope mismatch')
    if entry.get('pending'):raise FetchError('uncertain page requires reconciliation; no retry')
    if entry['status'] in ('search_exhausted','empty_unverified','page_cap_partial'):
        return _window(entry,scope)
    if len(entry['pages']) >= policy['max_pages_per_window']:
        raise FetchError('inconsistent window page cap')
    if state['reserved_credits']+300 > policy['credit_limit']:
        raise FetchError('durable credit allowance exhausted')
    cursor=entry['cursor']
    entry['pending']={'page':len(entry['pages'])+1,'cursor':cursor,'reserved_at':now.isoformat(),'credits':300}
    entry['status']='uncertain'
    state['reserved_credits']+=300
    reserved_revision=store.save(state,revision)  # must be durable before call
    params={'query':f'from:{handle} since_time:{int(start.timestamp())} until_time:{int(end.timestamp())}',
            'queryType':'Latest','cursor':cursor}
    try:
        if _current_time() >= _utc(policy['expires_at']):
            raise FetchError('grant expired after durable reservation')
        data=client.get('/twitter/tweet/advanced_search',params)
        rows=_validated_rows(data,handle,start,end)
        more,next_cursor=data['has_next_page'],data['next_cursor']
        previous_cursors={p['request_cursor'] for p in entry['pages']}
        if more and (not next_cursor or next_cursor==cursor or next_cursor in previous_cursors):
            raise FetchError('stalled/repeated cursor')
        # Cache only verified fields and full validated original tweet dictionaries.
        entry['pages'].append({'request_cursor':cursor,'next_cursor':next_cursor,'has_next_page':more,'tweets':deepcopy(rows)})
        entry['pending']=None
        entry['cursor']=next_cursor if more else ''
        total_rows=sum(len(p['tweets']) for p in entry['pages'])
        entry['status']=('search_exhausted' if total_rows else 'empty_unverified') if not more else (
            'page_cap_partial' if len(entry['pages'])>=policy['max_pages_per_window'] else 'continuation_ready')
        result=_window(entry,scope)  # cross-page duplicate validation before save
        store.save(state,reserved_revision)
        return result
    except Exception:
        # Do not log provider body/error/key or overwrite durable uncertain marker.
        raise FetchError('page response or persistence uncertain; no automatic retry') from None
