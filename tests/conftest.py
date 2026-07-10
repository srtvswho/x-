#!/usr/bin/env python3
"""conftest.py — pytest 配置

- 把 tests/ 的父目录加进 sys.path, 让 'from scripts.dashboard import ...' 能找到
- 跟现有 fixture (tmp_path / monkeypatch / capsys) 兼容
"""
import sys
from pathlib import Path

# 把仓库根 (tests/ 的父目录) 加进 sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
