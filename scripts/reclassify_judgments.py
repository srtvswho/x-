"""3 人 49 judgment 重新分类到 4 类 (①②③④) — 用 LLM 重新看原文 + 推文 context"""
import json, os, re, time, urllib.request, sys
from collections import Counter
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]

d = json.load(open("/workspace/logs/p5_industry_judgments/judgments_3kols.json"))

# 读 3 人 raw 推文, 按 source_id 找原文 context
def load_tweets(path):
    t = json.load(open(path))
    by_id = {}
    for x in t:
        if x.get("id"):
            by_id[x["id"]] = x
    return by_id

raw_fi = load_tweets("/workspace/logs/p5_industry_judgments/raw_fi56622380.json")
raw_zephyr = load_tweets("/workspace/logs/p5_zephyr/raw_all.json")
raw_austin = load_tweets("/workspace/logs/p5_newcandidates/raw_austinsemis.json")
RAW = {"fi56622380": raw_fi, "zephyr_z9": raw_zephyr, "austinsemis": raw_austin}

RECLASSIFY_PROMPT = """你是 X 推文产业判断重新分类器. 严格按 4 类, 不要混淆.

【4 类严格定义】

① **客观事实陈述 / 技术评价** — 不是判断, 不验
   - "美光技术比海力士差" — 客观技术比较, 可以同时看多美光
   - "HBM 容量最稀缺" — 客观描述
   - "AMD 发布了新 GPU" — 事实
   - "CUDA 护城河" — 技术评价
   - **不验, 直接标 ①**

② **倾向性看法但非建仓** — 是态度, 不是可验证多空押注
   - "不看好谷歌股票" — = 不 long, 不等于做空
   - "CEO 拉胯, 以后绕着走" — 负面态度, 但不是做空建仓
   - "我会避开" — 个人行为, 不押注
   - "我不认为 X 值得买" — 弱负面
   - "可以买但我不会" — 倾向
   - **不按 long/short 验, 标 ② (弱信号)**

③ **产业趋势预测 (有或无明确标的)** — 看能否明确对应到标的方向
   - "AI 电力缺口会爆发" — 趋势预测, 但没说买什么股
   - "HBM 紧缺持续" — 趋势, 但需要推导标的方向
   - "长视频生成让存储需求暴涨" — 趋势 + 暗含存储股受益
   - **如果能明确对应标的 + 方向 (long/short), 标 ③-验证**
   - **如果只能推导不能明确, 标 ③-模糊**

④ **明确的方向押注** — 这才是真·验证样本
   - "我看多 X" / "看空 X" / "做多/做空 X"
   - "X 会涨到 Y" / "X 会崩盘到 Y"
   - "X 必涨 / 必跌"
   - "买 X / 卖 X" / "buy X / sell X"
   - "X 严重低估 / X 严重高估" — 隐含 long/short, 且明确标的
   - "我已建仓 X" / "我已买入 X"
   - **长多 / 长空 / 短期 都可以, 只要明确方向 + 标的**

【特别注意】— 以下 3 类常见误抽
1. **技术比较 ≠ short**: "美光技术比海力士差" 是 ① (技术比较)
2. **不看好 ≠ short**: "不看好谷歌" 是 ② (态度, 不等于做空)
3. **CEO 评价 ≠ short**: "CEO 拉胯" 是 ② (主观评价)
4. **隐含 long**: "HBM 容量最稀缺" 是 ① (事实, 不能验, 推不出必然 long 哪个标的)
5. **产业趋势有标的**: "AI 电力缺口爆发 → 利好 VRT" 标 ③-验证
6. **产业趋势无标的**: "AI 电力缺口爆发" (没说股) 标 ③-模糊
7. **个人行为**: "我会绕着走" 标 ②

【输出严格 JSON】
{{"verdict": "①/②/③-验证/③-模糊/④",
  "category_reason": "1 句话说明为什么",
  "direction": "long/short/中性",  # 真实方向 (就算误抽)
  "subject": "实际是哪个标的"  # 真实标的
}}

【输入】
- handle: @{handle}
- judgment (LLM 之前抽出的 1 句话): {judgment}
- judgment_date: {date}
- 之前被分到的方向: {direction}
- 之前被分到的标的: {tickers}
- 原推文: {original_tweet}
"""


def reclassify(j, handle):
    sid = j.get("source_id")
    raw = RAW.get(handle, {}).get(sid, {})
    original_text = raw.get("text", "(no context)")

    prompt = RECLASSIFY_PROMPT.format(
        handle=handle,
        judgment=j.get("judgment", ""),
        date=j.get("date", ""),
        direction=j.get("direction", ""),
        tickers=j.get("implied_tickers", []),
        original_tweet=original_text[:1200],
    )

    data = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.05,
        "max_tokens": 400,
    }).encode()
    last_err = "?"
    for retry in range(3):
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode())
            cs = resp["choices"][0]["message"]["content"]
            if not cs:
                raise ValueError("empty")
            return json.loads(cs)
        except Exception as ex:
            last_err = str(ex)
            if retry < 2:
                time.sleep(2 * (retry + 1))
    return {"verdict": "?", "category_reason": f"err: {last_err}", "direction": j.get("direction"), "subject": j.get("implied_tickers", [])}


# 跑所有
ALL = []
for h, items in d.items():
    for j in items:
        j["handle"] = h
        ALL.append(j)

t0 = time.time()
results = []
done = 0
with ThreadPoolExecutor(max_workers=20) as pool:
    futures = {pool.submit(reclassify, j, h): (j, h) for h, items in d.items() for j in items}
    for fut in as_completed(futures):
        j, h = futures[fut]
        try:
            r = fut.result()
            j2 = dict(j)
            j2.update({
                "new_verdict": r.get("verdict", "?"),
                "category_reason": r.get("category_reason", ""),
                "real_direction": r.get("direction", j.get("direction")),
                "real_subject": r.get("subject", j.get("implied_tickers", [])),
            })
            results.append(j2)
        except Exception as e:
            sys.stderr.write(f"err: {e}\n")
        done += 1
        if done % 10 == 0:
            print(f"  [{time.time()-t0:.0f}s] {done}/{len(ALL)}", flush=True)
print(f"  [{time.time()-t0:.0f}s] done {len(results)}")

json.dump(results, open("/workspace/logs/p5_industry_judgments/reclassified_4categories.json", "w"), indent=2, ensure_ascii=False)

# 统计
print("\n=== 4 类分类统计 ===")
import collections
by_h = collections.defaultdict(list)
for r in results:
    by_h[r["handle"]].append(r)

for h, items in by_h.items():
    c = Counter(r["new_verdict"] for r in items)
    print(f"  @{h}: {dict(c)}")
    for v, n in c.most_common():
        print(f"    {v}: {n}")
