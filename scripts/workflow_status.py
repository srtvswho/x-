#!/usr/bin/env python3
"""Read-only cross-session status and production acceptance receipt."""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def live_investment(state):
    headers={'Accept':'application/json'}
    token=os.environ.get('IOS_SITE_TOKEN')
    if token:headers['OAI-Sites-Authorization']='Bearer '+token
    def get(path):
        with urllib.request.urlopen(urllib.request.Request(state['production_url']+path,headers=headers),timeout=45) as response:
            return json.load(response)
    auto=get('/api/leverage/refresh/automatic')
    if not auto.get('ok') or not auto.get('priceHealth',{}).get('ok') or not auto.get('refreshHealth',{}).get('ok'):
        return {'status':'pending','target':auto.get('target'),'next_step':auto.get('next_step'),
                'retry_after_seconds':auto.get('retry_after_seconds'),'checkpoints':auto.get('checkpoints')}
    audit=get('/api/system/audit')
    snapshot=get('/api/leverage/memory/snapshot')
    radar=get('/api/leverage/radar')['memorySnapshot']
    assert audit['summary']['failure_count']==0, 'System audit failed'
    assert snapshot['integrity']['status']=='passed' and snapshot['integrity']['report_eligible'], 'Snapshot not eligible'
    assert snapshot['freshness']['ok'], 'Snapshot freshness failed'
    assert snapshot['snapshot_id']==radar['snapshot_id'] and snapshot['content_hash']==radar['content_hash'], 'Radar/snapshot mismatch'
    return {'status':'verified','target':auto['target'],'next_step':None,
            'applicable':auto['refreshHealth']['applicable_count'],'current':auto['refreshHealth']['current_count'],
            'rank_checks':audit['summary']['rank_checks'],'failure_count':0,
            'snapshot_id':snapshot['snapshot_id'],'content_hash':snapshot['content_hash'],
            'verified_at_utc':datetime.now(timezone.utc).isoformat()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    state=json.loads((ROOT/'docs/WORKFLOW_STATE.json').read_text())
    report={'project':state['project'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'handoff':state,'live':{'status':'not_checked'}}
    if args.live:
        try:
            if state['project']=='investment-os':report['live']=live_investment(state)
            else:
                sys.path.insert(0,str(ROOT/'scripts/dashboard'))
                from verify_production import verify
                manifest=json.loads((ROOT/'dashboard_deploy_dist/build-manifest.json').read_text())
                report['live']=verify(state['production_url'],manifest)
        except Exception as error:
            report['live']={'status':'unverified','reason':str(error)}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if not args.live or report['live']['status']=='verified' else 1

if __name__=='__main__':raise SystemExit(main())
