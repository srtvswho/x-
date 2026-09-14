import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import author_mvp_20260913 as m
import resume_author_mvp_20260914 as resume


class ResumeTests(unittest.TestCase):
    def post(self):
        return m.normalize({'id':'2044423226051457174','text':'$MU buy memory',
                            'createdAt':'2026-01-01','author':{'userName':'bboczeng'}},'bboczeng')

    def payload(self,content):
        return {'choices':[{'message':{'content':content}}]}

    def test_exact_missing_id_quote_repaired_without_api(self):
        text='{"posts":[{"id":2044423226051457174","kind":"other","reason":"test","signals":[]}]}'
        with tempfile.TemporaryDirectory() as directory,patch.object(m,'OUT',Path(directory)),patch.object(m,'request') as request:
            result=m.decode_labels(self.payload(text),[self.post()],'test')
            self.assertEqual(result[0]['id'],'2044423226051457174')
            self.assertTrue((Path(directory)/'format_repairs/test.json').exists())
            request.assert_not_called()

    def test_numeric_id_keeps_exact_integer_precision(self):
        text='{"posts":[{"id":2044423226051457174,"kind":"other","signals":[]}]}'
        result=m.decode_labels(self.payload(text),[self.post()],'test')
        self.assertEqual(result[0]['id'],'2044423226051457174')

    def test_unrelated_corruption_not_repaired(self):
        text='{"posts":[{"id":"2044423226051457174","kind":"other","reason":"bad "quote"","signals":[]}]}'
        with self.assertRaises(m.OutputError):m.decode_labels(self.payload(text),[self.post()],'test')

    def test_unexpected_id_not_invented(self):
        text='{"posts":[{"id":2044423226051457175,"kind":"other","signals":[]}]}'
        with self.assertRaises(m.OutputError):m.decode_labels(self.payload(text),[self.post()],'test')

    def test_original_reservations_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'ledger.json'
            ledger=m.Ledger(path)
            ledger.reserve('old-scrape','apify','1.236')
            ledger.reserve('old-ai','ai','.258501')
            restarted=m.Ledger(path)
            restarted.reserve('new-ai','ai','.1')
            self.assertEqual(sum(r['reserved_micro_usd'] for r in restarted.rows),1594501)
            with self.assertRaises(m.Stop):restarted.reserve('too-large','ai','3.1')

    def test_tampered_restore_rejected(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(m,'OUT',Path(directory)):
            (Path(directory)/'ledger.json').write_text('[]')
            with self.assertRaises(m.Stop):resume.verify_restored()

    def test_resume_has_no_scraper_or_budget_reset(self):
        code=(ROOT/'scripts/resume_author_mvp_20260914.py').read_text()
        self.assertNotIn('m.scrape(',code)
        self.assertNotIn('ledger.rows = []',code)
        workflow=(ROOT/'.github/workflows/author-mvp-resume-20260914.yml').read_text()
        self.assertNotIn('APIFY_TOKEN',workflow)
        self.assertNotIn('HEAD:master',workflow)
        self.assertIn('Refuse duplicate continuation',workflow)


if __name__=='__main__':unittest.main()
