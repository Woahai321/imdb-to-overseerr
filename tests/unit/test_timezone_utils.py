"""Unit tests for timezone utilities."""

import re
import zoneinfo

import pytest

from list_sync.utils.timezone_utils import (
    TIMEZONE_ABBREVIATIONS,
    REGIONAL_PREFERENCES,
    get_all_timezones,
    list_supported_abbreviations,
    normalize_timezone_input,
)


class TestBrazilianTimezones:
    """Tests for Brazilian timezone abbreviations and IANA names."""

    @pytest.mark.parametrize(
        "abbreviation,expected",
        [
            ("BRT", "America/Sao_Paulo"),
            ("AMT", "America/Manaus"),
            ("ACT", "America/Rio_Branco"),
            ("FNT", "America/Noronha"),
        ],
    )
    def test_abbreviation_resolves_to_iana_name(self, abbreviation, expected):
        assert normalize_timezone_input(abbreviation) == expected

    @pytest.mark.parametrize(
        "abbreviation,expected",
        [
            ("BRT", "America/Sao_Paulo"),
            ("AMT", "America/Manaus"),
            ("ACT", "America/Rio_Branco"),
            ("FNT", "America/Noronha"),
            ("BST", "America/Sao_Paulo"),
        ],
    )
    def test_br_region_hint_resolves_conflicts(self, abbreviation, expected):
        assert normalize_timezone_input(abbreviation, region_hint="BR") == expected

    @pytest.mark.parametrize(
        "iana_name",
        [
            "America/Sao_Paulo",
            "America/Manaus",
            "America/Rio_Branco",
            "America/Noronha",
        ],
    )
    def test_iana_names_pass_through_unchanged(self, iana_name):
        assert normalize_timezone_input(iana_name) == iana_name

    def test_brazilian_mappings_are_valid_zones(self):
        for abbreviation in ("BRT", "AMT", "ACT", "FNT"):
            zone_name = TIMEZONE_ABBREVIATIONS[abbreviation]
            zoneinfo.ZoneInfo(zone_name)  # raises if invalid

    def test_br_regional_preferences_registered(self):
        assert "BR" in REGIONAL_PREFERENCES
        for zone_name in REGIONAL_PREFERENCES["BR"].values():
            zoneinfo.ZoneInfo(zone_name)  # raises if invalid


class TestGetAllTimezones:
    """Tests for the automatic IANA timezone listing."""

    @pytest.fixture(scope="class")
    def timezones(self):
        return get_all_timezones()

    def test_returns_all_available_timezones(self, timezones):
        assert len(timezones) == len(zoneinfo.available_timezones())

    def test_includes_common_zones(self, timezones):
        values = {tz["value"] for tz in timezones}
        for expected in ("UTC", "America/Sao_Paulo", "Europe/London", "Asia/Tokyo"):
            assert expected in values

    def test_entries_have_expected_shape(self, timezones):
        offset_pattern = re.compile(r"^UTC[+-]\d{2}:\d{2}$")
        for tz in timezones:
            assert set(tz.keys()) == {"value", "label", "offset"}
            assert tz["label"].startswith(tz["value"])
            assert offset_pattern.match(tz["offset"]), tz

    def test_values_are_valid_zone_names(self, timezones):
        for tz in timezones:
            zoneinfo.ZoneInfo(tz["value"])  # raises if invalid

    def test_sorted_by_offset_then_name(self, timezones):
        def sort_key(tz):
            sign = 1 if tz["offset"][3] == "+" else -1
            hours, minutes = tz["offset"][4:].split(":")
            return (sign * (int(hours) * 60 + int(minutes)), tz["value"])

        assert [tz["value"] for tz in timezones] == [
            tz["value"] for tz in sorted(timezones, key=sort_key)
        ]


class TestListSupportedAbbreviations:
    """Tests for the regional categorization of abbreviations."""

    @pytest.fixture(scope="class")
    def regions(self):
        return list_supported_abbreviations()

    def test_south_american_abbreviations_categorized(self, regions):
        for abbrev in ("BRT", "AMT", "ACT", "FNT", "ART", "CLT"):
            assert abbrev in regions["South America"], abbrev
            assert abbrev not in regions["North America"], abbrev

    def test_north_american_abbreviations_categorized(self, regions):
        for abbrev in ("ET", "PT", "CT"):
            assert abbrev in regions["North America"], abbrev

    def test_military_codes_categorized(self, regions):
        for abbrev in ("A", "R", "Z"):
            assert abbrev in regions["Military"], abbrev

    def test_every_abbreviation_appears_exactly_once(self, regions):
        all_abbrevs = [abbrev for group in regions.values() for abbrev in group]
        assert len(all_abbrevs) == len(set(all_abbrevs))
        assert set(all_abbrevs) == set(TIMEZONE_ABBREVIATIONS.keys())
