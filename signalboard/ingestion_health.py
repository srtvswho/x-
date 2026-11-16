"""Read verified provider coverage without changing legacy scrape checkpoints."""
from datetime import datetime, timedelta, timezone


def instant(value):
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def recent_timeline_coverage(conn, now, max_age=timedelta(hours=36)):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='twitterapi_timeline_coverage' AND type='table'").fetchone():
        return {}
    expected = {'handle','coverage_start','coverage_end','provider','endpoint','completion_reason','verified_at','in_window_count'}
    if not expected <= {r[1] for r in conn.execute('PRAGMA table_info(twitterapi_timeline_coverage)')}:
        return {}
    result = {}
    for handle, start, end, verified, count in conn.execute('''SELECT handle,coverage_start,coverage_end,verified_at,in_window_count
          FROM twitterapi_timeline_coverage WHERE provider='twitterapi.io' AND endpoint='last_tweets'
          AND completion_reason IN ('start_boundary_crossed','timeline_exhausted')'''):
        start, end, verified = map(instant, (start,end,verified))
        if (not all((start,end,verified)) or not start < end <= verified <= now or
                now-end > max_age or type(count) is not int or count < 0):
            continue
        handle=handle.lower()
        if handle not in result or end > result[handle]['end']:
            result[handle]={'start':start,'end':end,'verified_at':verified,'count':count}
    return result
