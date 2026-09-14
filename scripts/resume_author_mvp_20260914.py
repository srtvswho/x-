#!/usr/bin/env python3
"""Resume the frozen sample using its original ledger; no scraper entry point."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import author_mvp_20260913 as m

POLICY = ROOT/'config/author_mvp_resume_20260914.json'
CLAIM = m.OUT/'resume-20260914-claim.json'


def policy():
    return json.loads(POLICY.read_text())


def verify_restored():
    p = policy()
    for name, field in [('ledger.json','initial_ledger_sha256'),('selected.json','selected_sha256'),('coverage.json','coverage_sha256')]:
        if hashlib.sha256((m.OUT/name).read_bytes()).hexdigest() != p[field]:
            raise m.Stop('Restored '+name+' does not match the original immutable artifact')
    rows = m.Ledger(m.OUT/'ledger.json').rows
    if len(rows) != p['initial_ledger_rows'] or sum(r['reserved_micro_usd'] for r in rows) != p['initial_reserved_micro_usd']:
        raise m.Stop('Initial reservations do not reconcile')
    if any(r['status'] not in {'SUCCESS','SUCCEEDED'} for r in rows):
        raise m.Stop('An original request has an uncertain outcome')
    claim = json.loads((m.OUT/'claim.json').read_text())
    if claim['run_id'] != p['source_run_id'] or claim['config_hash'] != m.digest(m.config()):
        raise m.Stop('Original campaign identity changed')
    return rows


def selected_posts():
    selected = json.loads((m.OUT/'selected.json').read_text())
    return selected, {p['id']:p for values in selected.values() for p in values}


def recover_labels():
    """Revalidate existing model output without another provider request."""
    selected, posts = selected_posts()
    labels, retry_ids, recovered = {}, set(), []
    for row in m.Ledger(m.OUT/'ledger.json').rows:
        if row['kind'] != 'ai':
            continue
        batch = [posts[i] for i in row['metadata']['post_ids']]
        path = m.OUT/'labels'/f'{row["key"]}.json'
        if path.exists():
            results = json.loads(path.read_text())
            if set(p['id'] for p in results) != set(p['id'] for p in batch):
                raise m.Stop('Saved label identity mismatch')
        else:
            raw = m.OUT/'model'/f'{row["key"]}.json'
            if not raw.exists() or row['status'] != 'SUCCESS':
                raise m.Stop('Cannot recover a request without a known saved response')
            try:
                results = m.decode_labels(json.loads(raw.read_text()), batch, row['key'])
                m.save(path,results)
                recovered.extend(p['id'] for p in batch)
            except m.OutputError:
                retry_ids.update(p['id'] for p in batch)
                continue
        for result in results:
            if result['raw_hash'] != posts[result['id']]['raw_hash']:
                raise m.Stop('Saved post text changed')
            labels[result['id']] = result
    retry_ids -= labels.keys()
    m.save(m.OUT/'offline_recovery.json',{'recovered_without_api':recovered,'retry_ids':sorted(retry_ids),
                                         'reused_label_count':len(labels),'paid_calls':0})
    return selected, posts, labels, retry_ids


def claim_resume():
    if CLAIM.exists():
        raise m.Stop('This continuation was already claimed; reconcile its newer artifact first')
    verify_restored()
    if not os.getenv('DEEPSEEK_API_KEY'):
        raise m.Stop('Missing configured DEEPSEEK_API_KEY')
    models = m.request('GET',m.MODEL_API+'/models',token=os.environ['DEEPSEEK_API_KEY'])
    if m.config()['model'] not in [x['id'] for x in models['data']]:
        raise m.Stop('Reviewed Flash model unavailable')
    m.save(CLAIM,{'status':'claimed','run_id':os.environ['GITHUB_RUN_ID'],
                  'original_run_id':policy()['source_run_id'],'policy_hash':m.digest(policy()),
                  'initial_reserved_micro_usd':policy()['initial_reserved_micro_usd'],
                  'claimed_at':m.now().isoformat(),'new_budget':False})


def make_report(labels, selected, failures, status):
    coverage = json.loads((m.OUT/'coverage.json').read_text())
    screening = {}
    for author in m.AUTHORS:
        pool = json.loads((m.OUT/'normalized'/f'{author}.json').read_text())
        _, screening[author] = m.select_candidates(pool,m.AUTHORS[author][1])
    result = m.report(list(labels.values()),coverage,screening)
    result['processing'] = {'status':status,'selected':{k:len(v) for k,v in selected.items()},
                             'parsed':dict(Counter(p['author'] for p in labels.values())),
                             'unresolved_post_ids':failures,'scrape_calls_this_continuation':0,
                             'original_run_id':policy()['source_run_id']}
    result['status'] = status
    m.save(m.OUT/'report.json',result)
    return result


def run():
    claim = json.loads(CLAIM.read_text())
    if claim['run_id'] != os.getenv('GITHUB_RUN_ID') or claim['status'] != 'claimed' or claim['policy_hash'] != m.digest(policy()):
        raise m.Stop('Missing exact continuation claim')
    verify_restored()
    ledger = m.Ledger(m.OUT/'ledger.json')
    selected, posts, labels, retry_ids = recover_labels()
    claim['status'] = 'running'
    m.save(CLAIM,claim)
    invalid, failures, stopped = set(retry_ids), {}, None
    def process(batch):
        try:
            results = m.analyze(batch,ledger)
        except m.OutputError as error:
            return str(error)
        for p in results: labels[p['id']] = p
        return None
    try:
        queues = {a:[p for p in values if p['id'] not in labels and p['id'] not in retry_ids] for a,values in selected.items()}
        while any(queues.values()):
            for author in m.AUTHORS:
                if not queues[author]: continue
                batch,queues[author] = queues[author][:5],queues[author][5:]
                error = process(batch)
                if error:
                    invalid.update(p['id'] for p in batch)
                    print(f'Isolated malformed batch ({len(batch)} posts); other batches continue',flush=True)
                m.save(m.OUT/'progress.json',{'parsed':len(labels),'selected':len(posts),
                                             'isolated_invalid':len(invalid),'at':m.now().isoformat(),
                                             'reserved_upper_usd':sum(r['reserved_micro_usd'] for r in ledger.rows)/1e6})
                print(f'Parsed {len(labels)}/{len(posts)}; reserved ${sum(r["reserved_micro_usd"] for r in ledger.rows)/1e6:.6f}',flush=True)
        # Exactly one individual attempt for each known malformed-output post.
        # Never retry transport errors or requests with uncertain billing.
        for ident in sorted(invalid-labels.keys()):
            error = process([posts[ident]])
            if error: failures[ident] = error
    except m.Stop as error:
        stopped = str(error)
    except Exception as error:
        stopped = 'Unexpected '+type(error).__name__+'; preserve ledger, no automatic network retry'
    finally:
        for ident in posts.keys()-labels.keys():
            failures.setdefault(ident,stopped or 'unresolved_format')
        status = 'complete' if not failures and not stopped else 'partial'
        claim.update(status=status,parsed=len(labels),selected=len(posts),failure_count=len(failures),
                     stopped_reason=stopped,finished_at=m.now().isoformat())
        m.save(CLAIM,claim)
        m.save(m.OUT/'unresolved.json',failures)
        m.receipt()
        # Always try the free report stage, even if a paid stage was stopped.
        make_report(labels,selected,failures,status)
        original = json.loads((m.OUT/'claim.json').read_text())
        original['previous_failure'] = {k:original[k] for k in ['error_type','reason','last_updated'] if k in original}
        for field in ['error_type','reason']:
            original.pop(field,None)
        original.update(status='screening_complete_not_alpha_proven' if status=='complete' else 'partial',
                        completed_labels=len(labels),continued_by=claim['run_id'])
        m.save(m.OUT/'claim.json',original)
        m.receipt()
    if stopped: raise m.Stop(stopped)
    if failures: raise m.Stop('Partial output; unresolved posts listed, no fresh-budget rerun allowed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['check','claim','run','recover'])
    args=parser.parse_args()
    try:
        if args.action=='check':
            verify_restored()
            print('Original artifact and $1.494501 cumulative reservation verified; no paid calls')
        elif args.action=='claim': claim_resume()
        elif args.action=='recover':
            selected,posts,labels,retry = recover_labels()
            print(json.dumps({'recovered_labels':len(labels),'pending':len(posts)-len(labels),'retry_needed':len(retry)}))
        else: run()
    except m.Stop as error:
        print('STOP: '+str(error),file=sys.stderr)
        raise SystemExit(2)
