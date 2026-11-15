"""Offline local-bare-repository tests; never contacts real remote or provider."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from signalboard.twitterapi_state_store import GitBranchStore, StateStoreError, SCHEMA

class StoreTests(unittest.TestCase):
    def git(self,*args,cwd=None):
        return subprocess.check_output(['git',*args],cwd=cwd or self.repo,stderr=subprocess.DEVNULL,text=True).strip()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.remote=root/'remote.git';self.repo=root/'work';self.repo.mkdir()
        self.git('init','--bare',str(self.remote));self.git('init')
        self.git('config','user.name','test');self.git('config','user.email','test@example.invalid')
        self.initial={'schema':SCHEMA,'config':{'grant_id':'approved','credit_limit':600,'expires_at':'2026-11-16T00:00:00Z'},'reserved_credits':0,'windows':{}}
        (self.repo/'state.json').write_text(json.dumps(self.initial));(self.repo/'unrelated.txt').write_text('preserved')
        self.git('add','.');self.git('commit','-m','fixture');self.git('remote','add','origin',str(self.remote))
        self.git('push','origin','HEAD:refs/heads/state/twitterapi-recovery')
        self.original_head=self.git('rev-parse','HEAD');self.original_status=self.git('status','--porcelain')
        self.store=GitBranchStore(self.repo)
    def tearDown(self):self.temp.cleanup()
    def test_load_and_save_preserve_worktree(self):
        state,rev=self.store.load();self.assertEqual(state,self.initial)
        state['reserved_credits']=300;new=self.store.save(state,rev)
        reread,new2=self.store.load();self.assertEqual(new,new2);self.assertEqual(reread['reserved_credits'],300)
        self.assertEqual(self.git('rev-parse','HEAD'),self.original_head)
        self.assertEqual(self.git('status','--porcelain'),self.original_status)
        self.assertEqual(self.git('show',new+':unrelated.txt'),'preserved')
        self.assertEqual(json.loads((self.repo/'state.json').read_text()),self.initial)
    def test_reserved_credit_rollback_refused(self):
        state,rev=self.store.load();state['reserved_credits']=300;rev=self.store.save(state,rev)
        state['reserved_credits']=0
        with self.assertRaises(StateStoreError):self.store.save(state,rev)
    def test_stale_cas(self):
        state,rev=self.store.load();state['reserved_credits']=300;self.store.save(state,rev)
        with self.assertRaises(StateStoreError):self.store.save(self.initial,rev)
    def test_config_cannot_be_raised_or_extended(self):
        for key,val in [('credit_limit',900),('expires_at','2026-12-16T00:00:00Z')]:
            state,rev=self.store.load();state['config'][key]=val
            with self.assertRaises(StateStoreError):self.store.save(state,rev)
    def test_branch_guard(self):
        for branch in ['master','main','recovery/twitterapi-free','state/other']:
            with self.assertRaises(StateStoreError):GitBranchStore(self.repo,branch=branch)
    def test_no_missing_branch_creation(self):
        self.git('push','origin',':refs/heads/state/twitterapi-recovery')
        with self.assertRaises(StateStoreError):self.store.load()
        self.assertEqual(self.git('ls-remote','origin','refs/heads/state/twitterapi-recovery'),'')
    def test_invalid_state_no_push(self):
        state,rev=self.store.load();state['schema']='wrong'
        with self.assertRaises(StateStoreError):self.store.save(state,rev)
        self.assertEqual(self.store.load()[1],rev)
    def test_missing_config_fails(self):
        state,rev=self.store.load();state.pop('config')
        with self.assertRaises(StateStoreError):self.store.save(state,rev)
    def test_same_state_no_extra_commit(self):
        state,rev=self.store.load();self.assertEqual(self.store.save(state,rev),rev)
    def test_no_url_or_command_remote(self):
        for remote in ['https://secret@example.com/repo','--upload-pack=bad','a/b']:
            with self.assertRaises(StateStoreError):GitBranchStore(self.repo,remote=remote)
    def test_race_between_load_and_push(self):
        state,rev=self.store.load();other=copy.deepcopy(state);other['reserved_credits']=300
        original=self.store._git; triggered=False
        def race(*args,**kw):
            nonlocal triggered
            if args[0]=='push' and not triggered:
                triggered=True
                GitBranchStore(self.repo).save(other,rev)
            return original(*args,**kw)
        self.store._git=race;state['reserved_credits']=600
        with self.assertRaises(StateStoreError):self.store.save(state,rev)
        self.assertEqual(GitBranchStore(self.repo).load()[0]['reserved_credits'],300)
if __name__=='__main__':unittest.main()
