"""One shell for all product routes; reuse the tested market and return renderers.

No API/model calls. All data comes from the same completed dashboard export.
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pack(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0))


def market_module(legacy, target):
    css = re.search(r"<style>(.*?)</style>", legacy, re.S)[1].replace(":root", ":host")
    css += """
    :host{display:block;font:16px/1.6 var(--sans);color:var(--ink)}
    .shead{margin-top:24px}.shead .num{display:none}.shead h2{font-size:26px}
    .hint,.filter-note,.period-control label,.filters label,.ct,.cwin{font-size:14px}
    .consensus,.stance,.tcard,.cost-panel{box-shadow:none;border-radius:14px}
    .ttable{font-size:14px}.tcard{overflow-x:auto}.psum,.ctext{font-size:16px}
    select{font-size:14px}.signal-strip{font-size:14px}.shead{flex-wrap:wrap}
    """
    start = legacy.index('  <div class="shead section-anchor" id="ai-cost"')
    finish = legacy.index('  <!-- ===== 近期明细 ===== -->', start)
    sections = legacy[start:finish]
    sections = sections.replace('AI COST GUARDRAILS', 'AI 用量')
    sections = sections.replace('风险费用包含 Pending / Unknown · 管理员审计', '实际费用、调用次数与预算')
    sections = sections.replace('已存历史最早方向追踪 · 历史覆盖待核验 · 可查看更早原帖', '看谁在何时看多或看空、此后股价怎样变化。起点是已存历史中的最早明确方向。')
    sections = sections.replace('value="return_desc"', 'value="return_desc"').replace('<option value="latest">', '<option value="latest" selected>')
    blocks = re.split(r'(?=  <div class="shead section-anchor")', sections)
    views = {"usage": blocks[1], "market": blocks[2], "tracking": blocks[3]}
    script = re.findall(r'<script>(.*?)</script>', legacy, re.S)[-1]
    script = script[:script.index('const archiveDates=')]
    # Read data passed to the module, never inject/evaluate executable HTML.
    script = re.sub(r"JSON.parse\(document.getElementById\('([^']+)'\).textContent\)", r"data['\1']", script)
    script = script.replace("perfSort='return_desc'", "perfSort='latest'")
    script = script.replace('onclick="closeEvidence(this)"', 'data-close-evidence')
    setup = """
    document.addEventListener('click',e=>{if(e.target.closest('[data-close-evidence]'))closeEvidence(e.target);});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('details[open]').forEach(d=>d.open=false);});
    if(mode==='market'){
      const dates=Object.keys(SUM.daily_history||{}).sort().reverse();
      document.getElementById('daily-archive-date').innerHTML=dates.map(day=>`<option>${day}</option>`).join('');
      document.getElementById('daily-archive-date').onchange=renderDailyArchive;
      document.getElementById('stance-window').onchange=e=>{win=+e.target.value;renderStance();};
      renderDailyArchive();renderStance();
    }else if(mode==='tracking'){
      document.getElementById('perf-kol').innerHTML='<option value="all">全部人物</option>'+ORDER.map(k=>`<option value="${k}">${KOLS[k].name}</option>`).join('');
      document.getElementById('perf-kol').onchange=e=>{perfKol=e.target.value;renderTickers();};
      document.getElementById('perf-window').onchange=e=>{perfDays=+e.target.value;renderTickers();};
      document.getElementById('perf-sort').onchange=e=>{perfSort=e.target.value;renderTickers();};
      renderTickers();
    }else renderAiCostPanel();
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("export function mount(host,mode,data){\nconst document=host.attachShadow({mode:'open'});\n"
                      + "document.innerHTML=" + json.dumps('<style>'+css+'</style>', ensure_ascii=False)
                      + "+(" + json.dumps(views, ensure_ascii=False) + ")[mode];\n" + script + setup + "\n}\n")


# Specific subject matches, not broad 'memory'/'server' keyword fan-out.
# Matching posts are related observations, never automatically confirmed evidence.
MATCH = {
    'clue_ymtc_nand_wfe': [r'ymtc|长江存储'],
    'clue_abf_copos_cowop': [r'feynman|copos|cowop|abf|glass substrates'],
    'clue_datacenter_physical': [r'data.?cent(?:er|re)|ai infrastructure', r'cooling|chiller|transformer|power delivery|electric|water'],
    'clue_memory_architecture': [r'memory wall|hbf|3d dram|memory hierarch|tiered memory'],
    'clue_hbm_dram_crowdout': [r'hbm', r'dram|wafer', r'capacity|crowd|allocat|挤|产能|wafer intensity'],
    'clue_legacy_dram': [r'legacy dram|legacy memory|ddr2|ddr3|esmt'],
    'clue_cpo_cw_laser': [r'cpo|1\.6t|sivers|\bsive\b', r'laser|激光|cw|sivers|\bsive\b'],
    'clue_socamm_lpddr': [r'socamm|lpddr', r'socamm|data.?cent(?:er|re)|server'],
    'clue_cxl_interconnect': [r'\bcxl\b|memory interconnect|100 tb/s|6\.4tb/s'],
    'clue_gpu_server_price': [r'server|rack|nvl72', r'price|cost|涨价|售价|\$8 million'],
    'clue_traditional_packaging': [r'wire.?bonder|traditional packaging|打线|传统封装'],
    'clue_cxmt_hbm3e': [r'cxmt|长鑫', r'hbm'],
    'clue_samsung_hbm4_broadcom': [r'samsung|三星', r'hbm4', r'broadcom|asic|博通'],
}


def research_lines(report, raw):
    out = json.loads(json.dumps(report))
    by_id = {p['id']: p for p in raw['posts']}
    for c in out['clues']:
        patterns = MATCH.get(c['clue_id'], [])
        seen, events = set(), []
        for event in c.get('timeline', []):
            event = dict(event)
            ids = re.findall(r'/status/(\d+)', event.get('post_url', ''))
            pid = ids[0] if ids else ''
            if pid in seen:
                continue
            if pid:
                seen.add(pid)
            p = by_id.get(pid)
            event['kind'] = 'reviewed'
            if p:
                event.update(date=p['date'], author=p['author_name'], author_key=p['author'], post=p['text'])
            events.append(event)
        for p in raw['posts']:
            if p['id'] in seen or p.get('repost') or p['author'] not in raw.get('tracking', {}).get('people', {}):
                continue
            text = ' '.join([p.get('text', ''), (p.get('quote') or {}).get('text', '')])
            if not patterns or not all(re.search(pattern, text, re.I) for pattern in patterns):
                continue
            seen.add(p['id'])
            events.append(dict(date=p['date'], author=p['author_name'], author_key=p['author'],
                post=p['text'], post_url=p['url'], kind='related', event_type='RELATED_POST',
                what_changed=p.get('summary') or '新增相关推文，尚未解读',
                ai_interpretation=p.get('summary') or '', claims=p.get('claims', []), media=[], quoted_posts=[]))
        events.sort(key=lambda e:e['date'])
        c['timeline'] = events
        c['assessment_at'] = c.get('last_updated')
        c['observed_start'] = events[0]['date'] if events else c.get('first_seen')
        c['latest_post_at'] = events[-1]['date'] if events else c.get('last_updated')
        c['unreviewed_count'] = sum(e['kind']=='related' and e['date'][:10] > (c.get('assessment_at') or '')[:10] for e in events)
    out['data_until'] = raw.get('generated_at')
    return out


def build(deploy_root: Path, report_path: Path):
    legacy = (HERE / 'dashboard.html').read_text()
    fields = {k:json.loads(v) for k,v in re.findall(r'<script id="([^\"]+)"[^>]*>(.*?)</script>', legacy, re.S)}
    data_dir = deploy_root / 'data'
    # Only the data needed by each view is transferred. Historical evidence stays
    # in the corpus; stance filters only support the most recent twelve months.
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.fromisoformat(fields['BUILD_META']['build_time_utc']) - timedelta(days=370)).isoformat()
    market = dict(fields, CALL_PERFORMANCE=[], TICKERS=[], THESIS_CHANGES=[])
    market['DATA'] = [r for r in fields['DATA'] if r.get('published_at','') >= cutoff]
    pack(data_dir/'market-panels.json.gz', market)
    pack(data_dir/'tracking-panels.json.gz', dict(fields, DATA=[], TODAY_RECORDS=[], SUMMARIES={}, THESIS_CHANGES=[]))
    pack(data_dir/'usage-panels.json.gz', {k:(v if k in ('AI_COST_PANEL','KOLS','BUILD_META') else [] if isinstance(v,list) else {}) for k,v in fields.items()})
    market_module(legacy, deploy_root/'assets'/'market-panels.js')
    raw = json.loads(gzip.decompress((data_dir/'raw-intelligence.json.gz').read_bytes()))
    # Small first page; complete historical corpus remains available for filtering.
    recent = {k:v for k,v in raw.items() if k not in ('posts', 'tracking', 'research_changes')}
    recent.update(posts=sorted(raw['posts'], key=lambda p:p['date'], reverse=True)[:300], total_posts=len(raw['posts']), partial=True)
    pack(data_dir/'recent-posts.json.gz', recent)
    report = research_lines(json.loads(report_path.read_text()), raw)
    pack(data_dir/'research-lines.json.gz', report)
    meta = {"build":fields['BUILD_META'], "data_until":raw['generated_at']}
    template = (HERE/'research_clue_preview.template.html').read_text()
    html = template.replace('__RESEARCH_CLUES__', json.dumps({"clues":[], **meta}, ensure_ascii=False).replace('</','<\\/'))
    return html
