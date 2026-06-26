"""P4-10c 抓 9 公开 post 全文 + 标记 14 付费为 partial"""
import os, json, re, time, subprocess


def fetch_html(url, retries=2):
    for _ in range(retries):
        try:
            out = subprocess.check_output(
                ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", url],
                stderr=subprocess.STDOUT, timeout=30,
            ).decode(errors="ignore")
            return out
        except Exception as e:
            print(f"  err {e}")
            time.sleep(2)
    return ""


def extract_body(html):
    """从 Substack post HTML 提取 body 文本。"""
    m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
    if m:
        body = m.group(1)
        # 去 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', body)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    return ""


with open("/workspace/logs/p4p10b_substack_all.json") as f:
    posts = json.load(f)

print(f"Total: {len(posts)} posts")
public = [p for p in posts if p.get("audience") == "everyone"]
paid = [p for p in posts if p.get("audience") == "only_paid"]
print(f"Public: {len(public)}, Paid: {len(paid)}")

# 抓所有公开 post 完整 body
print("\n=== 抓 9 公开 post 全文 ===")
for p in public:
    url = f"https://www.semiconsam.com/p/{p['slug']}"
    html = fetch_html(url)
    body = extract_body(html)
    p["full_body"] = body
    p["body_source"] = "fetched_html" if body else "truncated_only"
    print(f"  [{p['post_date'][:10]}] {p['title'][:60]} → {len(body)} chars")
    time.sleep(1)

# 付费 post 标记 partial
print("\n=== 标记 14 付费 post 为 partial ===")
for p in paid:
    p["full_body"] = p.get("truncated_body", "")
    p["body_source"] = "paywall_partial"
    print(f"  [{p['post_date'][:10]}] {p['title'][:60]} → {len(p['full_body'])} chars (paywall)")

# 保存
with open("/workspace/logs/p4p10c_substack_with_bodies.json", "w") as f:
    json.dump(posts, f, indent=2)
print(f"\n✅ saved /workspace/logs/p4p10c_substack_with_bodies.json")

# 字数统计
total_public_chars = sum(len(p.get("full_body", "")) for p in public)
total_paid_chars = sum(len(p.get("full_body", "")) for p in paid)
print(f"\n公开 post 总字数: {total_public_chars}")
print(f"付费 post truncated 总字数: {total_paid_chars}")