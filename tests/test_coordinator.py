"""Tests for Surfcaster coordinator."""

import pytest

from custom_components.surfcaster.const import DEFAULT_SPOTS
from custom_components.surfcaster.coordinator import (
	SurfcasterCoordinator,
	_compute_forecast,
	_current_or_none,
	_daily_max,
	_max_or_none,
)


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


def test_daily_max_single_day():
	values = [1.2, 1.5, 1.0]
	times = ["2026-08-02T00:00", "2026-08-02T01:00", "2026-08-02T02:00"]
	assert _daily_max(values, times) == [1.5]


def test_daily_max_multi_day():
	values = [1.0, 2.0, 3.0, 4.0]
	times = [
		"2026-08-02T00:00",
		"2026-08-02T01:00",
		"2026-08-03T00:00",
		"2026-08-03T01:00",
	]
	assert _daily_max(values, times) == [2.0, 4.0]


def test_daily_max_with_nones():
	values = [1.0, None, 3.0, None]
	times = [
		"2026-08-02T00:00",
		"2026-08-02T01:00",
		"2026-08-03T00:00",
		"2026-08-03T01:00",
	]
	assert _daily_max(values, times) == [1.0, 3.0]


def test_daily_max_empty():
	assert _daily_max([], []) == []


def test_compute_forecast():
	marine_times = [
		"2026-08-02T00:00",
		"2026-08-02T01:00",
		"2026-08-03T00:00",
		"2026-08-03T01:00",
	]
	marine = {
		"time": marine_times,
		"wave_height": [1.2, 1.5, 0.8, 1.0],
		"wave_period": [8.0, 9.0, 7.0, 6.0],
	}
	weather_times = marine_times
	weather = {
		"time": weather_times,
		"wind_speed_10m": [10.0, 12.0, 8.0, 9.0],
	}

	result = _compute_forecast(marine, weather)
	assert result["wave_height"] == [1.5, 1.0]
	assert result["wave_period"] == [9.0, 7.0]
	assert result["wind_speed"] == [12.0, 9.0]


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


@pytest.mark.asyncio
async def test_coordinator_forecast(hass, spots):
	coordinator = SurfcasterCoordinator(hass, spots)
	await coordinator._async_update_data()

	wav = coordinator.get_forecast("spo", "wave_height", 0)
	assert wav == 1.5

	assert coordinator.get_forecast("spo", "wave_height", 9) is None
	assert coordinator.get_forecast("spo", "nonexistent", 0) is None
