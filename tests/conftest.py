"""Test fixtures for Surfcaster."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.surfcaster.const import DEFAULT_SPOTS, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
	"""Enable custom integrations."""
	yield


@pytest.fixture
def spots():
	return {"spo": DEFAULT_SPOTS["spo"]}


@pytest.fixture
def config_entry_data(spots):
	return {"spots": spots}


@pytest.fixture
def mock_config_entry(config_entry_data):
	return MockConfigEntry(
		domain=DOMAIN,
		data=config_entry_data,
		entry_id="test_entry",
	)


@pytest.fixture
def marine_hourly():
	times = ["2026-08-01T00:00", "2026-08-01T01:00", "2026-08-01T02:00"]
	return {
		"hourly": {
			"time": times,
			"wave_height": [1.2, 1.5, 1.0],
			"wave_period": [8.0, 9.0, 7.5],
			"wave_direction": [280.0, 290.0, 270.0],
		},
	}


@pytest.fixture
def weather_hourly():
	times = ["2026-08-01T00:00", "2026-08-01T01:00", "2026-08-01T02:00"]
	return {
		"hourly": {
			"time": times,
			"wind_speed_10m": [12.0, 15.0, 10.0],
			"wind_direction_10m": [180.0, 200.0, 160.0],
		},
	}


def _make_mock_session(marine_hourly, weather_hourly):
	"""Return a mock aiohttp ClientSession with a patched get()."""

	def _response(url, **kwargs):
		data = marine_hourly if "marine-api" in str(url) else weather_hourly
		_url = url

		class Ctx:
			url = _url

			async def __aenter__(self):
				return self

			async def __aexit__(self, *a):
				pass

			async def json(self):
				return data

			def raise_for_status(self):
				pass

		return Ctx()

	session = MagicMock()
	session.get = _response
	return session

	session = MagicMock()
	session.get = _response
	return session


@pytest.fixture(autouse=True)
def mock_clientsession(hass, marine_hourly, weather_hourly):
	"""Replace async_get_clientsession with a mock for all tests."""
	session = _make_mock_session(marine_hourly, weather_hourly)
	with patch(
		"custom_components.surfcaster.coordinator.async_get_clientsession",
		return_value=session,
	):
		yield


@pytest.fixture
async def hass_with_entry(hass: HomeAssistant, mock_config_entry, mock_clientsession):
	mock_config_entry.add_to_hass(hass)
	await async_setup_component(hass, DOMAIN, {})
	await hass.async_block_till_done()
	return hass
