"""Phone Number Normalization & Validation Service."""

from typing import Optional, NamedTuple
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat


class NormalizedPhone(NamedTuple):
    raw: str
    e164: Optional[str]
    formatted: str
    is_valid: bool
    skip_reason: Optional[str] = None
    extension: Optional[str] = None


def normalize_phone_number(raw_phone: Optional[str], default_region: str = "US") -> NormalizedPhone:
    """Validate and normalize a phone number using phonenumbers.

    Returns a NormalizedPhone namedtuple containing:
    - raw: raw input string
    - e164: standardized E.164 string (e.g. +15595550142) or None if invalid
    - formatted: user-friendly formatted string (e.g. (559) 555-0142)
    - is_valid: boolean indicating if it's a valid phone number
    - skip_reason: explanation if skipped / invalid
    - extension: any detected extension (stripped from E.164)
    """
    if not raw_phone or not raw_phone.strip():
        return NormalizedPhone(
            raw=raw_phone or "",
            e164=None,
            formatted="",
            is_valid=False,
            skip_reason="Missing or empty phone number",
        )

    cleaned_raw = raw_phone.strip()

    try:
        parsed = phonenumbers.parse(cleaned_raw, default_region)
    except NumberParseException as e:
        return NormalizedPhone(
            raw=cleaned_raw,
            e164=None,
            formatted=cleaned_raw,
            is_valid=False,
            skip_reason=f"Parse error: {e._msg}",
        )

    if not phonenumbers.is_valid_number(parsed):
        # Check if possible number
        is_possible = phonenumbers.is_possible_number(parsed)
        reason = "Invalid phone number" if not is_possible else "Number structure possible but invalid"
        return NormalizedPhone(
            raw=cleaned_raw,
            e164=None,
            formatted=cleaned_raw,
            is_valid=False,
            skip_reason=reason,
        )

    # Extract extension if any
    extension = parsed.extension if parsed.extension else None

    # Construct clean E.164 without extension
    # We clear the extension on a copy to format pure E.164
    e164_number = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    if extension and ";" in e164_number:
        # Some formats append ;ext=...
        e164_number = e164_number.split(";")[0]

    # Readable formatted number (National for US numbers, International otherwise)
    if parsed.country_code == 1:
        formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL)
    else:
        formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

    if extension:
        formatted = f"{formatted} ext. {extension}"

    return NormalizedPhone(
        raw=cleaned_raw,
        e164=e164_number,
        formatted=formatted,
        is_valid=True,
        skip_reason=None,
        extension=extension,
    )
