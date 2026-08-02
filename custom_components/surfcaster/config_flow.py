"""Config flow for HA Surfcaster."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
	SelectOptionDict,
	SelectSelector,
	SelectSelectorConfig,
	SelectSelectorMode,
)

from .const import CONF_SPOTS, CONF_TIDE_API_KEY, DEFAULT_SPOTS, DOMAIN

_SPOT_OPTIONS = [SelectOptionDict(value=sid, label=spot["name"]) for sid, spot in DEFAULT_SPOTS.items()]


class SurfcasterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
	"""Handle a config flow for Surfcaster."""

	VERSION = 1

	async def async_step_user(self, user_input=None):
		"""Handle the initial step."""
		errors = {}

		if user_input is not None:
			spot_ids = user_input.get(CONF_SPOTS, [])
			spots = {sid: DEFAULT_SPOTS[sid] for sid in spot_ids if sid in DEFAULT_SPOTS}
			if not spots:
				errors[CONF_SPOTS] = "no_spots_selected"
			else:
				return self.async_create_entry(
					title="Surfcaster",
					data={CONF_SPOTS: spots},
				)

		return self.async_show_form(
			step_id="user",
			data_schema=vol.Schema(
				{
					vol.Required(CONF_SPOTS, default=list(DEFAULT_SPOTS.keys())): SelectSelector(
						SelectSelectorConfig(
							options=_SPOT_OPTIONS,
							multiple=True,
							mode=SelectSelectorMode.DROPDOWN,
						),
					),
				}
			),
			errors=errors,
		)

	@staticmethod
	@callback
	def async_get_options_flow(config_entry):
		return SurfcasterOptionsFlow


class SurfcasterOptionsFlow(config_entries.OptionsFlow):
	"""Handle options flow."""

	async def async_step_init(self, user_input=None):
		"""Manage options — add/remove spots, set tide API key."""
		if user_input is not None:
			spot_ids = user_input.get(CONF_SPOTS, [])
			spots = {sid: DEFAULT_SPOTS[sid] for sid in spot_ids if sid in DEFAULT_SPOTS}
			opts: dict[str, Any] = {CONF_SPOTS: spots}
			tide_key = (user_input.get(CONF_TIDE_API_KEY) or "").strip()
			if tide_key:
				opts[CONF_TIDE_API_KEY] = tide_key
			return self.async_create_entry(data=opts)

		current_spots = list(self.config_entry.data.get(CONF_SPOTS, {}).keys())
		current_opts = self.config_entry.options or {}
		current_key = current_opts.get(CONF_TIDE_API_KEY, "")
		if not current_key:
			current_key = self.config_entry.data.get(CONF_TIDE_API_KEY, "")

		schema_dict: dict[vol.Required | vol.Optional, Any] = {
			vol.Required(CONF_SPOTS, default=current_spots): SelectSelector(
				SelectSelectorConfig(
					options=_SPOT_OPTIONS,
					multiple=True,
					mode=SelectSelectorMode.DROPDOWN,
				),
			),
		}
		# Tide API key is optional.
		if current_key:
			schema_dict[vol.Optional(CONF_TIDE_API_KEY, default=current_key)] = str
		else:
			schema_dict[vol.Optional(CONF_TIDE_API_KEY)] = str

		return self.async_show_form(
			step_id="init",
			data_schema=vol.Schema(schema_dict),
		)
