#!/usr/bin/env python3
"""Offline quote-schema audit. Original model responses and report are retained.

This does not re-extract with a new context/prompt. It only re-evaluates persisted
model proposals against corrected source metadata, followed by explicit reviewed
post/security decisions. It cannot recover signals omitted by the original model.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import author_mvp_20260913 as m


def candidates(source):
    raw={str(p['id']):p for f in (source/'raw').glob('*.json') for p in json.loads(f.read_text()) if p.get('id')}
    selected={p['id']:p for values in json.loads((source/'selected.json').read_text()).values() for p in values}
    ledger=m.Ledger(source/'ledger.json')
    original_out=m.OUT
    m.OUT=source/'schema_audit'
    labels={}
    changes=[]
    try:
        for row in ledger.rows:
            if row['kind']!='ai' or row['status']!='SUCCESS':continue
            batch=[]
            for ident in row['metadata']['post_ids']:
                old=selected[ident]
                new=m.normalize(raw[ident],old['author'])
                if not new or new['raw_hash']!=old['raw_hash']:
                    raise m.Stop('Raw text/identity mismatch in offline audit')
                if new['quote_context_missing']!=old['quote_context_missing']:
                    changes.append(ident)
                batch.append(new)
            try:
                outputs=m.decode_labels(json.loads((source/'model'/f'{row["key"]}.json').read_text()),batch,row['key'])
            except m.OutputError:continue
            for p in outputs:labels[p['id']]=p
        m.save(m.OUT/'labels.json',list(labels.values()))
        events=[]
        for p in labels.values():
            for s in p['signals']:
                at=p['text'].find(s['quote'])
                events.append(dict(s,id=p['id'],author=p['author'],published_at=p['published_at'],
                                   raw_hash=p['raw_hash'],context=p['text'][max(0,at-250):at+len(s['quote'])+300],
                                   text=p['text'],url=p['url']))
        events.sort(key=lambda e:(e['author'],e['published_at'],e['ticker']))
        for i,e in enumerate(events):e['audit_index']=i
        m.save(m.OUT/'candidates.json',events)
        m.save(m.OUT/'metadata.json',{'source_policy':m.VERSION,'audit_policy':'quote-schema-20260914',
                    'changed_post_ids':sorted(set(changes)),'paid_calls':0,
                    'new_model_interpretations':False,'model_was_not_given_quoted_body':True,
                    'limitation':'Revalidates existing proposals only; omissions caused by the old context flag remain possible.'})
        print(json.dumps({'labels':len(labels),'candidates':len(events),'authors':dict(Counter(e['author'] for e in events)),'corrected_post_flags':len(set(changes))}))
    finally:m.OUT=original_out


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=m.OUT)
    args=parser.parse_args()
    candidates(args.source)
