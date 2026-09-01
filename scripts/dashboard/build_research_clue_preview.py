#!/usr/bin/env python3
"""Render the standalone Research Clue Desk v1.6 Preview."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "outputs" / "research_clue_desk_v16" / "research_clues.json"
DEFAULT_TEMPLATE = Path(__file__).with_name("research_clue_preview.template.html")
DEFAULT_OUTPUT = ROOT / "dashboard_deploy_dist" / "research-clues" / "index.html"


def render(data_path: Path, template_path: Path, output_path: Path) -> Path:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if data.get("openai_calls") != 0 or data.get("production_changed") is not False:
        raise RuntimeError("Preview must be zero-AI and production-isolated")
    if not 8 <= len(data.get("clues", [])) <= 15:
        raise RuntimeError("Preview requires 8–15 clues")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    template = template_path.read_text(encoding="utf-8")
    if template.count("__RESEARCH_CLUES__") != 1:
        raise RuntimeError("Template placeholder missing or duplicated")
    html = template.replace("__RESEARCH_CLUES__", payload)
    forbidden = ("TOP INVESTMENT OPPORTUNITIES", "FOCUSED ODDS REVIEW", "BUY_CANDIDATE", "Bear Fair Value")
    for marker in forbidden:
        if marker in html:
            raise RuntimeError(f"valuation-era homepage marker leaked into Clue Preview: {marker}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = render(args.data, args.template, args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
