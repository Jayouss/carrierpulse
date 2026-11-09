"""Tests for Phone Number Normalization and Validation."""

import pytest
from app.services.phone_utils import normalize_phone_number


def test_valid_us_number():
    res = normalize_phone_number("(559) 555-0142")
    assert res.is_valid is True
    assert res.e164 == "+15595550142"
    assert res.formatted == "(559) 555-0142"
    assert res.skip_reason is None
    assert res.extension is None


def test_valid_number_without_punctuation():
    res = normalize_phone_number("5595550199")
    assert res.is_valid is True
    assert res.e164 == "+15595550199"
    assert res.formatted == "(559) 555-0199"


def test_valid_number_with_extension():
    res = normalize_phone_number("(559) 555-0142 ext. 301")
    assert res.is_valid is True
    # The E.164 output must not contain extension characters
    assert res.e164 == "+15595550142"
    assert "ext. 301" in res.formatted
    assert res.extension == "301"


def test_empty_or_none_number():
    res_none = normalize_phone_number(None)
    assert res_none.is_valid is False
    assert res_none.e164 is None
    assert "Missing" in res_none.skip_reason

    res_empty = normalize_phone_number("   ")
    assert res_empty.is_valid is False
    assert res_empty.e164 is None
    assert "Missing" in res_empty.skip_reason


def test_invalid_short_number():
    res = normalize_phone_number("12345")
    assert res.is_valid is False
    assert res.e164 is None
    assert res.skip_reason is not None


def test_invalid_letters():
    res = normalize_phone_number("NOT-A-PHONE")
    assert res.is_valid is False
    assert res.e164 is None
