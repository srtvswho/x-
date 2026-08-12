from pathlib import Path


ROOT = Path(__file__).parent.parent


def test_backfill_registry_covers_all_production_kols_and_includes_today():
    source = (ROOT / "scripts" / "intel_backfill_90d.py").read_text(encoding="utf-8")
    assert "KOL_LIST = KOL_TEST" in source
    assert "until_date = today + timedelta(days=1)" in source
    assert "end=today + timedelta(days=1)" in source
    assert 'client.run(run_id).get()' in source
    assert 'client.dataset(dataset_id).iterate_items()' in source


def test_one_year_rebuild_is_bounded_and_recomputes_all_derived_views():
    workflow = (
        ROOT / ".github" / "workflows" / "signalboard-history-rebuild.yml"
    ).read_text(encoding="utf-8")
    for handle in ("DGretta_Author", "FeroceResearch", "TradexWhisperer", "gsmferrari"):
        assert handle in workflow
    assert "--since-days 370" in workflow
    assert "--since-days 30" in workflow
    assert "--max-targets 6000" in workflow
    assert "--ticker-clues-only" in workflow
    assert "Save raw backfill checkpoint" in workflow
    for run_id in (
        "eHzAhTk5bZiBrDzDD",
        "PeeVsMuLX75q2gUph",
        "KLHVvrYw16h9c7iUV",
        "aIleM6JgGwMNmKhc8",
    ):
        assert run_id in workflow
    assert "refresh_prices_polygon.py" in workflow
    assert "intel_gen_summaries.py" in workflow
    assert "build_dashboard.py" in workflow
    assert "signalboard_history_rebuild_latest.json" in workflow


def test_daily_and_rebuild_workflows_share_database_concurrency_lock():
    daily = (ROOT / ".github" / "workflows" / "signalboard-daily.yml").read_text()
    rebuild = (
        ROOT / ".github" / "workflows" / "signalboard-history-rebuild.yml"
    ).read_text()
    assert "group: signalboard-data-write" in daily
    assert "group: signalboard-data-write" in rebuild
