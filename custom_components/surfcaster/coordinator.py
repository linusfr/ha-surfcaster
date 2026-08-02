"""Data update coordinator for Surfcaster."""

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
	API_TIMEOUT,
	DOMAIN,
	MARINE_PARAMS,
	MARINE_URL,
	UPDATE_INTERVAL_MINUTES,
	WEATHER_PARAMS,
	WEATHER_URL,
	SpotConditions,
)

_LOGGER = logging.getLogger(__name__)

_MAX_CONCURRENT = 5


class SurfcasterCoordinator(DataUpdateCoordinator[dict[str, SpotConditions]]):
	"""Fetch surf conditions from Open-Meteo Marine + Weather APIs."""

	def __init__(self, hass: HomeAssistant, spots: dict) -> None:
		"""Initialize the coordinator."""
		super().__init__(
			hass,
			_LOGGER,
			name=DOMAIN,
			update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
		)
		self.spots = spots
		self._session = async_get_clientsession(hass)
		self._timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

	async def _async_update_data(self) -> dict[str, SpotConditions]:
		"""Fetch marine and wind data for all spots concurrently."""
		sem = asyncio.Semaphore(_MAX_CONCURRENT)

		async def _fetch_one(spot_id: str, spot: dict) -> tuple[str, SpotConditions]:
			async with sem:
				try:
					return spot_id, await self._fetch_spot(spot)
				except Exception as err:
					_LOGGER.warning("Failed to fetch data for %s: %s", spot_id, err)
					return spot_id, SpotConditions()

		tasks = [_fetch_one(sid, s) for sid, s in self.spots.items()]
		results = await asyncio.gather(*tasks)

		data = dict(results)

		if not data:
			raise UpdateFailed("No surf spots configured")

		if all(cond == SpotConditions() for cond in data.values()):
			raise UpdateFailed("All surf spots failed to fetch")

		return data

	async def _fetch_spot(self, spot: dict) -> SpotConditions:
		"""Fetch marine + wind for one spot."""
		lat = spot["latitude"]
		lon = spot["longitude"]

		marine, weather = await asyncio.gather(
			self._fetch_json(
				MARINE_URL,
				{
					"latitude": lat,
					"longitude": lon,
					"hourly": MARINE_PARAMS,
					"timezone": "Europe/Berlin",
					"forecast_days": 3,
				},
			),
			self._fetch_json(
				WEATHER_URL,
				{
					"latitude": lat,
					"longitude": lon,
					"hourly": WEATHER_PARAMS,
					"windspeed_unit": "kn",
					"timezone": "Europe/Berlin",
					"forecast_days": 3,
				},
			),
		)

		return SpotConditions(
			wave_height=_current_or_none(marine, "wave_height"),
			wave_period=_current_or_none(marine, "wave_period"),
			wave_direction=_current_or_none(marine, "wave_direction"),
			wave_height_max=_max_or_none(marine, "wave_height"),
			wave_period_max=_max_or_none(marine, "wave_period"),
			wind_speed=_current_or_none(weather, "wind_speed_10m"),
			wind_direction=_current_or_none(weather, "wind_direction_10m"),
			wind_speed_max=_max_or_none(weather, "wind_speed_10m"),
		)

	async def _fetch_json(self, url: str, params: dict) -> dict[str, Any]:
		"""GET JSON from an API endpoint."""
		async with self._session.get(url, params=params, timeout=self._timeout) as resp:
			resp.raise_for_status()
			return await resp.json()


def _current_or_none(data: dict, key: str) -> float | None:
	"""First non-None value from hourly array, or None."""
	hourly = data.get("hourly", {})
	values = hourly.get(key)
	if not values:
		return None
	for v in values:
		if v is not None:
			return round(v, 1)
	return None


def _max_or_none(data: dict, key: str) -> float | None:
	"""Max non-None value from hourly array, or None."""
	hourly = data.get("hourly", {})
	values = hourly.get(key)
	if not values:
		return None
	filtered = [v for v in values if v is not None]
	return round(max(filtered), 1) if filtered else None
