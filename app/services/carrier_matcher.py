"""Carrier Matching and Classification Service.

Classifies carrier strings from Twilio Lookup v2 into:
- Comcast Match
- Possible Match
- Not Match
- Unknown
"""

import re
from typing import NamedTuple, Optional


class CarrierClassification(NamedTuple):
    status: str  # "Comcast Match", "Possible Match", "Not Match", "Unknown"
    raw_carrier: str
    normalized_carrier: str
    matched_alias: Optional[str] = None
    confidence: str = "none"  # "high", "medium", "none"
    notes: str = ""


# Status Constants
STATUS_COMCAST_MATCH = "Comcast Match"
STATUS_POSSIBLE_MATCH = "Possible Match"
STATUS_NOT_MATCH = "Not Match"
STATUS_UNKNOWN = "Unknown"

# Exact and strong aliases for Comcast Match
COMCAST_DIRECT_ALIASES = {
    "comcast",
    "xfinity",
    "comcast business",
    "comcast business communications",
    "comcast business communications llc",
    "comcast ip phone",
    "comcast ip phone llc",
    "comcast cable",
    "comcast cable communications",
    "comcast cable communications llc",
    "comcast phone",
    "comcast phone llc",
    "comcast phone of california",
    "comcast phone of california llc",
    "comcast broadband",
    "xfinity mobile",
    "comcast corporate",
    "comcast opex",
    "comcast telecom",
}

# Regex pattern for direct Comcast / Xfinity mentions with word boundaries
COMCAST_REGEX = re.compile(r"\b(comcast|xfinity)\b", re.IGNORECASE)

# Known legacy acquired entities or unconfirmed affiliates that map to Possible Match
POSSIBLE_AFFILIATE_KEYWORDS = [
    "broadwing",
    "cimco",
    "at&t broadband",  # Historic legacy asset
]


def normalize_carrier_string(raw: Optional[str]) -> str:
    """Normalize raw carrier name: lowercase, strip punctuation, collapse whitespace."""
    if not raw:
        return ""
    text = raw.lower()
    # Replace punctuation characters with spaces, except alphanumeric
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_carrier(raw_carrier: Optional[str]) -> CarrierClassification:
    """Classify carrier name according to PRD FR-04 rules."""
    raw = raw_carrier.strip() if raw_carrier else ""

    if not raw or raw.lower() in {"unknown", "n/a", "none", "null", "undefined"}:
        return CarrierClassification(
            status=STATUS_UNKNOWN,
            raw_carrier=raw,
            normalized_carrier="",
            matched_alias=None,
            confidence="none",
            notes="Carrier information not provided, empty, or unresolvable",
        )

    norm = normalize_carrier_string(raw)

    # 1. Exact alias check
    if norm in COMCAST_DIRECT_ALIASES:
        return CarrierClassification(
            status=STATUS_COMCAST_MATCH,
            raw_carrier=raw,
            normalized_carrier=norm,
            matched_alias=norm,
            confidence="high",
            notes=f"Direct alias match for '{norm}'",
        )

    # 2. Strong word boundary match for Comcast or Xfinity
    if COMCAST_REGEX.search(raw):
        # If it explicitly says "unverified comcast" or "possible comcast"
        if "unverified" in norm or "possible" in norm or "rumored" in norm:
            return CarrierClassification(
                status=STATUS_POSSIBLE_MATCH,
                raw_carrier=raw,
                normalized_carrier=norm,
                matched_alias="unverified comcast signal",
                confidence="medium",
                notes="Contains unverified or possible Comcast reference",
            )

        return CarrierClassification(
            status=STATUS_COMCAST_MATCH,
            raw_carrier=raw,
            normalized_carrier=norm,
            matched_alias=COMCAST_REGEX.search(raw).group(0).lower(),
            confidence="high",
            notes="Contains verified Comcast or Xfinity carrier brand identifier",
        )

    # 3. Possible Match: Historic/Partner affiliates without direct Comcast keyword
    for affiliate in POSSIBLE_AFFILIATE_KEYWORDS:
        if affiliate in norm:
            return CarrierClassification(
                status=STATUS_POSSIBLE_MATCH,
                raw_carrier=raw,
                normalized_carrier=norm,
                matched_alias=affiliate,
                confidence="medium",
                notes=f"Associated with carrier entity '{affiliate}' requiring secondary verification",
            )

    # 4. Identified as another known or distinct carrier
    return CarrierClassification(
        status=STATUS_NOT_MATCH,
        raw_carrier=raw,
        normalized_carrier=norm,
        matched_alias=None,
        confidence="high",
        notes=f"Identified as non-Comcast operator: {raw}",
    )
