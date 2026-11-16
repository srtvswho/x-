"""Preserve originals; recognize an identical quoted post later seen on its author's timeline."""
import hashlib
import json
from datetime import datetime
from .twitterapi_ingest import IngestError


def reconcile_existing_source(conn, prior, post, verified_at):
    if prior['platform'] != 'twitter':
        raise IngestError('existing ID provider mismatch')
    if prior['source_id'].lower() == post.source_id.lower():
        return False
    if prior['source_id'].lower() != 'ctx_' + post.source_id.lower():
        raise IngestError('existing ID author mismatch')
    # A graph context alias is not a different author. Require independent exact
    # identity/content/time agreement before promoting ONLY the source label.
    try:
        original = json.loads(prior['raw_json'])
        author = original['author']['userName']
        same_time = (datetime.fromisoformat(prior['published_at'].replace('Z', '+00:00')) ==
                     datetime.fromisoformat(post.published_at.replace('Z', '+00:00')))
        matches = (str(original['id']) == post.post_id and
                   str(author).lower() == post.source_id[3:].lower() and
                   prior['raw_text'] == post.raw_text and same_time)
    except (ValueError, TypeError, KeyError):
        matches = False
    if not matches:
        raise IngestError('context identity/content requires review')
    conn.execute('''CREATE TABLE IF NOT EXISTS twitterapi_source_promotions (
        post_id TEXT PRIMARY KEY, previous_source_id TEXT NOT NULL,
        canonical_source_id TEXT NOT NULL, original_json_sha256 TEXT NOT NULL,
        verified_at TEXT NOT NULL)''')
    conn.execute('INSERT INTO twitterapi_source_promotions VALUES (?,?,?,?,?)',
                 (post.post_id, prior['source_id'], post.source_id,
                  hashlib.sha256(prior['raw_json'].encode()).hexdigest(), verified_at))
    conn.execute('UPDATE raw_posts SET source_id=? WHERE post_id=? AND source_id=?',
                 (post.source_id, post.post_id, prior['source_id']))
    return True
