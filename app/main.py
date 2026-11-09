"""Fresno Carrier Finder - FastAPI Main Application Entrypoint."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import AppSettings
from app.services.csv_exporter import (
    LicensingRestrictionError,
    export_businesses_to_csv,
    generate_export_filename,
)
from app.services.google_places import GooglePlacesService
from app.services.scan_manager import scan_manager
from app.services.twilio_lookup import TwilioLookupService

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fresno_carrier_finder")

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Fresno Carrier Finder",
    description="Find businesses in Fresno, CA and detect Comcast/Xfinity phone carriers.",
    version=AppSettings.VERSION,
    docs_url="/docs",
    redoc_url=None,
)

# CORS setup for local browser usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# -----------------------------------------------------------------------------
# Pydantic Request Models
# -----------------------------------------------------------------------------
class SaveSettingsRequest(BaseModel):
    google_places_api_key: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_api_key_sid: Optional[str] = None
    twilio_api_secret: Optional[str] = None


class StartScanRequest(BaseModel):
    categories: List[str] = Field(default_factory=lambda: ["restaurant", "dentist"])
    max_businesses: int = Field(default=50, ge=1, le=500)
    max_lookups: int = Field(default=25, ge=1, le=250)
    provider_mode: str = Field(default="demo")  # "demo", "google_places", "licensed_dataset"
    max_spend_guard_dollars: float = Field(default=5.00, ge=0.1, le=100.0)
    custom_csv_content: Optional[str] = None


class ExportCsvRequest(BaseModel):
    filter_mode: str = Field(default="confirmed_only")  # "confirmed_only", "include_possible", "all"
    ignore_licensing_guard: bool = Field(default=False)


# -----------------------------------------------------------------------------
# Frontend View
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main single-page application dashboard."""
    settings_data = AppSettings.get_masked_settings()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "settings": settings_data,
            "version": AppSettings.VERSION,
        },
    )


# -----------------------------------------------------------------------------
# Settings & Credential Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/settings")
async def get_settings():
    """Retrieve safe, masked settings for the UI."""
    return AppSettings.get_masked_settings()


@app.post("/api/settings")
async def update_settings(req: SaveSettingsRequest):
    """Save credentials to local encrypted storage (keyring) or local config."""
    if req.google_places_api_key is not None and req.google_places_api_key.strip():
        AppSettings.set_google_key(req.google_places_api_key)

    twilio_update = False
    twilio_creds = AppSettings.get_twilio_credentials()

    account_sid = req.twilio_account_sid if req.twilio_account_sid is not None else twilio_creds["account_sid"]
    api_key_sid = req.twilio_api_key_sid if req.twilio_api_key_sid is not None else twilio_creds["api_key_sid"]
    api_secret = req.twilio_api_secret if req.twilio_api_secret is not None else twilio_creds["api_secret"]

    if req.twilio_api_secret or req.twilio_api_key_sid or req.twilio_account_sid:
        AppSettings.set_twilio_credentials(account_sid, api_key_sid, api_secret)
        twilio_update = True

    return {
        "success": True,
        "message": "Credentials updated securely.",
        "settings": AppSettings.get_masked_settings(),
    }


@app.post("/api/settings/test-google")
async def test_google_connection():
    """Test the configured Google Places API key."""
    key = AppSettings.get_google_key()
    if not key:
        return {"success": False, "status_code": 400, "message": "No Google Places API key found."}

    service = GooglePlacesService(api_key=key)
    res = await service.test_connection()
    return res


@app.post("/api/settings/test-twilio")
async def test_twilio_connection():
    """Test the configured Twilio credentials."""
    creds = AppSettings.get_twilio_credentials()
    if not (creds["api_secret"] and (creds["api_key_sid"] or creds["account_sid"])):
        return {"success": False, "status_code": 400, "message": "Incomplete Twilio credentials."}

    service = TwilioLookupService(
        account_sid=creds["account_sid"],
        api_key_sid=creds["api_key_sid"],
        api_secret=creds["api_secret"],
    )
    res = await service.test_connection()
    return res


# -----------------------------------------------------------------------------
# Scan Orchestration Endpoints
# -----------------------------------------------------------------------------
@app.post("/api/scan/start")
async def start_scan(req: StartScanRequest):
    """Initiate a business discovery and carrier lookup scan."""
    if scan_manager.current_metrics.is_running:
        raise HTTPException(status_code=409, detail="A scan is already in progress.")

    if req.provider_mode == "google_places" and not AppSettings.get_google_key():
        raise HTTPException(
            status_code=400,
            detail="Google Places API Key is required for live discovery. Configure it in Settings or switch to Demo Mode.",
        )

    success = await scan_manager.start_scan(
        category_ids=req.categories,
        max_businesses=req.max_businesses,
        max_lookups=req.max_lookups,
        provider_mode=req.provider_mode,
        custom_csv_content=req.custom_csv_content,
        max_spend_guard_dollars=req.max_spend_guard_dollars,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to initialize scan.")

    return {"success": True, "message": "Scan started", "status": scan_manager.get_progress()}


@app.post("/api/scan/stop")
async def stop_scan():
    """Stop the running scan gracefully."""
    scan_manager.stop_scan()
    return {"success": True, "message": "Scan stop requested.", "status": scan_manager.get_progress()}


@app.get("/api/scan/progress")
async def get_scan_progress():
    """Return the current scan progress snapshot."""
    return scan_manager.get_progress()


@app.get("/api/scan/results")
async def get_scan_results(
    match_status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """Retrieve processed business records with optional server-side filtering."""
    records = scan_manager.get_records()
    filtered = records

    if match_status and match_status.lower() != "all":
        filtered = [r for r in filtered if r.get("match_status", "").lower() == match_status.lower()]

    if category and category.lower() != "all":
        filtered = [
            r for r in filtered
            if r.get("category", "").lower() == category.lower()
            or r.get("category_id", "").lower() == category.lower()
        ]

    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            r for r in filtered
            if q in r.get("name", "").lower()
            or q in r.get("address", "").lower()
            or q in r.get("carrier", "").lower()
            or q in r.get("phone", "").lower()
            or q in r.get("formatted_phone", "").lower()
        ]

    return {
        "total": len(records),
        "filtered_count": len(filtered),
        "records": filtered,
        "progress": scan_manager.get_progress(),
    }


@app.get("/api/scan/stream")
async def stream_scan_events():
    """Server-Sent Events endpoint for real-time progress streaming."""
    async def event_generator():
        queue = scan_manager.subscribe()
        try:
            # Send initial state
            yield f"event: progress\ndata: {json.dumps(scan_manager.get_progress())}\n\n"

            while True:
                msg = await queue.get()
                event_type = msg.get("type", "message")
                data_json = json.dumps(msg.get("data", {}))
                yield f"event: {event_type}\ndata: {data_json}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            scan_manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# -----------------------------------------------------------------------------
# CSV Export & Import Endpoints
# -----------------------------------------------------------------------------
@app.post("/api/export/csv")
async def export_csv(req: ExportCsvRequest):
    """Generate and download UTF-8 BOM CSV for Excel."""
    records = scan_manager.get_records()
    if not records:
        raise HTTPException(status_code=400, detail="No scan records available to export. Run a scan first.")

    enforce_licensing = not req.ignore_licensing_guard

    try:
        csv_bytes = export_businesses_to_csv(
            records=records,
            filter_mode=req.filter_mode,
            enforce_licensing=enforce_licensing,
        )
    except LicensingRestrictionError as e:
        return JSONResponse(
            status_code=403,
            content={
                "compliance_error": True,
                "detail": str(e),
                "title": "Google Places Source Licensing Restriction",
                "recommendation": "Use Provider B (Export-Licensed Dataset) or Demo Mode to export CSV files.",
            },
        )

    filename = generate_export_filename()
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@app.post("/api/import/csv")
async def import_custom_csv(file: UploadFile = File(...)):
    """Upload a user-provided CSV dataset for Provider B (Licensed Business Dataset)."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = content.decode("latin-1")

    # Quick preview
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty.")

    return {
        "success": True,
        "filename": file.filename,
        "row_count": len(lines) - 1,
        "content_snippet": text_content[:500],
        "message": f"Successfully loaded {len(lines) - 1} business rows from {file.filename}.",
    }
