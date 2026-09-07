import json
import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/dashboard'))
from signalboard.call_attribution import validate, save, candidates
from signalboard.history_reuse import DDL, load_reviews
from common import query_call_performance_events, normalize_ticker, price_currency
from test_first_call_repair import database,post
from refresh_prices_international import parse_chart


def fixture():
    con=database();con.execute('ALTER TABLE extractions_intel ADD COLUMN raw_response TEXT')
    post(con,'comparison','2025-01-01',text='AMD and NVDA are peers. Just buy TSM.')
    con.execute("UPDATE extractions_intel SET ticker=?,raw_response='{}'",(json.dumps(['AMD','NVDA','TSM']),))
    return con


def payload():
    return {'decisions':[{'ticker':t,'direction':'long' if t=='TSM' else 'neutral',
        'quote':'Just buy TSM.' if t=='TSM' else '', 'reason':'Explicit choice' if t=='TSM' else 'Comparison'} for t in ['AMD','NVDA','TSM']]}


def test_unreviewed_multiple_tickers_never_inherit_global_direction():
    con=fixture()
    assert query_call_performance_events(con)==[]
    assert len(candidates(con))==1
    save(con,candidates(con)[0],payload())
    assert [e['ticker'] for e in query_call_performance_events(con)]==['TSM']
    assert candidates(con)==[]


def test_neutral_override_preserves_raw_extraction():
    con=fixture();p=candidates(con)[0]
    data=payload()
    for d in data['decisions']:d.update(direction='neutral',quote='')
    save(con,p,data)
    assert not query_call_performance_events(con)
    assert con.execute('select direction from extractions_intel').fetchone()[0]=='long'
    assert len(load_reviews(con))==1


def test_invented_quotes_or_missing_candidates_are_rejected():
    con=fixture();p=candidates(con)[0]
    data=payload();data['decisions'][2]['quote']='I am buying TSM now.'
    with pytest.raises(ValueError):validate(data,p)
    data=payload();data['decisions'].pop()
    with pytest.raises(ValueError):validate(data,p)


def test_changed_raw_text_cannot_receive_old_review():
    con=fixture();p=candidates(con)[0]
    con.execute("UPDATE raw_posts SET raw_text='Now neutral'")
    with pytest.raises(ValueError):save(con,p,payload())


def test_newer_extraction_invalidates_per_security_review():
    con=fixture();p=candidates(con)[0];save(con,p,payload())
    con.execute("UPDATE extractions_intel SET id=id+1")
    assert len(candidates(con))==1
    assert query_call_performance_events(con)==[]


def test_listing_identity_preserves_explicit_adr():
    assert normalize_ticker('MICRON')=='MU'
    assert normalize_ticker('CREDO')=='CRDO'
    assert normalize_ticker('SAMSUNG')=='005930.KS'
    assert normalize_ticker('SSNLF')=='SSNLF'
    assert normalize_ticker('NV','NVIDIA')=='NVDA'
    assert normalize_ticker('NV','Nova Minerals')=='NV'
    assert price_currency('005930.KS')=='KRW'
    assert price_currency('285A.T')=='JPY'


def test_foreign_chart_rejects_wrong_currency_and_uses_exchange_date():
    data={'chart':{'result':[{'meta':{'symbol':'285A.T','currency':'JPY','exchangeTimezoneName':'Asia/Tokyo'},
        'timestamp':[1735776000], 'indicators':{'quote':[{'close':[100]}]}}]}}
    assert parse_chart(data,'285A.T')==[('2025-01-02',100)]
    data['chart']['result'][0]['meta']['currency']='USD'
    with pytest.raises(ValueError):parse_chart(data,'285A.T')
