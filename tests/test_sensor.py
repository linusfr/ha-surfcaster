"""Tests for Surfcaster sensors."""

import pytest

_SPO = "sensor.sankt_peter_ording"


@pytest.mark.asyncio
async def test_sensor_native_value(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	state = hass.states.get(f"{_SPO}_wave_height")
	assert state is not None, f"Expected {_SPO}_wave_height to exist, got {list(hass.states.async_entity_ids())}"
	assert state.state == "1.2"
	assert state.attributes["unit_of_measurement"] == "m"
	assert state.attributes["device_class"] == "distance"
	assert state.attributes["friendly_name"] == "Sankt Peter-Ording Wave Height"


@pytest.mark.asyncio
async def test_sensor_device_info(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	eid = f"{_SPO}_wave_height"
	state = hass.states.get(eid)
	assert state is not None, f"Sensor {eid} not found."

	entity_entry = hass.data["entity_registry"].async_get(eid)
	assert entity_entry is not None
	assert entity_entry.device_id is not None

	device = hass.data["device_registry"].async_get(entity_entry.device_id)
	assert device is not None
	assert device.name == "Sankt Peter-Ording"


@pytest.mark.asyncio
async def test_forecast_sensor_today(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	eid = f"{_SPO}_wave_height_today"
	state = hass.states.get(eid)
	assert state is not None, f"Forecast sensor {eid} not found in {list(hass.states.async_entity_ids())}"
	assert state.attributes["friendly_name"] == "Sankt Peter-Ording Wave Height Today"
	assert state.attributes["unit_of_measurement"] == "m"
	assert state.state == "1.5"


@pytest.mark.asyncio
async def test_forecast_sensor_tomorrow(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	eid = f"{_SPO}_wave_height_tomorrow"
	state = hass.states.get(eid)
	assert state is not None, f"Forecast sensor {eid} not found"
	assert state.attributes["friendly_name"] == "Sankt Peter-Ording Wave Height Tomorrow"
	assert state.state == "1.0"


@pytest.mark.asyncio
async def test_forecast_sensor_wind_speed_today(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	eid = f"{_SPO}_wind_speed_today"
	state = hass.states.get(eid)
	assert state is not None, f"Forecast sensor {eid} not found"
	assert state.attributes["friendly_name"] == "Sankt Peter-Ording Wind Speed Today"
	assert state.attributes["unit_of_measurement"] == "kn"
	assert state.state == "15.0"


@pytest.mark.asyncio
async def test_forecast_sensor_device_info(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	eid = f"{_SPO}_wave_height_today"
	entity_entry = hass.data["entity_registry"].async_get(eid)
	assert entity_entry is not None
	assert entity_entry.device_id is not None

	device = hass.data["device_registry"].async_get(entity_entry.device_id)
	assert device is not None
	assert device.name == "Sankt Peter-Ording"


@pytest.mark.asyncio
async def test_series_sensor(hass_with_entry):
	hass = hass_with_entry
	await hass.async_block_till_done()

	eid = f"{_SPO}_forecast"
	state = hass.states.get(eid)
	assert state is not None, f"Series sensor {eid} not found"
	assert state.state == "1.2"
	assert state.attributes["friendly_name"] == "Sankt Peter-Ording Forecast"
	assert state.attributes["unit_of_measurement"] == "m"

	forecast = state.attributes.get("forecast")
	assert forecast is not None
	assert isinstance(forecast, list)
	assert len(forecast) > 0
	assert "h" in forecast[0]
	assert "t" in forecast[0]
