#!/usr/bin/env python3
"""Out-of-sample light validation for candidates found in expansion pass two."""
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "validate_memory_startup_candidates.py"
if not BASE_PATH.exists():
    BASE_PATH = Path(__file__).with_name("startup_light_validation.py")
spec = importlib.util.spec_from_file_location("memory_startup_validation_base", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

CANDIDATES = (
    "jp_money_95630", "hypertechinvest", "venu_7_",
    "feroceresearch", "akinatorassets", "d27357",
)
WINDOWS = (
    (date(2024, 6, 1), date(2025, 2, 28)),
    (date(2025, 11, 1), date(2026, 5, 14)),
)
DISCOVERY_EXCLUDED = (date(2025, 3, 1), date(2025, 10, 31))
MAX_PER_AUTHOR_WINDOW = 180


def render(result):
    lines = [
        "# 2025存储扩搜新增候选：发现窗口外轻测", "",
        "发现窗口2025-03-01至2025-10-31完全排除；同作者/标的/方向21日内合并为一个事件。", "",
        "| 排名 | 作者 | n | 命中率 | 中位收益 | 中位超额SOXX | 抓取帖数 | 是否触顶 |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for i, row in enumerate(result["ranking"], 1):
        lines.append(
            f"| {i} | @{row['handle']} | {row['n']} | {row['hit_rate']:.1%} | "
            f"{row['median_raw_return']:.1%} | {row['median_excess_soxx']:.1%} | "
            f"{row['raw_posts']} | {'是' if row['hit_cap'] else '否'} |")
    lines += ["", "本轮只做轻测；最差案例和信号语义经人工审计后才决定是否进入观察位。"]
    return "\n".join(lines) + "\n"


def configure():
    base.CANDIDATES = CANDIDATES
    base.WINDOWS = WINDOWS
    base.DISCOVERY_EXCLUDED = DISCOVERY_EXCLUDED
    base.MAX_PER_AUTHOR_WINDOW = MAX_PER_AUTHOR_WINDOW
    base.render = render


def main():
    configure()
    base.main()


if __name__ == "__main__":
    main()
