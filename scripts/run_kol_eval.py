"""run_kol_eval.py — CLI 入口

用法:
    python scripts/run_kol_eval.py --handle aleabitoreddit
    python scripts/run_kol_eval.py --handle aleabitoreddit --out /path/to/report.md
    python scripts/run_kol_eval.py --handle somekol --db /path/to/other.db

内部会自动跑 6 个模块,输出标准记分牌。
"""
import argparse
import sys
from pathlib import Path

# 路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from signalboard.quality.kol_eval import evaluate_kol


def main():
    parser = argparse.ArgumentParser(description="KOL 评估标准流程")
    parser.add_argument("--handle", required=True, help="KOL handle (e.g. aleabitoreddit)")
    parser.add_argument("--db", default="/workspace/data/signalboard_full.db", help="数据库路径")
    parser.add_argument("--out", default=None, help="输出 markdown 路径 (默认 outputs/quality_kol_<handle>.md)")
    args = parser.parse_args()

    if args.out is None:
        out = ROOT / "outputs" / f"quality_kol_{args.handle}.md"
    else:
        out = Path(args.out)

    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"[KOL Eval] handle={args.handle} db={args.db}")
    report = evaluate_kol(handle=args.handle, db_path=args.db, output_path=str(out))

    print(f"\n✅ 置信度等级: {report.confidence_grade}")
    print(f"   Tier 分布: A={report.tier_distribution.get('A',0)} / B={report.tier_distribution.get('B',0)} / C={report.tier_distribution.get('C',0)}")
    h_3m = report.tier_stats.get("A", {}).n_resolved.get("3m") if hasattr(report.tier_stats.get("A"), "n_resolved") else None
    if h_3m and h_3m.hit_rate is not None:
        print(f"   tier_A 3m hit_rate: {h_3m.hit_rate*100:.1f}% / median_excess: {h_3m.median_excess:+.2f}%")
    print(f"\n   报告写入: {out}")


if __name__ == "__main__":
    main()