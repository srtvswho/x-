import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('history_cli',Path(__file__).resolve().parents[1]/'scripts/twitterapi_history_once.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class Tests(unittest.TestCase):
    def test_gate_every_boundary(self):
        head='a'*40
        env=dict(GITHUB_REPOSITORY='srtvswho/x-',GITHUB_EVENT_NAME='push',GITHUB_REF='refs/heads/master',GITHUB_RUN_ATTEMPT='1',HISTORY_RAW_ONLY_APPROVED='true',HISTORY_REVIEWED_HEAD=head,AI_ENABLED='false',ALLOW_EXPENSIVE_AI_JOB='false',AI_DRY_RUN='true',GITHUB_WORKFLOW_REF='srtvswho/x-/.github/workflows/twitterapi-history-recovery.yml@refs/heads/master')
        cli.gate(env,head)
        for key in env:
            bad=dict(env);bad[key]='wrong'
            with self.assertRaises(ValueError,msg=key):cli.gate(bad,head)
        with self.assertRaises(ValueError):cli.gate(env,'b'*40)
    def test_read_only_exact_checkpoint_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fixture.db';c=sqlite3.connect(p)
            c.execute('CREATE TABLE scrape_state(handle TEXT,last_fetched_at TEXT)')
            c.executemany('INSERT INTO scrape_state VALUES(?,?)',cli.BOUNDARIES.items());c.commit();c.close()
            before=p.read_bytes();self.assertEqual(cli.verify_database(p),cli.BOUNDARIES);self.assertEqual(p.read_bytes(),before)
            c=sqlite3.connect(p);c.execute("UPDATE scrape_state SET last_fetched_at='2026-11-12T08:00:00Z' WHERE handle='jukan05'");c.commit();c.close()
            with self.assertRaises(ValueError):cli.verify_database(p)
    def test_bad_state_before_client_creation(self):
        class Store:
            def load(self):return {'reserved_credits':3420},'revision'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fixture.db';c=sqlite3.connect(p);c.execute('CREATE TABLE scrape_state(handle,last_fetched_at)');c.executemany('INSERT INTO scrape_state VALUES(?,?)',cli.BOUNDARIES.items());c.commit();c.close()
            def never():raise AssertionError('client must not be constructed')
            with self.assertRaisesRegex(ValueError,'canonical_legacy_state_mismatch'):cli.run(Store(),never,p,now='2026-11-16T05:00:00Z')
if __name__=='__main__':unittest.main()
