"""Tests for Surfcaster coordinator."""

import pytest

from custom_components.surfcaster.const import DEFAULT_SPOTS
from custom_components.surfcaster.coordinator import SurfcasterCoordinator, _current_or_none, _max_or_none


def test_max_or_none_with_values():
	data = {"hourly": {"wave_height": [1.2, 1.5, 1.0, None]}}
	assert _max_or_none(data, "wave_height") == 1.5


def test_max_or_none_empty():
	assert _max_or_none({}, "wave_height") is None
	assert _max_or_none({"hourly": {}}, "wave_height") is None
	assert _max_or_none({"hourly": {"wave_height": []}}, "wave_height") is None


def test_current_or_none_first_value():
	data = {"hourly": {"wave_height": [None, None, 1.5, 2.0]}}
	assert _current_or_none(data, "wave_height") == 1.5


def test_current_or_none_empty():
	assert _current_or_none({}, "wave_height") is None


@pytest.mark.asyncio
async def test_coordinator_fetch(hass, spots):
	coordinator = SurfcasterCoordinator(hass, spots)
	result = await coordinator._async_update_data()

	assert "spo" in result
	assert result["spo"].wave_height == 1.2
	assert result["spo"].wave_height_max == 1.5
	assert result["spo"].wind_speed == 12.0
	assert result["spo"].wind_speed_max == 15.0


@pytest.mark.asyncio
async def test_coordinator_returns_spotconditions_for_all_spots(hass):
	spots = {"spo": DEFAULT_SPOTS["spo"], "sylt": DEFAULT_SPOTS["sylt"]}
	coordinator = SurfcasterCoordinator(hass, spots)
	result = await coordinator._async_update_data()

	assert "spo" in result
	assert "sylt" in result
	assert result["spo"].wave_height is not None
	assert result["sylt"].wave_height is not None
