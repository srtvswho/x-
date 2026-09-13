#!/usr/bin/env python3
"""Read-only deployment receipt. A successful git push is not a live check."""
import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

def verify(base, expected):
    suffix = '?revision='+expected['source_commit']
    def fetch(path):
        req=urllib.request.Request(base.rstrip('/')+'/'+path+suffix,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity','User-Agent':'SignalBoard-Publication-Check/1'})
        with urllib.request.urlopen(req,timeout=30) as response:
            return response.read()
    actual=json.loads(fetch('build-manifest.json'))
    if actual != expected:
        raise RuntimeError('Production manifest is still a different publication')
    checked=['index.html','assets/market-panels.js','assets/unified-navigation.js',
             'data/tracking-panels.json.gz','data/market-panels.json.gz',
             'data/raw-intelligence.json.gz','data/focus-signals.json.gz']
    for name in checked:
        if hashlib.sha256(fetch(name)).hexdigest() != expected['files'][name]:
            raise RuntimeError('Production content mismatch: '+name)
    return {'status':'verified','source_commit':expected['source_commit'],
            'url':base,'checked_files':checked,'verified_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='https://signalboard-602.pages.dev')
    parser.add_argument('--manifest',type=Path,default=Path('dashboard_deploy_dist/build-manifest.json'))
    parser.add_argument('--wait-seconds',type=int,default=0)
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    expected=json.loads(args.manifest.read_text())
    deadline=time.monotonic()+args.wait_seconds
    while True:
        try:
            result=verify(args.url,expected)
            if args.receipt:
                args.receipt.parent.mkdir(parents=True,exist_ok=True)
                args.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(result,ensure_ascii=False));return
        except Exception as error:
            if time.monotonic() >= deadline:
                raise SystemExit('Production verification failed: '+str(error))
            print('Waiting for production: '+str(error),flush=True)
            time.sleep(min(20,max(0,deadline-time.monotonic())))

if __name__=='__main__':
    main()
