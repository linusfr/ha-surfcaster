"""HA Surfcaster integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SurfcasterCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Set up Surfcaster from a config entry."""
	hass.data.setdefault(DOMAIN, {})

	spots = entry.data.get("spots", {})
	coordinator = SurfcasterCoordinator(hass, spots)
	await coordinator.async_config_entry_first_refresh()

	hass.data[DOMAIN][entry.entry_id] = coordinator
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

	# Reload when user changes spots via Options.
	entry.async_on_unload(entry.add_update_listener(_async_update_listener))

	return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
	"""Handle options update — reload the entry so sensor platform picks up new spots."""
	await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Unload a config entry."""
	unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
	if unload_ok:
		hass.data[DOMAIN].pop(entry.entry_id)
	return unload_ok
