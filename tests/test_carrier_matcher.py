"""Tests for Carrier Matching and Comcast Classification."""

import pytest
from app.services.carrier_matcher import (
    STATUS_COMCAST_MATCH,
    STATUS_NOT_MATCH,
    STATUS_POSSIBLE_MATCH,
    STATUS_UNKNOWN,
    classify_carrier,
)


def test_comcast_direct_matches():
    cases = [
        "Comcast",
        "comcast",
        "Comcast Business",
        "COMCAST BUSINESS COMMUNICATIONS, LLC",
        "Xfinity",
        "Xfinity Mobile",
        "Comcast IP Phone, LLC",
        "Comcast Cable Communications, LLC",
        "Comcast Phone of California, LLC",
        "Comcast Broadband",
    ]
    for c in cases:
        res = classify_carrier(c)
        assert res.status == STATUS_COMCAST_MATCH, f"Failed on '{c}': got {res.status}"
        assert res.raw_carrier == c
        assert res.confidence == "high"


def test_possible_matches():
    cases = [
        "Broadwing Communications LLC",
        "CIMCO Communications",
        "Unverified Comcast Partner",
        "Possible Comcast Affiliate",
    ]
    for c in cases:
        res = classify_carrier(c)
        assert res.status == STATUS_POSSIBLE_MATCH, f"Failed on '{c}': got {res.status}"
        assert res.raw_carrier == c


def test_not_match_other_carriers():
    cases = [
        "AT&T Corp.",
        "Verizon Wireless",
        "Charter Communications Inc.",
        "Spectrum",
        "Frontier Communications",
        "T-Mobile USA, Inc.",
        "Lumen Technologies",
        "Bandwidth.com CLEC",
        "Vonage Business",
    ]
    for c in cases:
        res = classify_carrier(c)
        assert res.status == STATUS_NOT_MATCH, f"Failed on '{c}': got {res.status}"
        assert res.raw_carrier == c


def test_unknown_carrier():
    cases = [
        None,
        "",
        "   ",
        "Unknown",
        "UNKNOWN",
        "N/A",
        "null",
        "none",
    ]
    for c in cases:
        res = classify_carrier(c)
        assert res.status == STATUS_UNKNOWN, f"Failed on '{c}': got {res.status}"
