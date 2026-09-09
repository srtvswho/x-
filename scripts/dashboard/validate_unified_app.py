"""Publication gates for navigation, chronology and the completed data snapshot."""
import gzip
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dashboard_deploy_dist'


def read(name):
    return json.loads(gzip.decompress((DIST/'data'/name).read_bytes()))


def main():
    home = (DIST/'index.html').read_text()
    expected = [('market','/'),('tracking','/tracking/'),('posts','/posts/'),('clues','/research-clues/'),('usage','/ai-usage/')]
    assert re.findall(r'data-nav="([^"]+)" href="([^"]+)"',home) == expected
    for path in DIST.glob('*/index.html'):
        assert path.read_text() == home, f'Different shell: {path}'
    assert '<iframe' not in home and home.count('<nav ') == 1
    raw, recent, lines = read('raw-intelligence.json.gz'), read('recent-posts.json.gz'), read('research-lines.json.gz')
    assert recent['total_posts'] == len(raw['posts'])
    assert recent['posts'][0]['date'] == max(p['date'] for p in raw['posts'])
    assert len(recent['posts']) <= 300
    assert lines['data_until'] == raw['generated_at']
    for line in lines['clues']:
        events = line['timeline']
        assert events and events == sorted(events,key=lambda e:e['date'])
        assert line['latest_post_at'] == events[-1]['date']
        assert line['assessment_at'] == line['last_updated']
        urls = [e['post_url'] for e in events if e.get('post_url')]
        assert len(urls) == len(set(urls)), line['clue_id']
        assert all(e['author'] and e['date'] for e in events)
    for name in ['market','tracking','usage']:
        data=read(name+'-panels.json.gz')
        assert data['BUILD_META']['data_until_utc'] == raw['generated_at']
    js=re.findall(r'<script>(.*?)</script>',home,re.S)[-1]
    subprocess.run(['node','--check'],input=js,text=True,check=True)
    subprocess.run(['node','--check',str(DIST/'assets/unified-navigation.js')],check=True)
    subprocess.run(['node','--input-type=module','--check'],input=(DIST/'assets/market-panels.js').read_text(),text=True,check=True)
    subprocess.run(['node',str(ROOT/'tests/test_unified_ui_runtime.cjs')],check=True,cwd=ROOT)
    print(f'PASS: one shell, five navigation items, {len(raw["posts"])} posts, {len(lines["clues"])} chronological research lines')


if __name__ == '__main__':
    main()
