from pathlib import Path


ROOT = Path(__file__).parent.parent


def test_backfill_registry_covers_all_production_kols_and_includes_today():
    source = (ROOT / "scripts" / "intel_backfill_90d.py").read_text(encoding="utf-8")
    assert "KOL_LIST = KOL_TEST" in source
    assert "until_date_override or (today + timedelta(days=1))" in source
    assert "end=today + timedelta(days=1)" in source
    assert 'client.run(run_id).get()' in source
    assert 'client.dataset(dataset_id).iterate_items()' in source
    assert 'getattr(run, "default_dataset_id", None)' in source
    assert "个账号回填失败" in source
    assert "current_pub >= last_tweet_published_at" in source
    assert "即使是幂等命中，也用本次数据修复状态水位" in source


def test_history_repair_is_manual_bounded_and_keeps_checkpoints():
    workflow = (ROOT / ".github/workflows/signalboard-history-rebuild.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "scripts/intel_history_backfill.py" in workflow
    assert 'AI_MAX_CALLS_PER_RUN: "500"' in workflow
    assert 'AI_MAX_COST_PER_RUN_USD: "2.00"' in workflow
    assert "Save extraction checkpoint" in workflow
    assert "refresh_prices_polygon.py" in workflow
    assert "build_dashboard.py" in workflow
    assert "--ticker-clues-only" not in workflow
    assert "--since" not in workflow
    assert "history_complete" in (ROOT / "scripts/intel_history_backfill.py").read_text()


def test_daily_and_rebuild_workflows_share_database_concurrency_lock():
    daily = (ROOT / ".github" / "workflows" / "signalboard-daily.yml").read_text()
    rebuild = (
        ROOT / ".github" / "workflows" / "signalboard-history-rebuild.yml"
    ).read_text()
    assert "group: signalboard-data-write" in daily
    assert "group: signalboard-data-write" in rebuild


def test_daily_workflow_checkpoints_ingest_before_bounded_price_refresh():
    daily = (ROOT / ".github" / "workflows" / "signalboard-daily.yml").read_text()
    checkpoint = daily.index("Save ingest checkpoint")
    price_refresh = daily.index("Refresh prices")
    assert checkpoint < price_refresh
    assert 'POLYGON_MAX_API_REQUESTS: "60"' in daily
    assert 'git add data/signalboard.db.gz' in daily


def test_health_check_creates_log_directory():
    source = (ROOT / "scripts" / "intel_daily_health.py").read_text(encoding="utf-8")
    assert "os.makedirs(LOG_DIR, exist_ok=True)" in source
