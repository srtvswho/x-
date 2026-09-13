"""Bind the published UI to its source revision, inputs and content bytes."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_manifest(dist):
    from signalboard.semantic_review import VERSION
    paths = [*dist.rglob('index.html'), *dist.glob('assets/*.js'),
             *dist.glob('data/*.json.gz'), *dist.glob('reports/*.html')]
    doc = {
        'schema': 'signalboard-publication-v1',
        'source_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'semantic_review_version': VERSION,
        'review_sha256': digest(ROOT/'config/semantic_reviews.json'),
        'files': {str(p.relative_to(dist)):digest(p) for p in sorted(set(paths))},
    }
    (dist/'build-manifest.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    return doc

def validate_manifest(dist):
    doc = json.loads((dist/'build-manifest.json').read_text())
    assert doc['schema'] == 'signalboard-publication-v1'
    assert doc['review_sha256'] == digest(ROOT/'config/semantic_reviews.json')
    required = {'index.html','tracking/index.html','posts/index.html','assets/market-panels.js',
                'data/raw-intelligence.json.gz','data/tracking-panels.json.gz','data/focus-signals.json.gz'}
    assert required <= doc['files'].keys()
    for name, expected in doc['files'].items():
        path = (dist/name).resolve()
        assert path.is_relative_to(dist.resolve())
        assert digest(path) == expected, f'Publication content mismatch: {name}'
    return doc
