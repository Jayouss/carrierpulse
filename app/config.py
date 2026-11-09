"""Configuration and Credential Management for Fresno Carrier Finder."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import keyring
from keyring.errors import KeyringError

BASE_DIR = Path(__file__).resolve().parent.parent
KEYRING_SERVICE_NAME = "fresno_carrier_finder"

# Keys stored in keyring or environment
KEY_GOOGLE_PLACES = "GOOGLE_PLACES_API_KEY"
KEY_TWILIO_ACCOUNT_SID = "TWILIO_ACCOUNT_SID"
KEY_TWILIO_API_KEY_SID = "TWILIO_API_KEY_SID"
KEY_TWILIO_API_SECRET = "TWILIO_API_SECRET"

# Fresno Geographic Defaults
FRESNO_LAT = 36.7468422
FRESNO_LNG = -119.7725868
FRESNO_SEARCH_RADIUS_METERS = 25000  # 25 km covers Fresno & Clovis metro

# Standard Business Categories
DEFAULT_CATEGORIES = [
    {"id": "restaurant", "label": "Restaurants", "query": "restaurants in Fresno CA", "place_type": "restaurant"},
    {"id": "dentist", "label": "Dentists", "query": "dentists in Fresno CA", "place_type": "dentist"},
    {"id": "auto_repair", "label": "Auto Repair Shops", "query": "auto repair in Fresno CA", "place_type": "car_repair"},
    {"id": "plumber", "label": "Plumbers", "query": "plumbers in Fresno CA", "place_type": "plumber"},
    {"id": "law_firm", "label": "Law Firms / Professional Offices", "query": "law firms in Fresno CA", "place_type": "lawyer"},
]

# Cost Estimates
EST_TWILIO_LOOKUP_COST = 0.005  # $0.005 per Line Type Intelligence lookup
EST_GOOGLE_PLACES_SEARCH_COST = 0.032  # $0.032 per Places Text Search (New) request

# In-memory runtime override cache (useful if keyring fails or for testing)
_runtime_secret_cache: Dict[str, str] = {}


def _load_env_file():
    """Load simple key=value pairs from .env if present and not yet loaded in os.environ."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("\"'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


_load_env_file()


def _get_secret(key_name: str) -> Optional[str]:
    """Retrieve secret with order: runtime cache -> keyring -> environment variables."""
    if key_name in _runtime_secret_cache and _runtime_secret_cache[key_name]:
        return _runtime_secret_cache[key_name]

    try:
        val = keyring.get_password(KEYRING_SERVICE_NAME, key_name)
        if val:
            return val
    except (KeyringError, Exception):
        pass

    return os.getenv(key_name)


def _set_secret(key_name: str, value: Optional[str]) -> bool:
    """Store secret into keyring with runtime cache fallback."""
    clean_val = value.strip() if value else ""
    _runtime_secret_cache[key_name] = clean_val

    try:
        if clean_val:
            keyring.set_password(KEYRING_SERVICE_NAME, key_name, clean_val)
        else:
            try:
                keyring.delete_password(KEYRING_SERVICE_NAME, key_name)
            except Exception:
                pass
        return True
    except (KeyringError, Exception):
        # Fallback to local memory / env
        return True


def mask_secret(secret: Optional[str]) -> str:
    """Return a masked representation (e.g. AIzaSy...7xQ) without revealing full secret."""
    if not secret:
        return ""
    s = secret.strip()
    if len(s) <= 8:
        return "****"
    return f"{s[:4]}...{s[-4:]}"


class AppSettings:
    """Application settings accessor."""

    VERSION = "1.0.0"
    APP_NAME = "Fresno Carrier Finder"
    LOCATION = "Fresno, California, USA"

    @classmethod
    def get_google_key(cls) -> Optional[str]:
        return _get_secret(KEY_GOOGLE_PLACES)

    @classmethod
    def set_google_key(cls, key: Optional[str]) -> bool:
        return _set_secret(KEY_GOOGLE_PLACES, key)

    @classmethod
    def get_twilio_credentials(cls) -> Dict[str, Optional[str]]:
        return {
            "account_sid": _get_secret(KEY_TWILIO_ACCOUNT_SID),
            "api_key_sid": _get_secret(KEY_TWILIO_API_KEY_SID),
            "api_secret": _get_secret(KEY_TWILIO_API_SECRET),
        }

    @classmethod
    def set_twilio_credentials(
        cls,
        account_sid: Optional[str],
        api_key_sid: Optional[str],
        api_secret: Optional[str],
    ) -> bool:
        r1 = _set_secret(KEY_TWILIO_ACCOUNT_SID, account_sid)
        r2 = _set_secret(KEY_TWILIO_API_KEY_SID, api_key_sid)
        r3 = _set_secret(KEY_TWILIO_API_SECRET, api_secret)
        return r1 and r2 and r3

    @classmethod
    def is_configured(cls) -> bool:
        """Check if both Google and Twilio credentials are present."""
        has_google = bool(cls.get_google_key())
        twilio = cls.get_twilio_credentials()
        # Twilio needs either (account_sid + api_secret/auth_token) or (api_key_sid + api_secret)
        has_twilio = bool(twilio["api_secret"] and (twilio["api_key_sid"] or twilio["account_sid"]))
        return has_google and has_twilio

    @classmethod
    def get_masked_settings(cls) -> Dict[str, Any]:
        """Return safe UI-ready configuration dictionary."""
        google_key = cls.get_google_key()
        twilio = cls.get_twilio_credentials()

        return {
            "version": cls.VERSION,
            "app_name": cls.APP_NAME,
            "location": cls.LOCATION,
            "is_configured": cls.is_configured(),
            "google": {
                "has_key": bool(google_key),
                "masked_key": mask_secret(google_key),
            },
            "twilio": {
                "has_credentials": bool(twilio["api_secret"] and (twilio["api_key_sid"] or twilio["account_sid"])),
                "account_sid_masked": mask_secret(twilio["account_sid"]),
                "api_key_sid_masked": mask_secret(twilio["api_key_sid"]),
                "has_secret": bool(twilio["api_secret"]),
            },
            "defaults": {
                "categories": DEFAULT_CATEGORIES,
                "max_businesses": int(os.getenv("MAX_BUSINESSES_DEFAULT", 50)),
                "max_lookups": int(os.getenv("MAX_LOOKUPS_DEFAULT", 25)),
                "max_spend_guard_dollars": float(os.getenv("MAX_SPEND_LIMIT_DOLLARS", 5.00)),
                "costs": {
                    "twilio_lookup_per_unit": EST_TWILIO_LOOKUP_COST,
                    "google_search_per_req": EST_GOOGLE_PLACES_SEARCH_COST,
                },
            },
        }
