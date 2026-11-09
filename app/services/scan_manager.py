"""Commercial Scan Orchestrator and Telecommunications Pipeline Service.

Manages background scans, enforces concurrency and spend limits,
updates real-time metrics, coordinates phone normalization & carrier matching,
and broadcasts events for live dashboard monitoring.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from app.config import (
    AppSettings,
    EST_GOOGLE_PLACES_SEARCH_COST,
    EST_TWILIO_LOOKUP_COST,
)
from app.providers.base import BaseBusinessProvider, BusinessRecord
from app.providers.demo_provider import DemoBusinessProvider
from app.providers.google_provider import GooglePlacesProvider
from app.providers.licensed_provider import LicensedDatasetProvider
from app.services.carrier_matcher import (
    STATUS_COMCAST_MATCH,
    STATUS_NOT_MATCH,
    STATUS_POSSIBLE_MATCH,
    STATUS_UNKNOWN,
    classify_carrier,
)
from app.services.google_places import GooglePlacesService
from app.services.phone_utils import normalize_phone_number
from app.services.twilio_lookup import TwilioLookupService

logger = logging.getLogger(__name__)


class ScanMetrics:
    """Real-time metrics for an active scan."""

    def __init__(self):
        self.stage: str = "Preparing"
        self.businesses_discovered: int = 0
        self.valid_phones: int = 0
        self.numbers_checked: int = 0
        self.comcast_matches: int = 0
        self.possible_matches: int = 0
        self.not_matches: int = 0
        self.unknowns: int = 0
        self.failed_lookups: int = 0
        self.skipped_numbers: int = 0
        self.estimated_cost_dollars: float = 0.0
        self.provider_id: str = "demo"
        self.attribution_text: str = ""
        self.allows_export: bool = False
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.is_running: bool = False
        self.is_stopped: bool = False
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "businesses_discovered": self.businesses_discovered,
            "valid_phones": self.valid_phones,
            "numbers_checked": self.numbers_checked,
            "comcast_matches": self.comcast_matches,
            "possible_matches": self.possible_matches,
            "not_matches": self.not_matches,
            "unknowns": self.unknowns,
            "failed_lookups": self.failed_lookups,
            "skipped_numbers": self.skipped_numbers,
            "estimated_cost_dollars": round(self.estimated_cost_dollars, 4),
            "provider_id": self.provider_id,
            "attribution_text": self.attribution_text,
            "allows_export": self.allows_export,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "is_running": self.is_running,
            "is_stopped": self.is_stopped,
            "error_message": self.error_message,
        }


class ScanManager:
    """Coordinates and executes background scans."""

    def __init__(self):
        self.current_metrics = ScanMetrics()
        self.records: List[Dict[str, Any]] = []
        self._cancel_event: Optional[asyncio.Event] = None
        self._scan_task: Optional[asyncio.Task] = None
        self._subscribers: Set[asyncio.Queue] = set()

    def get_progress(self) -> Dict[str, Any]:
        """Return snapshot of current metrics and record count."""
        data = self.current_metrics.to_dict()
        data["total_records"] = len(self.records)
        return data

    def get_records(self) -> List[Dict[str, Any]]:
        return self.records

    def subscribe(self) -> asyncio.Queue:
        """Subscribe a queue for Server-Sent Events (SSE)."""
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def _broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected SSE clients."""
        payload = {"type": event_type, "data": data}
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except Exception:
                pass

    def stop_scan(self):
        """Signal the running scan to stop safely without discarding collected records."""
        if self._cancel_event:
            self._cancel_event.set()
        self.current_metrics.stage = "Stopped"
        self.current_metrics.is_stopped = True
        self.current_metrics.is_running = False
        self.current_metrics.completed_at = datetime.now().isoformat()
        asyncio.create_task(self._broadcast("scan_stopped", self.get_progress()))

    async def start_scan(
        self,
        category_ids: List[str],
        max_businesses: int = 50,
        max_lookups: int = 25,
        provider_mode: str = "demo",  # "google_places", "licensed_dataset", "demo"
        custom_csv_content: Optional[str] = None,
        max_spend_guard_dollars: float = 5.00,
    ) -> bool:
        """Start a new background scan job."""
        if self.current_metrics.is_running:
            return False

        self.records = []
        self.current_metrics = ScanMetrics()
        self.current_metrics.is_running = True
        self.current_metrics.started_at = datetime.now().isoformat()
        self.current_metrics.provider_id = provider_mode
        self._cancel_event = asyncio.Event()

        if provider_mode == "demo":
            # For demo mode (and serverless environments like Vercel), complete the pipeline
            # quickly before returning so state is immediately available.
            await self._run_scan_pipeline(
                category_ids=category_ids,
                max_businesses=max_businesses,
                max_lookups=max_lookups,
                provider_mode=provider_mode,
                custom_csv_content=custom_csv_content,
                max_spend_guard_dollars=max_spend_guard_dollars,
            )
        else:
            self._scan_task = asyncio.create_task(
                self._run_scan_pipeline(
                    category_ids=category_ids,
                    max_businesses=max_businesses,
                    max_lookups=max_lookups,
                    provider_mode=provider_mode,
                    custom_csv_content=custom_csv_content,
                    max_spend_guard_dollars=max_spend_guard_dollars,
                )
            )
        return True

    async def _run_scan_pipeline(
        self,
        category_ids: List[str],
        max_businesses: int,
        max_lookups: int,
        provider_mode: str,
        custom_csv_content: Optional[str],
        max_spend_guard_dollars: float,
    ):
        """Execute the six stages of the scan pipeline."""
        try:
            # Stage 1: Preparing
            self.current_metrics.stage = "Preparing"
            await self._broadcast("progress", self.get_progress())

            provider: BaseBusinessProvider
            demo_provider_instance: Optional[DemoBusinessProvider] = None

            if provider_mode == "google_places":
                google_key = AppSettings.get_google_key()
                if not google_key:
                    raise ValueError("Google Places API Key is not configured. Please add it in Settings.")
                places_service = GooglePlacesService(api_key=google_key)
                provider = GooglePlacesProvider(service=places_service)
            elif provider_mode == "licensed_dataset":
                provider = LicensedDatasetProvider(custom_csv_content=custom_csv_content)
            else:
                demo_provider_instance = DemoBusinessProvider()
                provider = demo_provider_instance

            self.current_metrics.attribution_text = provider.attribution_text
            self.current_metrics.allows_export = provider.allows_csv_export

            # Initialize Twilio Service if live provider or if demo allows real lookup
            twilio_creds = AppSettings.get_twilio_credentials()
            twilio_service: Optional[TwilioLookupService] = None
            if twilio_creds["api_secret"] and (twilio_creds["api_key_sid"] or twilio_creds["account_sid"]):
                twilio_service = TwilioLookupService(
                    account_sid=twilio_creds["account_sid"],
                    api_key_sid=twilio_creds["api_key_sid"],
                    api_secret=twilio_creds["api_secret"],
                )

            # Stage 2: Discovering businesses
            self.current_metrics.stage = "Discovering businesses"
            await self._broadcast("progress", self.get_progress())

            discovered_records = await provider.discover(
                category_ids=category_ids,
                max_results=max_businesses,
                cancel_event=self._cancel_event,
            )

            self.current_metrics.businesses_discovered = len(discovered_records)
            if provider_mode == "google_places":
                # Estimate Google searches used
                num_reqs = max(1, (len(discovered_records) + 19) // 20)
                self.current_metrics.estimated_cost_dollars += num_reqs * EST_GOOGLE_PLACES_SEARCH_COST

            await self._broadcast("progress", self.get_progress())

            if self._cancel_event.is_set():
                self.stop_scan()
                return

            # Stage 3: Validating numbers & deduplication
            self.current_metrics.stage = "Validating numbers"
            await self._broadcast("progress", self.get_progress())

            # Map from normalized E.164 -> list of business records with this number
            phone_to_businesses: Dict[str, List[Dict[str, Any]]] = {}
            processed_items: List[Dict[str, Any]] = []

            for rec in discovered_records:
                norm_phone = normalize_phone_number(rec.raw_phone)

                item = {
                    "id": rec.id,
                    "name": rec.name,
                    "address": rec.address,
                    "phone": rec.raw_phone or "",
                    "formatted_phone": norm_phone.formatted if norm_phone.is_valid else (rec.raw_phone or ""),
                    "e164": norm_phone.e164,
                    "is_phone_valid": norm_phone.is_valid,
                    "skip_reason": norm_phone.skip_reason,
                    "website": rec.website or "",
                    "category": rec.category,
                    "category_id": rec.category_id,
                    "carrier": "Unknown",
                    "line_type": "unknown",
                    "match_status": STATUS_UNKNOWN,
                    "match_notes": "",
                    "place_id": rec.place_id,
                    "provider_source": rec.provider_source,
                    "allows_export": rec.allows_export,
                }
                processed_items.append(item)

                if norm_phone.is_valid and norm_phone.e164:
                    self.current_metrics.valid_phones += 1
                    phone_to_businesses.setdefault(norm_phone.e164, []).append(item)
                else:
                    self.current_metrics.skipped_numbers += 1
                    item["match_notes"] = norm_phone.skip_reason or "No valid phone number"

            self.records = processed_items
            await self._broadcast("progress", self.get_progress())

            if self._cancel_event.is_set():
                self.stop_scan()
                return

            # Stage 4: Checking carriers
            self.current_metrics.stage = "Checking carriers"
            await self._broadcast("progress", self.get_progress())

            unique_e164_numbers = list(phone_to_businesses.keys())

            for e164 in unique_e164_numbers:
                if self._cancel_event.is_set():
                    break

                # Enforce Max Lookups and Spend Guard
                if self.current_metrics.numbers_checked >= max_lookups:
                    logger.info("Reached maximum lookups limit (%d)", max_lookups)
                    break

                if self.current_metrics.estimated_cost_dollars >= max_spend_guard_dollars:
                    logger.warning("Spend guard limit reached ($%.2f)", max_spend_guard_dollars)
                    break

                carrier_name: Optional[str] = None
                line_type: str = "unknown"
                is_billable = False

                if provider_mode == "demo" or not twilio_service:
                    # In demo mode, use simulated carrier data if available
                    if demo_provider_instance:
                        # Match by phone or first linked item's raw phone
                        linked = phone_to_businesses.get(e164, [{}])[0]
                        sim = demo_provider_instance.get_simulated_carrier_info(
                            linked.get("phone", "")
                        ) or demo_provider_instance.get_simulated_carrier_info(linked.get("id", ""))
                        if sim:
                            carrier_name = sim.get("carrier_name")
                            line_type = sim.get("line_type") or "unknown"
                        else:
                            carrier_name = "AT&T Corp."
                            line_type = "landline"
                    else:
                        carrier_name = "Unknown"
                        line_type = "unknown"

                    # Realistic micro-delay for UI feel
                    await asyncio.sleep(0.08)
                else:
                    # Live Twilio Lookup v2 call
                    lookup_res = await twilio_service.lookup_number(e164)
                    carrier_name = lookup_res.carrier_name
                    line_type = lookup_res.line_type
                    is_billable = lookup_res.is_billable

                    if lookup_res.status not in {"success", "not_found"}:
                        self.current_metrics.failed_lookups += 1

                self.current_metrics.numbers_checked += 1
                if is_billable:
                    self.current_metrics.estimated_cost_dollars += EST_TWILIO_LOOKUP_COST

                # Stage 5: Classification for all businesses sharing this number
                classification = classify_carrier(carrier_name)

                for b in phone_to_businesses.get(e164, []):
                    b["carrier"] = carrier_name or "Unknown"
                    b["line_type"] = line_type or "unknown"
                    b["match_status"] = classification.status
                    b["match_notes"] = classification.notes

                # Update counts
                if classification.status == STATUS_COMCAST_MATCH:
                    self.current_metrics.comcast_matches += len(phone_to_businesses.get(e164, []))
                elif classification.status == STATUS_POSSIBLE_MATCH:
                    self.current_metrics.possible_matches += len(phone_to_businesses.get(e164, []))
                elif classification.status == STATUS_NOT_MATCH:
                    self.current_metrics.not_matches += len(phone_to_businesses.get(e164, []))
                else:
                    self.current_metrics.unknowns += len(phone_to_businesses.get(e164, []))

                await self._broadcast("progress", self.get_progress())

            # Mark any remaining valid numbers that weren't checked due to limit
            for e164 in unique_e164_numbers[self.current_metrics.numbers_checked :]:
                for b in phone_to_businesses.get(e164, []):
                    b["match_notes"] = "Lookup omitted due to lookup limit or spend guard"

            # Stage 6: Processing results and complete
            if self._cancel_event.is_set():
                self.current_metrics.stage = "Stopped"
                self.current_metrics.is_stopped = True
            else:
                self.current_metrics.stage = "Completed"

            self.current_metrics.is_running = False
            self.current_metrics.completed_at = datetime.now().isoformat()
            await self._broadcast("scan_completed", self.get_progress())

        except Exception as e:
            logger.exception("Scan pipeline failure")
            self.current_metrics.stage = "Failed"
            self.current_metrics.is_running = False
            self.current_metrics.error_message = str(e)
            self.current_metrics.completed_at = datetime.now().isoformat()
            await self._broadcast("scan_failed", self.get_progress())


# Global singleton instance for the app session
scan_manager = ScanManager()
