"""Tests for Scan Orchestration and Manager Pipeline."""

import asyncio
from app.services.scan_manager import ScanManager


def test_demo_scan_pipeline_execution():
    async def _run():
        sm = ScanManager()
        categories = ["restaurant", "dentist", "auto_repair", "plumber", "law_firm"]

        started = await sm.start_scan(
            category_ids=categories,
            max_businesses=20,
            max_lookups=10,
            provider_mode="demo",
        )
        assert started is True

        # Wait for the background task to complete
        if sm._scan_task:
            await sm._scan_task

        progress = sm.get_progress()
        assert progress["stage"] == "Completed"
        assert progress["businesses_discovered"] > 0
        assert progress["numbers_checked"] <= 10
        assert progress["numbers_checked"] > 0

        records = sm.get_records()
        assert len(records) > 0
        assert any(r["match_status"] == "Comcast Match" for r in records)

    asyncio.run(_run())


def test_scan_stop_cancellation():
    async def _run():
        sm = ScanManager()
        started = await sm.start_scan(
            category_ids=["restaurant"],
            max_businesses=50,
            max_lookups=25,
            provider_mode="demo",
        )
        assert started is True

        # Stop scan immediately
        sm.stop_scan()
        if sm._scan_task:
            await sm._scan_task

        progress = sm.get_progress()
        assert progress["stage"] in {"Stopped", "Completed"}
        assert progress["is_running"] is False

    asyncio.run(_run())
