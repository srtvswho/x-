"""CAS journal persistence on a pre-provisioned, non-production Git branch.

No checkout, reset, branch initialization, credential output or automatic retry.
The caller must save a reservation successfully BEFORE making its provider call.
If push completion is uncertain, stop and load/reconcile; never repeat the API call.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess

STATE_BRANCH = 'state/twitterapi-recovery'
SCHEMA = 'twitterapi-page-journal-v1'
MAX_BYTES = 32 * 1024 * 1024

class StateStoreError(RuntimeError):
    pass

class GitBranchStore:
    def __init__(self, repo_path, remote='origin', branch=STATE_BRANCH):
        if branch != STATE_BRANCH:
            raise StateStoreError('state branch must be dedicated and allowlisted')
        if not isinstance(remote,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',remote):
            raise StateStoreError('configured remote name required')
        self.repo=Path(repo_path).resolve()
        self.remote=remote
        self.branch=branch
        self.ref='refs/signalboard/twitterapi-state'

    def _git(self,*args,input=None,env=None):
        try:
            result=subprocess.run(['git',*args],cwd=self.repo,input=input,
                                  stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                  text=True,check=True,timeout=60,env=env)
        except (OSError,subprocess.SubprocessError):
            # No command/remote/stdout/stderr disclosure (could include credentials).
            raise StateStoreError('state Git operation failed or uncertain; reconcile before continuing') from None
        return result.stdout.strip()

    @staticmethod
    def _validate(state):
        if not isinstance(state,dict) or state.get('schema') != SCHEMA or not isinstance(state.get('config'),dict) or not state['config']:
            raise StateStoreError('pre-provisioned state schema and explicit config required')
        if type(state.get('reserved_credits')) is not int or state['reserved_credits'] < 0:
            raise StateStoreError('explicit nonnegative reserved credits required')
        # Reject serialization ambiguity and bound journal/cache growth.
        try:
            encoded=json.dumps(state,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n'
        except (TypeError,ValueError):
            raise StateStoreError('invalid JSON state') from None
        if len(encoded.encode()) > MAX_BYTES:
            raise StateStoreError('state size cap reached; stop before further requests')
        return encoded

    def _read(self,revision):
        raw=self._git('show',f'{revision}:state.json')
        if len(raw.encode()) > MAX_BYTES:
            raise StateStoreError('state size cap reached')
        try:
            state=json.loads(raw)
        except (ValueError,TypeError):
            raise StateStoreError('invalid remote state JSON') from None
        self._validate(state)
        return state

    def load(self):
        # Explicit refspec only; missing remote branch fails, never auto-creates.
        self._git('fetch','--depth=1','--no-tags',self.remote,f'+refs/heads/{self.branch}:{self.ref}')
        revision=self._git('rev-parse','--verify',self.ref)
        if not re.fullmatch(r'[0-9a-f]{40,64}',revision):
            raise StateStoreError('invalid state revision')
        return self._read(revision),revision

    def save(self,state,expected_revision):
        encoded=self._validate(state)
        if not isinstance(expected_revision,str) or not re.fullmatch(r'[0-9a-f]{40,64}',expected_revision):
            raise StateStoreError('explicit expected revision required')
        current,head=self.load()
        if head != expected_revision:
            raise StateStoreError('state CAS conflict; stop and reconcile')
        if current['config'] != state['config']:
            raise StateStoreError('config immutable; no implicit budget or expiry change')
        old_reads=current.get('balance_reads',[]);new_reads=state.get('balance_reads',[])
        if len(new_reads)<len(old_reads) or any(a!=b and not (i==len(old_reads)-1 and a=='pending' and b=='zero_recharge') for i,(a,b) in enumerate(zip(old_reads,new_reads))):
            raise StateStoreError('balance attempt rollback refused')
        if state['reserved_credits'] < current['reserved_credits']:
            raise StateStoreError('reserved credit rollback refused')
        if current == state:
            return head
        # Build a new tree from prior entries without touching index/worktree. All
        # unrelated root entries are preserved, and state.json must be a plain blob.
        entries=self._git('ls-tree',head).splitlines()
        old_entry=next((e for e in entries if e.split('\t',1)[-1]=='state.json'),None)
        if not old_entry or not old_entry.startswith('100644 blob '):
            raise StateStoreError('state.json must be a regular committed file')
        blob=self._git('hash-object','-w','--stdin',input=encoded)
        tree_input='\n'.join([e for e in entries if e != old_entry]+[f'100644 blob {blob}\tstate.json'])+'\n'
        tree=self._git('mktree',input=tree_input)
        commit=self._git('-c','user.name=signalboard-state-bot','-c','user.email=signalboard-state-bot@users.noreply.github.com',
                         'commit-tree',tree,'-p',head,'-m','[CF-Pages-Skip] Persist bounded TwitterAPI recovery journal [skip daily] [skip ui]')
        # A race after load is caught server-side. This is a fast-forward child of
        # head, with an exact lease; no force without expected revision is allowed.
        self._git('push',f'--force-with-lease=refs/heads/{self.branch}:{head}',self.remote,
                  f'{commit}:refs/heads/{self.branch}')
        # Confirm persisted remote SHA. Uncertain writes never trigger another push.
        remote_head=self._git('ls-remote',self.remote,f'refs/heads/{self.branch}').split()
        if not remote_head or remote_head[0] != commit:
            raise StateStoreError('state persistence unconfirmed; reconcile before provider call')
        return commit
