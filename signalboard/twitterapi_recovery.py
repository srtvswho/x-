"""Offline-tested recovery building blocks; intentionally not wired into production.

A grant is explicit bounded authorization, not an assertion of provider balance.
Do not create one from the expiring smoke exception. Bonus-only execution additionally
requires verified bonus expiry/remaining credits and no payment instrument.
"""
from datetime import datetime, timedelta, timezone
import sqlite3
from .twitterapi_io import Budget, FetchError

HANDLES = ('jukan05', 'aleabitoreddit', 'zephyr_z9', 'austinsemis',
           'DGretta_Author', 'FeroceResearch', 'TradexWhisperer', 'gsmferrari')

def utc(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value,str) else value
    if not dt.tzinfo:
        raise ValueError('timezone required')
    return dt.astimezone(timezone.utc)


def plan_windows(checkpoints, target, *, mode, bootstrap=None):
    """Plan only. Missing verified coverage blocks daily, never guesses from newest post.

    Catch-up advances oldest-first in <=24h chunks. Its explicitly reviewed bootstrap
    starts a NEW coverage range, not a claim that earlier history is complete.
    """
    target = utc(target)
    if mode not in ('daily','catchup'):
        raise ValueError('invalid mode')
    result = []
    for handle in HANDLES:
        point = checkpoints.get(handle)
        if point is None and mode == 'catchup':
            point = (bootstrap or {}).get(handle)
        if point is None:
            result.append({'handle':handle,'status':'coverage_bootstrap_required'})
            continue
        start = utc(point)
        if start >= target:
            result.append({'handle':handle,'status':'up_to_date' if start == target else 'future_checkpoint'})
            continue
        if mode == 'daily' and target-start > timedelta(days=1):
            result.append({'handle':handle,'status':'catchup_required'})
            continue
        end = min(target,start+timedelta(days=1))
        result.append({'handle':handle,'status':'planned','stream':mode,
                       'start':start.isoformat(),'end':end.isoformat(),
                       'max_pages':2,'reserved_search_credits':600})
    return result


class CreditLedger:
    """Persistent worst-case reservations survive errors/restarts/concurrency.

    Reserve 300 credits BEFORE each <=20-result search page, including empty pages.
    Never refund on failure, timeout or uncertain response. Budget deliberately does
    not use recharge_credits as bonus balance. No grant top-ups or implicit renewal.
    Caller must keep the same ledger across jobs; a fresh Actions workspace is unsafe.
    """
    def __init__(self,path):
        self.path=path

    def create_grant(self,grant_id,credits,expires_at):
        if not grant_id or type(credits) is not int or credits <= 0:
            raise ValueError('explicit positive grant required')
        expiry=utc(expires_at).isoformat()
        with sqlite3.connect(self.path) as con:
            con.execute('CREATE TABLE IF NOT EXISTS twitterapi_credit_grants (id TEXT PRIMARY KEY, credits INTEGER NOT NULL, expires_at TEXT NOT NULL, reserved INTEGER NOT NULL DEFAULT 0)')
            con.execute('CREATE TABLE IF NOT EXISTS twitterapi_page_reservations (id TEXT PRIMARY KEY, grant_id TEXT NOT NULL, credits INTEGER NOT NULL)')
            old=con.execute('SELECT credits,expires_at FROM twitterapi_credit_grants WHERE id=?',(grant_id,)).fetchone()
            if old and old != (credits,expiry):
                raise FetchError('grant immutable; cannot replenish or extend')
            con.execute('INSERT OR IGNORE INTO twitterapi_credit_grants VALUES (?,?,?,0)',(grant_id,credits,expiry))

    def reserve(self,grant_id,reservation_id,now):
        with sqlite3.connect(self.path,timeout=30) as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT credits,expires_at,reserved FROM twitterapi_credit_grants WHERE id=?',(grant_id,)).fetchone()
            if not row or utc(now) >= utc(row[1]):
                raise FetchError('missing/expired credit grant')
            if con.execute('SELECT 1 FROM twitterapi_page_reservations WHERE id=?',(reservation_id,)).fetchone():
                raise FetchError('page already attempted; reconcile instead of repeating')
            if row[2]+300 > row[0]:
                raise FetchError('credit grant exhausted')
            con.execute('INSERT INTO twitterapi_page_reservations VALUES (?,?,300)',(reservation_id,grant_id))
            con.execute('UPDATE twitterapi_credit_grants SET reserved=reserved+300 WHERE id=?',(grant_id,))

class LedgerBudget(Budget):
    def __init__(self,ledger,grant_id,logical_attempt_id,*,max_pages=16,clock=None):
        super().__init__(max_pages)
        self.ledger=ledger;self.grant_id=grant_id;self.logical_attempt_id=logical_attempt_id
        self.clock=clock or (lambda:datetime.now(timezone.utc))

    def take(self):
        if not 1 <= self.max_pages <= 16 or self.used >= self.max_pages:
            raise FetchError('page budget exhausted')
        self.ledger.reserve(self.grant_id,f'{self.logical_attempt_id}:page:{self.used+1}',self.clock())
        self.used+=1


def apply_captured_batch(db_path, plans, captured_windows, *, captured_at, checkpoints):
    """Offline replay integration. Never calls provider; no implicit activation.

    Replay on an isolated working DB after recording captured input evidence. Per-author
    atomic receipts remain separate; failures cannot label the entire batch healthy.
    Caller persists receipts independently of any later AI/publication work.
    """
    from .twitterapi_ingest import ingest_window, IngestError
    receipts=[]
    for plan in plans:
        handle=plan['handle']
        if handle not in HANDLES:
            raise ValueError('unapproved handle')
        if plan['status'] != 'planned' or handle not in captured_windows:
            receipts.append({'handle':handle,'fetch_status':plan['status'] if plan['status']!='planned' else 'not_attempted',
                             'checkpoint_changed':False,'summary_status':'not_requested'})
            continue
        try:
            receipts.append(ingest_window(db_path,handle,utc(plan['start']),utc(plan['end']),
                captured_windows[handle],captured_at=utc(captured_at),stream=plan['stream'],
                expected_coverage_end=checkpoints.get(handle)))
        except (IngestError,sqlite3.Error):
            receipts.append({'handle':handle,'fetch_status':'ingest_failed','checkpoint_changed':False,
                             'summary_status':'not_requested'})
    return {'accounts':receipts,'all_eight_planned_windows_verified':len(receipts)==8 and len({r['handle'] for r in receipts})==8
            and all(r.get('coverage_status')=='provider_search_exhausted' for r in receipts),
            'summary_status':'not_requested','publication_status':'not_requested'}
