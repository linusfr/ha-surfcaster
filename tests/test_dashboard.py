"""Tests for Surfcaster dashboard builder."""

from custom_components.surfcaster.const import DEFAULT_SPOTS
from custom_components.surfcaster.dashboard import _BALTIC, _NORTH, build_surf_dashboard


def test_build_empty_spots():
	result = build_surf_dashboard({})
	assert result["views"] == []


def test_build_north_only():
	spots = {"spo": DEFAULT_SPOTS["spo"], "sylt": DEFAULT_SPOTS["sylt"]}
	result = build_surf_dashboard(spots)
	assert len(result["views"]) == 1
	assert result["views"][0]["title"] == "North Sea"
	cards = result["views"][0]["sections"][0]["cards"]
	assert cards[0]["type"] == "heading"
	apex_cards = [c for c in cards if c["type"] == "custom:apexcharts-card"]
	assert len(apex_cards) == 2


def test_build_baltic_only():
	spots = {"timmendorf": DEFAULT_SPOTS["timmendorf"]}
	result = build_surf_dashboard(spots)
	assert len(result["views"]) == 1
	assert result["views"][0]["title"] == "Baltic Sea"


def test_build_all_spots():
	result = build_surf_dashboard(DEFAULT_SPOTS)
	assert len(result["views"]) == 2

	north = result["views"][0]
	baltic = result["views"][1]
	assert north["title"] == "North Sea"
	assert baltic["title"] == "Baltic Sea"

	north_apex = [c for c in north["sections"][0]["cards"] if c["type"] == "custom:apexcharts-card"]
	baltic_apex = [c for c in baltic["sections"][0]["cards"] if c["type"] == "custom:apexcharts-card"]
	assert len(north_apex) == len(_NORTH)
	assert len(baltic_apex) == len(_BALTIC)


def test_apex_card_structure():
	result = build_surf_dashboard({"spo": DEFAULT_SPOTS["spo"]})
	cards = result["views"][0]["sections"][0]["cards"]
	apex_cards = [c for c in cards if c["type"] == "custom:apexcharts-card"]
	apex = apex_cards[0]

	assert apex["graph_span"] == "7d"
	assert apex["header"]["title"] == "SPO"
	assert len(apex["series"]) == 3
	assert apex["series"][0]["name"] == "Wave (m)"
	assert apex["series"][0]["entity"] == "sensor.sankt_peter_ording_forecast"
	assert apex["series"][1]["name"] == "Period (s)"
	assert apex["series"][2]["name"] == "Wind (kn)"
