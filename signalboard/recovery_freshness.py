"""Read-only publication metadata: new timeline coverage never closes old gaps."""
import html
from datetime import datetime, timezone, timedelta


def recovery_freshness(con):
    result = {'status':'not_recorded','timeline_windows':[],
              'historical_gap':{'from_shanghai':'2026-11-12T00:00:00+08:00','status':'not_verified_closed'},
              'ai_status':'independent_not_verified_by_fetch'}
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='twitterapi_timeline_coverage'").fetchone():
        return result
    rows=con.execute('SELECT handle,coverage_start,coverage_end,completion_reason,verified_at,in_window_count FROM twitterapi_timeline_coverage ORDER BY handle,coverage_start').fetchall()
    fields=('handle','coverage_start','coverage_end','completion_reason','verified_at','in_window_count')
    result['timeline_windows']=[dict(zip(fields,row)) for row in rows]
    result['status']='recorded_intervals_only' if rows else 'not_recorded'
    return result


def _display(value):
    try:
        instant=datetime.fromisoformat(value.replace('Z','+00:00'))
        if not instant.tzinfo:raise ValueError()
        return instant.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError,TypeError,AttributeError):
        return '时间未核实'


def recovery_banner(meta):
    if not meta or not meta.get('timeline_windows'):
        return ''
    rows=meta['timeline_windows']
    handles={r['handle'] for r in rows}
    items=''.join('<li>@'+html.escape(str(r['handle']))+'：'+_display(r['coverage_start'])+' 至 '+_display(r['coverage_end'])+'（'+str(int(r['in_window_count']))+' 条）</li>' for r in rows)
    return ('<aside id="recovery-freshness" role="status" style="margin:16px 0;padding:12px 16px;background:#fbf1db;border:1px solid #e7d6ac;border-radius:10px;font-size:12px">'
            '<strong>原帖新窗口已核验：'+str(len(handles))+' 个账户</strong>。仅代表下列时间段的提供方时间线覆盖，不代表完整 X 历史。'
            '<br>历史缺口：自 2026-11-12 起的旧缺口尚未验证补齐；新窗口不会抹平该缺口。'
            '<br>AI 解读：抓取成功不代表解读已更新，原有解读及其时间保持独立。'
            '<details><summary>查看逐账户覆盖范围（上海时间）</summary><ul>'+items+'</ul></details></aside>')
