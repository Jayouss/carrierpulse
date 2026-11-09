"""Google Places API (New) Integration Service.

Handles Text Search (New), field masking, location biasing, pagination,
deduplication, and geographic filtering for Fresno, CA.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.config import FRESNO_LAT, FRESNO_LNG, FRESNO_SEARCH_RADIUS_METERS
from app.providers.base import BusinessRecord

logger = logging.getLogger(__name__)

GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Mandatory field mask to only request the fields we use
PLACES_FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.nationalPhoneNumber,"
    "places.internationalPhoneNumber,"
    "places.websiteUri,"
    "places.primaryType,"
    "places.types,"
    "nextPageToken"
)

# Fresno ZIP Code pattern: 936xx, 937xx, 938xx
FRESNO_ZIP_REGEX = re.compile(r"\b93[678]\d{2}\b")


def is_in_fresno_area(address: str) -> bool:
    """Check if address is within Fresno, CA metro area."""
    if not address:
        return True  # If address omitted but returned with strict locationBias, permit
    addr_lower = address.lower()
    if "fresno" in addr_lower or "clovis" in addr_lower:
        return True
    if FRESNO_ZIP_REGEX.search(address):
        return True
    return False


class GooglePlacesService:
    """Client for Google Places API (New)."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: float = 12.0):
        self.api_key = api_key
        self.timeout = timeout_seconds

    async def test_connection(self) -> Dict[str, Any]:
        """Test API key by executing a lightweight single-result query."""
        if not self.api_key:
            return {
                "success": False,
                "status_code": 401,
                "message": "Missing Google Places API Key.",
            }

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName",
        }
        body = {
            "textQuery": "Fresno City Hall Fresno CA",
            "pageSize": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(GOOGLE_PLACES_TEXT_SEARCH_URL, headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places", [])
                    name = places[0].get("displayName", {}).get("text") if places else "Fresno City Hall"
                    return {
                        "success": True,
                        "status_code": 200,
                        "message": f"Google Places connection verified. Probe found: {name}",
                    }
                elif resp.status_code in {400, 403}:
                    try:
                        err = resp.json().get("error", {})
                        msg = err.get("message") or err.get("status") or resp.text
                    except Exception:
                        msg = resp.text
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "message": f"Google API authentication/billing error: {msg}",
                    }
                else:
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "message": f"Google API returned HTTP {resp.status_code}: {resp.text[:120]}",
                    }
        except Exception as e:
            logger.exception("Google test connection error")
            return {
                "success": False,
                "status_code": 500,
                "message": f"Google Places connection network error: {str(e)}",
            }

    async def search_category(
        self,
        query: str,
        category_label: str,
        category_id: str,
        max_results: int = 20,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> List[BusinessRecord]:
        """Query Google Places Text Search (New) for businesses matching category in Fresno, CA.

        Handles pagination and enforces geographic and deduplication constraints.
        """
        if not self.api_key:
            raise ValueError("Google Places API Key is not configured")

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": PLACES_FIELD_MASK,
        }

        records: List[BusinessRecord] = []
        page_token: Optional[str] = None
        seen_place_ids: set[str] = set()

        while len(records) < max_results:
            if cancel_event and cancel_event.is_set():
                logger.info("Search cancelled by user.")
                break

            remaining = max_results - len(records)
            page_size = min(20, max(1, remaining))

            body: Dict[str, Any] = {
                "textQuery": query,
                "pageSize": page_size,
                "locationBias": {
                    "circle": {
                        "center": {"latitude": FRESNO_LAT, "longitude": FRESNO_LNG},
                        "radius": float(FRESNO_SEARCH_RADIUS_METERS),
                    }
                },
            }
            if page_token:
                body["pageToken"] = page_token

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(GOOGLE_PLACES_TEXT_SEARCH_URL, headers=headers, json=body)

                    if resp.status_code != 200:
                        logger.error("Google Places HTTP %d: %s", resp.status_code, resp.text)
                        break

                    data = resp.json()
                    places = data.get("places", [])
                    if not places:
                        break

                    for place in places:
                        if cancel_event and cancel_event.is_set():
                            break

                        place_id = place.get("id")
                        if not place_id or place_id in seen_place_ids:
                            continue
                        seen_place_ids.add(place_id)

                        name = place.get("displayName", {}).get("text") or "Unknown Business"
                        address = place.get("formattedAddress", "")

                        # Filter strictly for Fresno / Clovis area
                        if not is_in_fresno_area(address):
                            continue

                        phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
                        website = place.get("websiteUri")

                        record = BusinessRecord(
                            id=f"gp_{place_id}",
                            name=name,
                            address=address,
                            raw_phone=phone,
                            website=website,
                            category=category_label,
                            category_id=category_id,
                            provider_source="google_places",
                            place_id=place_id,
                            allows_export=False,  # Restricted per Google Maps ToS
                        )
                        records.append(record)

                        if len(records) >= max_results:
                            break

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

                    # Short pause for token propagation
                    await asyncio.sleep(1.0)

            except Exception as e:
                logger.exception("Error querying Google Places for %s", query)
                break

        return records
