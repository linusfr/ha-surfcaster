"""Dashboard builder for Surfcaster — creates the surf forecast Lovelace view."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

_DAY_LABELS = ("today", "tomorrow", "day_2", "day_3", "day_4", "day_5", "day_6")

_NORTH = {
	"spo": ("sankt_peter_ording", "SPO"),
	"vorupor": ("norre_vorupor", "Vorupør"),
	"hvidesande": ("hvide_sande", "Hv.Sande"),
	"sylt": ("sylt_brandenburg", "Sylt"),
}
_BALTIC = {
	"weissenhaus": ("weissenhauser_strand", "Weiß.-Strand"),
	"timmendorf": ("timmendorfer_strand", "Timmendorf"),
	"kuehlungsborn": ("kuhlungsborn", "Kühlungsborn"),
}


def _apex(entity_slug: str, spot_title: str) -> dict:
	"""One apexcharts-card for a single spot."""
	entity = f"sensor.{entity_slug}_forecast"
	dg_wave = "return entity.attributes.forecast.map(e => [new Date(e.t).getTime(), e.h]);"
	dg_per = "return entity.attributes.forecast.map(e => [new Date(e.t).getTime(), e.p]);"
	dg_wind = "return entity.attributes.forecast.map(e => [new Date(e.t).getTime(), e.ws]);"

	return {
		"type": "custom:apexcharts-card",
		"graph_span": "7d",
		"span": {"start": "day"},
		"header": {"show": True, "show_states": True, "title": spot_title},
		"series": [
			{
				"entity": entity,
				"data_generator": dg_wave,
				"name": "Wave (m)",
				"type": "area",
				"stroke_width": 0,
				"opacity": 0.3,
				"color": "#00bcd4",
				"group_by": {"func": "avg", "duration": "3h"},
			},
			{
				"entity": entity,
				"data_generator": dg_per,
				"name": "Period (s)",
				"type": "line",
				"stroke_width": 2,
				"color": "#ff9800",
				"group_by": {"func": "avg", "duration": "3h"},
			},
			{
				"entity": entity,
				"data_generator": dg_wind,
				"name": "Wind (kn)",
				"type": "line",
				"stroke_width": 1,
				"opacity": 0.5,
				"color": "#8bc34a",
				"group_by": {"func": "avg", "duration": "3h"},
			},
		],
		"apex_config": {
			"chart": {"height": 220, "toolbar": {"show": False}},
			"xaxis": {"type": "datetime", "tickAmount": 7, "labels": {"format": "E dd"}},
			"stroke": {"curve": "smooth"},
			"grid": {"borderColor": "#333"},
			"theme": {"mode": "dark"},
			"legend": {"show": True, "position": "bottom"},
		},
	}


def build_surf_dashboard(spots: dict[str, dict]) -> dict:
	"""Build the full surf forecast dashboard config.

	spots: {spot_id: {name, latitude, longitude}, ...}
	Returns a dict suitable for ha_config_set_dashboard or LovelaceStorage.
	"""
	north_spots = [(slug, title) for sid, (slug, title) in _NORTH.items() if sid in spots]
	baltic_spots = [(slug, title) for sid, (slug, title) in _BALTIC.items() if sid in spots]

	views = []
	if north_spots:
		views.append(
			{
				"title": "North Sea",
				"path": "north",
				"icon": "mdi:waves",
				"type": "sections",
				"max_columns": 2,
				"sections": [
					{
						"type": "grid",
						"cards": [
							{"type": "heading", "heading": "North Sea", "icon": "mdi:waves"},
						]
						+ [_apex(slug, title) for slug, title in north_spots],
					}
				],
			}
		)
	if baltic_spots:
		views.append(
			{
				"title": "Baltic Sea",
				"path": "baltic",
				"icon": "mdi:waves-arrow-up",
				"type": "sections",
				"max_columns": 3,
				"sections": [
					{
						"type": "grid",
						"cards": [
							{"type": "heading", "heading": "Baltic Sea", "icon": "mdi:waves-arrow-up"},
						]
						+ [_apex(slug, title) for slug, title in baltic_spots],
					}
				],
			}
		)

	return {"views": views}


async def create_forecast_dashboard(hass: HomeAssistant, spots: dict[str, dict]) -> bool:
	"""Create or update the surf-forecast dashboard in Lovelace storage.

	Returns True on success.
	"""
	url_path = "surf-forecast"

	try:
		from homeassistant.components.lovelace.dashboard import LovelaceStorage  # noqa: PLC0415
	except ImportError:
		_LOGGER.warning("Lovelace storage API unavailable (HA version too old?)")
		return False

	lovelace = hass.data.get("lovelace")
	if lovelace is None:
		_LOGGER.warning("Lovelace not loaded, cannot create dashboard")
		return False

	config = build_surf_dashboard(spots)

	# Find existing dashboard entry or create a new one.
	dashboard_id = None
	for item in lovelace.async_items():
		if item.get("url_path") == url_path:
			dashboard_id = item["id"]
			break

	if dashboard_id is None:
		new_item = await lovelace.async_create_item(
			{
				"url_path": url_path,
				"title": "Surf Forecast",
				"icon": "mdi:waves",
				"show_in_sidebar": True,
				"require_admin": False,
				"mode": "storage",
			}
		)
		dashboard_id = new_item["id"]

	# Save the dashboard config
	storage = LovelaceStorage(hass, str(dashboard_id), config)
	await storage.async_save()

	_LOGGER.info("Surf forecast dashboard created/updated at /%s", url_path)
	return True
