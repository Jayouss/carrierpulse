"""Licensed / CSV Imported Business Provider (Provider B).

Provides businesses with explicit licensing rights that permit bulk CSV export.
Supports bundled licensed dataset as well as user-uploaded CSV files.
"""

import asyncio
import csv
import io
from pathlib import Path
from typing import List, Optional
from app.providers.base import BaseBusinessProvider, BusinessRecord

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_LICENSED_CSV = BASE_DIR / "sample_data" / "fresno_businesses_licensed.csv"


class LicensedDatasetProvider(BaseBusinessProvider):
    """Provider B: Discovers businesses from an export-licensed dataset or imported CSV."""

    provider_id = "licensed_dataset"
    provider_name = "Export-Licensed Business Dataset"
    allows_csv_export = True
    attribution_text = "Licensed Business Dataset (Export-Eligible)"

    def __init__(self, custom_csv_content: Optional[str] = None):
        self.custom_csv_content = custom_csv_content

    async def discover(
        self,
        category_ids: List[str],
        max_results: int,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> List[BusinessRecord]:
        records: List[BusinessRecord] = []
        raw_rows: List[dict] = []

        if self.custom_csv_content:
            reader = csv.DictReader(io.StringIO(self.custom_csv_content))
            raw_rows = list(reader)
        elif DEFAULT_LICENSED_CSV.exists():
            with open(DEFAULT_LICENSED_CSV, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                raw_rows = list(reader)

        # Map header variations
        for idx, row in enumerate(raw_rows):
            if cancel_event and cancel_event.is_set():
                break

            name = (
                row.get("Business Name")
                or row.get("business_name")
                or row.get("Name")
                or row.get("name")
                or ""
            ).strip()
            if not name:
                continue

            address = (
                row.get("Address")
                or row.get("address")
                or row.get("Full Address")
                or ""
            ).strip()
            phone = (
                row.get("Phone Number")
                or row.get("Phone")
                or row.get("phone")
                or row.get("telephone")
                or ""
            ).strip()
            website = (
                row.get("Website")
                or row.get("website")
                or row.get("URL")
                or row.get("url")
                or ""
            ).strip()
            cat = (
                row.get("Category")
                or row.get("category")
                or row.get("Type")
                or "General"
            ).strip()

            cat_id = cat.lower().replace(" ", "_").replace("/", "_")

            # Match category filter if specified
            if category_ids:
                matches_cat = False
                for cid in category_ids:
                    if cid.lower() in cat_id or cat_id in cid.lower() or cid.lower() in cat.lower():
                        matches_cat = True
                        break
                if not matches_cat:
                    continue

            record = BusinessRecord(
                id=f"lic_{idx+1}",
                name=name,
                address=address,
                raw_phone=phone if phone else None,
                website=website if website else None,
                category=cat,
                category_id=cat_id,
                provider_source="licensed_dataset",
                place_id=None,
                allows_export=True,
            )
            records.append(record)

            if len(records) >= max_results:
                break

            await asyncio.sleep(0.01)

        return records[:max_results]
