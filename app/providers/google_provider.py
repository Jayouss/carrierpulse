"""Google Places Business Discovery Provider (Provider A)."""

import asyncio
from typing import List, Optional
from app.config import DEFAULT_CATEGORIES
from app.providers.base import BaseBusinessProvider, BusinessRecord
from app.services.google_places import GooglePlacesService


class GooglePlacesProvider(BaseBusinessProvider):
    """Live business discovery via Google Places API (New).

    Subject to Google Maps Platform ToS (display & discovery only, no bulk CSV lead export).
    """

    provider_id = "google_places"
    provider_name = "Google Places API (New)"
    allows_csv_export = False
    attribution_text = "Data provided by Google Places"

    def __init__(self, service: GooglePlacesService):
        self.service = service

    async def discover(
        self,
        category_ids: List[str],
        max_results: int,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> List[BusinessRecord]:
        all_records: List[BusinessRecord] = []
        if not category_ids:
            return all_records

        # Distribute target results across chosen categories
        per_cat_target = max(1, max_results // len(category_ids))

        category_map = {c["id"]: c for c in DEFAULT_CATEGORIES}

        for cat_id in category_ids:
            if cancel_event and cancel_event.is_set():
                break

            cat_info = category_map.get(cat_id)
            if not cat_info:
                # Custom category query
                query = f"{cat_id} in Fresno CA"
                label = cat_id.capitalize()
            else:
                query = cat_info["query"]
                label = cat_info["label"]

            needed = min(per_cat_target, max_results - len(all_records))
            if needed <= 0:
                break

            records = await self.service.search_category(
                query=query,
                category_label=label,
                category_id=cat_id,
                max_results=needed,
                cancel_event=cancel_event,
            )
            all_records.extend(records)

        return all_records[:max_results]
