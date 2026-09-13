import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/dashboard'))
from verify_production import verify

FILES=['index.html','assets/market-panels.js','assets/unified-navigation.js',
       'data/tracking-panels.json.gz','data/market-panels.json.gz',
       'data/raw-intelligence.json.gz','data/focus-signals.json.gz']

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.expected={'source_commit':'a'*40,'files':{p:hashlib.sha256(p.encode()).hexdigest() for p in FILES}}
        self.content={p:p.encode() for p in FILES}
        self.content['build-manifest.json']=json.dumps(self.expected).encode()

    def fetch(self,request,timeout):
        path=request.full_url.split('https://example.test/')[1].split('?')[0]
        return BytesIO(self.content[path])

    def test_matching_publication_produces_receipt(self):
        with patch('urllib.request.urlopen',self.fetch):
            receipt=verify('https://example.test',self.expected)
        self.assertEqual(receipt['status'],'verified')
        self.assertEqual(receipt['checked_files'],FILES)

    def test_source_revision_alone_does_not_prove_data_published(self):
        self.content['data/tracking-panels.json.gz']=b'old tracking snapshot'
        with patch('urllib.request.urlopen',self.fetch),self.assertRaisesRegex(RuntimeError,'content mismatch'):
            verify('https://example.test',self.expected)

    def test_stale_manifest_fails(self):
        self.content['build-manifest.json']=b'{}'
        with patch('urllib.request.urlopen',self.fetch),self.assertRaisesRegex(RuntimeError,'different publication'):
            verify('https://example.test',self.expected)

if __name__=='__main__':unittest.main()
