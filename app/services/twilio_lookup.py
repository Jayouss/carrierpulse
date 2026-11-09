"""Twilio Lookup v2 Service for Line Type and Carrier Identification."""

import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

TWILIO_LOOKUP_V2_BASE_URL = "https://lookups.twilio.com/v2/PhoneNumbers"


class TwilioLookupResult:

    def __init__(
        self,
        phone_number: str,
        carrier_name: Optional[str] = None,
        line_type: str = "unknown",
        raw_response: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_code: Optional[int] = None,
        error_message: Optional[str] = None,
        is_billable: bool = False,
    ):
        self.phone_number = phone_number
        self.carrier_name = carrier_name or "Unknown"
        self.line_type = line_type or "unknown"
        self.raw_response = raw_response or {}
        self.status = status
        self.error_code = error_code
        self.error_message = error_message
        self.is_billable = is_billable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phone_number": self.phone_number,
            "carrier_name": self.carrier_name,
            "line_type": self.line_type,
            "status": self.status,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "is_billable": self.is_billable,
        }


class TwilioLookupService:
    """Twilio Lookup v2 client with concurrency limit, retry with exponential backoff, and caching."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        api_key_sid: Optional[str] = None,
        api_secret: Optional[str] = None,
        max_concurrency: int = 3,
        timeout_seconds: float = 12.0,
    ):
        self.account_sid = account_sid
        self.api_key_sid = api_key_sid
        self.api_secret = api_secret
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout = timeout_seconds
        self._cache: Dict[str, TwilioLookupResult] = {}

    def _get_auth_tuple(self) -> Optional[tuple[str, str]]:
        """Return (username, password) for HTTP Basic Auth."""
        if self.api_key_sid and self.api_secret:
            return (self.api_key_sid, self.api_secret)
        if self.account_sid and self.api_secret:
            return (self.account_sid, self.api_secret)
        return None

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and credentials against Twilio Lookup API using a known probe query."""
        auth = self._get_auth_tuple()
        if not auth:
            return {
                "success": False,
                "status_code": 401,
                "message": "Missing Twilio credentials. Provide API Key SID (or Account SID) and Secret.",
            }

        # Probe with Twilio's own US Toll Free number: +18005550199 or Twilio HQ +18448144627
        test_phone = "+18448144627"
        url = f"{TWILIO_LOOKUP_V2_BASE_URL}/{test_phone}?Fields=line_type_intelligence"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, auth=auth)
                if resp.status_code == 200:
                    data = resp.json()
                    lti = data.get("line_type_intelligence") or {}
                    carrier = lti.get("carrier_name", "Twilio / Carrier detected")
                    return {
                        "success": True,
                        "status_code": 200,
                        "message": f"Twilio connection verified successfully. Probe carrier: {carrier}",
                    }
                elif resp.status_code == 401:
                    return {
                        "success": False,
                        "status_code": 401,
                        "message": "Twilio authentication failed. Check API Key SID/Account SID and Secret.",
                    }
                elif resp.status_code == 403:
                    return {
                        "success": False,
                        "status_code": 403,
                        "message": "Twilio forbidden. Ensure your Twilio project has Lookup v2 permission and balance.",
                    }
                else:
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "message": f"Twilio returned HTTP {resp.status_code}: {resp.text[:120]}",
                    }
        except Exception as e:
            logger.exception("Twilio test connection error")
            return {
                "success": False,
                "status_code": 500,
                "message": f"Twilio network connection error: {str(e)}",
            }

    async def lookup_number(self, e164_phone: str) -> TwilioLookupResult:
        """Perform Twilio Lookup v2 with Line Type Intelligence for an E.164 phone number.

        Includes duplicate caching, bounded concurrency, and exponential backoff retry on 429/5xx.
        """
        if not e164_phone or not e164_phone.startswith("+"):
            return TwilioLookupResult(
                phone_number=e164_phone,
                status="invalid_number",
                error_message="Invalid E.164 phone format",
                is_billable=False,
            )

        # Check in-memory cache to avoid repeated paid lookups
        if e164_phone in self._cache:
            cached = self._cache[e164_phone]
            # Cached return is not a new billable lookup
            return TwilioLookupResult(
                phone_number=cached.phone_number,
                carrier_name=cached.carrier_name,
                line_type=cached.line_type,
                raw_response=cached.raw_response,
                status=cached.status,
                error_code=cached.error_code,
                error_message=cached.error_message,
                is_billable=False,
            )

        auth = self._get_auth_tuple()
        if not auth:
            return TwilioLookupResult(
                phone_number=e164_phone,
                status="auth_error",
                error_message="Twilio credentials not configured",
                is_billable=False,
            )

        url = f"{TWILIO_LOOKUP_V2_BASE_URL}/{e164_phone}?Fields=line_type_intelligence"

        async with self.semaphore:
            max_retries = 3
            backoff = 1.0

            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        resp = await client.get(url, auth=auth)

                        if resp.status_code == 200:
                            data = resp.json()
                            lti = data.get("line_type_intelligence") or {}
                            carrier = lti.get("carrier_name") or "Unknown"
                            line_type = lti.get("type") or "unknown"
                            error_code = lti.get("error_code")

                            res = TwilioLookupResult(
                                phone_number=e164_phone,
                                carrier_name=carrier,
                                line_type=line_type,
                                raw_response=data,
                                status="success",
                                error_code=error_code,
                                is_billable=True,
                            )
                            self._cache[e164_phone] = res
                            return res

                        elif resp.status_code == 404:
                            res = TwilioLookupResult(
                                phone_number=e164_phone,
                                carrier_name="Unknown",
                                line_type="unknown",
                                status="not_found",
                                error_message="Number not found in carrier registry",
                                is_billable=False,
                            )
                            self._cache[e164_phone] = res
                            return res

                        elif resp.status_code == 429:
                            # Rate limit hit, wait and retry
                            if attempt < max_retries - 1:
                                await asyncio.sleep(backoff)
                                backoff *= 2.0
                                continue
                            return TwilioLookupResult(
                                phone_number=e164_phone,
                                status="rate_limited",
                                error_code=429,
                                error_message="Twilio rate limit exceeded",
                                is_billable=False,
                            )

                        elif resp.status_code in {500, 502, 503, 504}:
                            # Server error, back off
                            if attempt < max_retries - 1:
                                await asyncio.sleep(backoff)
                                backoff *= 2.0
                                continue
                            return TwilioLookupResult(
                                phone_number=e164_phone,
                                status="server_error",
                                error_code=resp.status_code,
                                error_message=f"Twilio server error {resp.status_code}",
                                is_billable=False,
                            )

                        elif resp.status_code in {401, 403}:
                            return TwilioLookupResult(
                                phone_number=e164_phone,
                                status="auth_error",
                                error_code=resp.status_code,
                                error_message=f"Twilio authentication/permission error {resp.status_code}",
                                is_billable=False,
                            )

                        else:
                            return TwilioLookupResult(
                                phone_number=e164_phone,
                                status="failed",
                                error_code=resp.status_code,
                                error_message=f"HTTP {resp.status_code}: {resp.text[:100]}",
                                is_billable=False,
                            )

                except httpx.TimeoutException:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2.0
                        continue
                    return TwilioLookupResult(
                        phone_number=e164_phone,
                        status="timeout",
                        error_message="Twilio lookup request timed out",
                        is_billable=False,
                    )
                except Exception as e:
                    logger.exception("Twilio lookup error on %s", e164_phone)
                    return TwilioLookupResult(
                        phone_number=e164_phone,
                        status="error",
                        error_message=str(e),
                        is_billable=False,
                    )

            return TwilioLookupResult(
                phone_number=e164_phone,
                status="retry_exhausted",
                error_message="Max retries exhausted for Twilio lookup",
                is_billable=False,
            )
