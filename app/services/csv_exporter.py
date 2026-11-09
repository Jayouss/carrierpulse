"""CSV Export Service with Excel BOM, Formula Injection Protection, and Licensing Verification."""

import csv
import datetime
import io
import re
from typing import Any, Dict, List, Optional


class LicensingRestrictionError(Exception):
    """Raised when an export is attempted on data sources that prohibit bulk CSV lead extraction."""
    pass


CSV_MANDATORY_HEADERS = [
    "Business Name",
    "Address",
    "Phone Number",
    "Carrier",
    "Line Type",
    "Website",
    "Category",
    "Match Status",
]

# Spreadsheet formula trigger characters
FORMULA_CHARS = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_cell(value: Any) -> str:
    """Sanitize CSV cell to prevent CSV / Spreadsheet formula injection.

    If value begins with =, +, -, @, prepend a single quote (').
    """
    if value is None:
        return ""
    s = str(value).strip()
    if s and s[0] in FORMULA_CHARS:
        return f"'{s}"
    return s


def generate_export_filename(prefix: str = "carrierpulse_records") -> str:
    """Generate standardized export filename with current date: carrierpulse_records_YYYY-MM-DD.csv"""
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    return f"{prefix}_{date_str}.csv"


def export_businesses_to_csv(
    records: List[Dict[str, Any]],
    filter_mode: str = "confirmed_only",  # "confirmed_only", "include_possible", "all"
    enforce_licensing: bool = True,
) -> bytes:
    """Generate UTF-8 BOM CSV byte buffer for Excel on Windows.

    Filter modes:
    - confirmed_only: only "Comcast Match"
    - include_possible: "Comcast Match" and "Possible Match"
    - all: all processed records

    Raises LicensingRestrictionError if enforce_licensing is True and any record has allows_export=False.
    """
    if enforce_licensing:
        # Check if any record in the batch comes from a restricted source
        restricted = [r for r in records if not r.get("allows_export", False)]
        if restricted:
            raise LicensingRestrictionError(
                f"Export blocked by source compliance policy. {len(restricted)} record(s) originate from "
                "Google Places API, which prohibits bulk business lead downloads under Google Maps Platform ToS. "
                "To export CSV leads, use an Export-Licensed dataset (CSV Import) or Demo Mode."
            )

    # Filter records based on requested filter_mode
    filtered: List[Dict[str, Any]] = []
    for r in records:
        status = r.get("match_status", "Unknown")
        carrier = (r.get("carrier") or "").strip()

        if filter_mode == "confirmed_only":
            # Confirmed Comcast matches only (do not include empty carriers)
            if status == "Comcast Match" and carrier and carrier.lower() != "unknown":
                filtered.append(r)
        elif filter_mode == "include_possible":
            if status in {"Comcast Match", "Possible Match"}:
                filtered.append(r)
        else:  # "all"
            filtered.append(r)

    # Use StringIO with utf-8-sig (UTF-8 with BOM)
    output = io.StringIO()
    # Write UTF-8 BOM explicitly
    output.write("\ufeff")

    writer = csv.writer(output, dialect="excel", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_MANDATORY_HEADERS)

    for r in filtered:
        row = [
            sanitize_csv_cell(r.get("name", "")),
            sanitize_csv_cell(r.get("address", "")),
            sanitize_csv_cell(r.get("formatted_phone") or r.get("phone", "")),
            sanitize_csv_cell(r.get("carrier") or "Unknown"),
            sanitize_csv_cell(r.get("line_type") or "unknown"),
            sanitize_csv_cell(r.get("website") or ""),
            sanitize_csv_cell(r.get("category", "")),
            sanitize_csv_cell(r.get("match_status", "Unknown")),
        ]
        writer.writerow(row)

    return output.getvalue().encode("utf-8")
