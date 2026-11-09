"""Tests for CSV Exporter, Excel UTF-8 BOM, Formula Escaping, and Licensing."""

import io
import pytest
from app.services.csv_exporter import (
    CSV_MANDATORY_HEADERS,
    LicensingRestrictionError,
    export_businesses_to_csv,
    generate_export_filename,
    sanitize_csv_cell,
)


def test_sanitize_csv_cell_formula_injection():
    # Formula characters (=, +, -, @) must be prepended with a single quote
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+15595550142") == "'+15595550142"
    assert sanitize_csv_cell("-50") == "'-50"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    # Safe text remains unchanged
    assert sanitize_csv_cell("Comcast Business") == "Comcast Business"
    assert sanitize_csv_cell("(559) 555-0142") == "(559) 555-0142"
    assert sanitize_csv_cell(None) == ""


def test_export_filename_format():
    fn = generate_export_filename()
    assert fn.startswith("carrierpulse_records_")
    assert fn.endswith(".csv")


def test_export_utf8_bom_and_headers():
    sample_records = [
        {
            "name": "Fresno Premier Dental",
            "address": "1313 E Herndon Ave, Fresno, CA 93720",
            "formatted_phone": "(559) 438-6000",
            "carrier": "Comcast IP Phone",
            "line_type": "fixedVoip",
            "website": "https://fresnopremierdental.example.com",
            "category": "Dentists",
            "match_status": "Comcast Match",
            "allows_export": True,
        },
        {
            "name": "Tower Bistro",
            "address": "820 E Olive Ave, Fresno, CA 93728",
            "formatted_phone": "(559) 268-3410",
            "carrier": "AT&T",
            "line_type": "landline",
            "website": "",
            "category": "Restaurants",
            "match_status": "Not Match",
            "allows_export": True,
        },
    ]

    # Test confirmed_only mode
    csv_bytes = export_businesses_to_csv(sample_records, filter_mode="confirmed_only", enforce_licensing=True)

    # Must start with UTF-8 BOM bytes (\xef\xbb\xbf)
    assert csv_bytes.startswith(b"\xef\xbb\xbf")

    # Decode text
    csv_text = csv_bytes.decode("utf-8-sig")

    # Verify all mandatory headers are present in the first row
    lines = csv_text.splitlines()
    header_line = lines[0]
    for h in CSV_MANDATORY_HEADERS:
        assert h in header_line

    # In confirmed_only mode, only the Comcast match should be exported
    assert "Fresno Premier Dental" in csv_text
    assert "Tower Bistro" not in csv_text


def test_export_licensing_restriction_blocks_google_places():
    restricted_records = [
        {
            "name": "Restricted Google Listing",
            "address": "Fresno, CA",
            "formatted_phone": "(559) 555-9999",
            "carrier": "Comcast",
            "line_type": "fixedVoip",
            "website": "",
            "category": "Restaurants",
            "match_status": "Comcast Match",
            "allows_export": False,  # Restricted source
        }
    ]

    # Must raise LicensingRestrictionError
    with pytest.raises(LicensingRestrictionError) as exc_info:
        export_businesses_to_csv(restricted_records, filter_mode="all", enforce_licensing=True)

    assert "Google Places API" in str(exc_info.value)
