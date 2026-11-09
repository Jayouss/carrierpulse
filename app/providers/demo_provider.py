"""Demo Business Data Provider (FR-11).

Provides realistic synthetic Fresno businesses without requiring live API keys.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.providers.base import BaseBusinessProvider, BusinessRecord

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEMO_DATA_FILE = BASE_DIR / "sample_data" / "demo_records.json"


class DemoBusinessProvider(BaseBusinessProvider):
    """Zero-configuration demo provider with synthetic Fresno records."""

    provider_id = "demo"
    provider_name = "Demo Mode (Synthetic Fresno Records)"
    allows_csv_export = True
    attribution_text = "Demo Mode — Synthetic sample dataset for testing"

    def __init__(self):
        self._raw_records: List[Dict[str, Any]] = []
        self._load_demo_data()

    def _load_demo_data(self):
        if DEMO_DATA_FILE.exists():
            try:
                with open(DEMO_DATA_FILE, "r", encoding="utf-8") as f:
                    self._raw_records = json.load(f)
            except Exception:
                self._raw_records = []

    def get_simulated_carrier_info(self, e164_or_raw: str) -> Optional[Dict[str, Any]]:
        """Retrieve simulated carrier data for a demo phone number."""
        for item in self._raw_records:
            if item.get("raw_phone") == e164_or_raw or item.get("id") == e164_or_raw:
                return {
                    "carrier_name": item.get("simulated_carrier"),
                    "line_type": item.get("simulated_line_type") or "unknown",
                }
        return None

    async def discover(
        self,
        category_ids: List[str],
        max_results: int,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> List[BusinessRecord]:
        records: List[BusinessRecord] = []
        target_cats = set(category_ids) if category_ids else None

        for item in self._raw_records:
            if cancel_event and cancel_event.is_set():
                break

            cat_id = item.get("category_id", "")
            if target_cats and cat_id not in target_cats:
                continue

            rec = BusinessRecord(
                id=item["id"],
                name=item["name"],
                address=item.get("address", ""),
                raw_phone=item.get("raw_phone"),
                website=item.get("website"),
                category=item.get("category", "General"),
                category_id=cat_id,
                provider_source="demo",
                place_id=None,
                allows_export=True,
            )
            records.append(rec)
            if len(records) >= max_results:
                break

            # Short micro-delay to simulate discovery rhythm
            await asyncio.sleep(0.02)

        return records[:max_results]
