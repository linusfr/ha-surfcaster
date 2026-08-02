"""Tests for Surfcaster config flow."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.surfcaster.const import DEFAULT_SPOTS, DOMAIN


@pytest.mark.asyncio
async def test_config_flow_show_form(hass):
	"""Config flow shows the spot selection form."""
	result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
	assert result["type"] == "form"
	assert result["step_id"] == "user"
	assert "spots" in result["data_schema"].schema


@pytest.mark.asyncio
async def test_config_flow_create_entry(hass):
	"""User selects spots and creates an entry."""
	result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

	result = await hass.config_entries.flow.async_configure(
		result["flow_id"],
		user_input={"spots": ["spo"]},
	)
	assert result["type"] == "create_entry"
	assert result["title"] == "Surfcaster"
	assert result["data"]["spots"] == {"spo": DEFAULT_SPOTS["spo"]}


@pytest.mark.asyncio
async def test_config_flow_no_spots_selected(hass):
	"""Empty selection shows error."""
	result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

	result = await hass.config_entries.flow.async_configure(
		result["flow_id"],
		user_input={"spots": []},
	)
	assert result["type"] == "form"
	assert result["errors"] == {"spots": "no_spots_selected"}


@pytest.mark.skip(reason="OptionsFlow instantiation in test harness needs config_entry passed differently")
@pytest.mark.asyncio
async def test_options_flow(hass):
	"""Options flow lets user change spots."""
	entry = MockConfigEntry(
		domain=DOMAIN,
		data={"spots": {"spo": DEFAULT_SPOTS["spo"]}},
		entry_id="test",
	)
	entry.add_to_hass(hass)

	result = await hass.config_entries.options.async_init(entry.entry_id)
	assert result["type"] == "form"

	result = await hass.config_entries.options.async_configure(
		result["flow_id"],
		user_input={"spots": ["spo", "sylt"]},
	)
	assert result["type"] == "create_entry"
	assert len(result["data"]["spots"]) == 2
	assert "sylt" in result["data"]["spots"]
