"""P4-10b 抓所有 Substack posts + X 长段时间"""
import os, json, time, subprocess

def fetch_substack_posts():
    """拉 SemiconSam Substack 全部 posts (用 /archive 端点)。"""
    url = "https://www.semiconsam.com/api/v1/archive"
    out = subprocess.check_output(
        ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", url],
        stderr=subprocess.STDOUT, timeout=30,
    ).decode(errors="ignore")
    posts = json.loads(out)
    return posts


print("=== 抓 SemiconSam Substack 全部 posts ===")
posts = fetch_substack_posts()
print(f"\nTotal: {len(posts)} posts")

# 简化保存: title + post_date + truncated_body_text + slug + tags + audience
simplified = []
for p in posts:
    simplified.append({
        "id": p.get("id"),
        "title": p.get("title"),
        "slug": p.get("slug"),
        "post_date": p.get("post_date"),
        "wordcount": p.get("wordcount"),
        "audience": p.get("audience"),
        "write_comment_permissions": p.get("write_comment_permissions"),
        "truncated_body": p.get("truncated_body_text", ""),
        "tags": [t.get("name") for t in p.get("postTags", [])],
        "url": f"https://www.semiconsam.com/p/{p.get('slug')}",
    })

# 按时间排序
simplified.sort(key=lambda x: x.get("post_date", ""))

# 统计
from collections import Counter
years = Counter(p["post_date"][:7] if p.get("post_date") else "?" for p in simplified)
print("\n按月分布:")
for m, n in sorted(years.items()):
    print(f"  {m}: {n} 篇")

# 公开 vs 付费
audiences = Counter(p.get("audience") for p in simplified)
print(f"\n可见性: {dict(audiences)}")

# 保存
with open("/workspace/logs/p4p10b_substack_all.json", "w") as f:
    json.dump(simplified, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p10b_substack_all.json")
print(f"最早: {simplified[0].get('post_date')} - {simplified[0].get('title')[:80]}")
print(f"最晚: {simplified[-1].get('post_date')} - {simplified[-1].get('title')[:80]}")