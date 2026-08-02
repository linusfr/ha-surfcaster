"""HA Surfcaster integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import SurfcasterCoordinator
from .dashboard import create_forecast_dashboard

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Set up Surfcaster from a config entry."""
	hass.data.setdefault(DOMAIN, {})

	spots = entry.data.get("spots", {})
	tide_api_key = (entry.options or {}).get("tide_api_key") or (entry.data or {}).get("tide_api_key")
	coordinator = SurfcasterCoordinator(hass, spots, tide_api_key)
	await coordinator.async_config_entry_first_refresh()

	hass.data[DOMAIN][entry.entry_id] = coordinator
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

	entry.async_on_unload(entry.add_update_listener(_async_update_listener))

	# Register service + auto-create dashboard.
	if not hass.services.has_service(DOMAIN, "create_dashboard"):

		async def _handle(call: ServiceCall) -> None:
			for cfg in hass.config_entries.async_entries(DOMAIN):
				sp = (cfg.data or {}).get("spots", {})
				if sp:
					await _ensure_dashboard(hass, sp)
					break

		hass.services.async_register(DOMAIN, "create_dashboard", _handle)

	hass.async_create_background_task(
		_ensure_dashboard(hass, spots),
		f"{DOMAIN} dashboard",
	)

	return True


async def _ensure_dashboard(hass: HomeAssistant, spots: dict) -> None:
	"""Create or update the surf forecast dashboard (best-effort)."""
	try:
		await create_forecast_dashboard(hass, spots)
	except Exception:
		_LOGGER.debug("Dashboard creation skipped", exc_info=True)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
	"""Handle options update — reload the entry so sensor platform picks up new spots."""
	await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Unload a config entry."""
	unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
	if unload_ok:
		hass.data[DOMAIN].pop(entry.entry_id)
	return unload_ok
