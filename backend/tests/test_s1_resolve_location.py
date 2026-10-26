"""S1: deterministic postcode → DSO mapping (ticket C-T14-T19 SPEC §1)."""

import pytest

from app.stages.s1_resolve_location import resolve


@pytest.mark.parametrize(
    ("postcode", "dso", "gemeente"),
    [
        ("5600", "Enexis", "Eindhoven"),
        ("5658", "Enexis", "Eindhoven"),
        ("5612 AB", "Enexis", "Eindhoven"),
        ("5612ab", "Enexis", "Eindhoven"),
        ("1000", "Liander", "Amsterdam"),
        ("1099", "Liander", "Amsterdam"),
        ("3000", "Stedin", "Rotterdam"),
        ("3089", "Stedin", "Rotterdam"),
    ],
)
def test_ranges_resolve_inclusive(postcode, dso, gemeente):
    loc, cit = resolve(postcode)
    assert loc["resolved"] is True
    assert (loc["dso"], loc["gemeente"]) == (dso, gemeente)
    assert cit is not None and loc["dso_evidence_citation"] == cit["id"]
    assert "UNVERIFIED" in cit["locator"]


def test_postcode_is_normalised():
    loc, _ = resolve(" 5612ab ")
    assert loc["postcode"] == "5612 AB" and loc["postcode4"] == "5612"


@pytest.mark.parametrize("postcode", ["5599", "5659", "0999", "1100", "2999", "3090", "9999"])
def test_outside_ranges_abstains_instead_of_guessing(postcode):
    loc, cit = resolve(postcode)
    assert cit is None
    assert loc["resolved"] is False and loc["dso"] is None
    assert loc["abstain_reason"] in {"unmapped_postcode", "malformed_postcode"}


@pytest.mark.parametrize("postcode", ["", "56", "abcd", "56123", "5612 ABC", "5612-AB"])
def test_malformed_postcodes(postcode):
    loc, cit = resolve(postcode)
    assert cit is None and loc["abstain_reason"] == "malformed_postcode"


def test_location_and_citation_are_contract_valid(validator_for):
    loc, cit = resolve("5612 AB")
    assert not list(validator_for("LocationResolution").iter_errors(loc))
    assert not list(validator_for("Citation").iter_errors(cit))
    miss, _ = resolve("9999")
    assert not list(validator_for("LocationResolution").iter_errors(miss))
