"""Source-bound corrections shared by tracking, research labels and publication.

Never rewrite raw posts or old model interpretations. A changed source text
invalidates the adjudication and leaves the affected signal pending review.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

VERSION = 'semantic-review-v1'
PATH = Path(__file__).resolve().parents[1] / 'config/semantic_reviews.json'

@lru_cache(maxsize=1)
def reviews():
    document = json.loads(PATH.read_text())
    assert document['version'] == VERSION
    return document['reviews']

def adjudication(source_id, post_id, symbol, text):
    matches = [r for r in reviews() if r['source_id'] == source_id
               and r['post_id'] == str(post_id) and r['ticker'] in ('*', symbol)]
    if not matches:
        return None
    review = dict(matches[0])
    if hashlib.sha256((text or '').encode()).hexdigest() != review['raw_sha256']:
        review.update(decision='quarantine', direction=None, reason='原文与已核读版本不一致，等待重新核实。')
    return {k:v for k,v in review.items() if k != 'raw_text'}

def apply_reviews(events):
    result = []
    for original in events:
        e = dict(original)
        review = adjudication(e['source_id'],e['post_id'],e['ticker'],e.get('raw_text',''))
        if review:
            if review['decision'] != 'correct_direction':
                continue
            e.update(direction=review['direction'], semantic_review=review,
                     original_direction=e.get('original_direction', e['direction']))
        result.append(e)
    return list({(e['source_id'],str(e['post_id']),e['ticker'],e['direction']):e for e in result}.values())

def post_reviews(source_id, post_id, text):
    symbols = {r['ticker'] for r in reviews() if r['source_id']==source_id and r['post_id']==str(post_id)}
    return [adjudication(source_id,post_id,symbol,text) for symbol in sorted(symbols)]

def review_market_records(records):
    """A post-wide direction cannot contradict a reviewed security direction.

    Only reviewed posts are split; unrelated records retain their existing form.
    Non-security/ambiguous mentions stay visible with neutral direction.
    """
    out=[]
    for r in records:
        notes=post_reviews(r['source_id'],r['post_id'],r.get('raw_text',''))
        if not notes:
            out.append(r);continue
        for symbol in r['ticker']:
            review=adjudication(r['source_id'],r['post_id'],symbol,r.get('raw_text',''))
            e=dict(r,ticker=[symbol])
            if review:
                e.update(original_direction=r['direction'],direction=review['direction'] if review['decision']=='correct_direction' else 'neutral',semantic_review=review)
            out.append(e)
    return out
