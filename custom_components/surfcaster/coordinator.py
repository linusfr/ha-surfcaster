"""Data update coordinator for Surfcaster."""

import asyncio
import logging
import time
from collections import OrderedDict
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
	API_TIMEOUT,
	DOMAIN,
	FORECAST_DAYS,
	MARINE_PARAMS,
	MARINE_URL,
	TIDE_INTERVAL_HOURS,
	TIDE_LENGTH,
	TIDE_PARAMS,
	TIDE_URL,
	UPDATE_INTERVAL_MINUTES,
	WEATHER_PARAMS,
	WEATHER_URL,
	SpotConditions,
	TideExtreme,
)

_LOGGER = logging.getLogger(__name__)

_MAX_CONCURRENT = 5


class SurfcasterCoordinator(DataUpdateCoordinator[dict[str, SpotConditions]]):
	"""Fetch surf conditions from Open-Meteo Marine + Weather APIs."""

	def __init__(self, hass: HomeAssistant, spots: dict, tide_api_key: str | None = None) -> None:
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
		self._forecasts: dict[str, dict[str, list[float | None]]] = {}
		self._series: dict[str, list[dict[str, float | None]]] = {}
		self._tide_api_key = tide_api_key
		self._tides: dict[str, list[TideExtreme]] = {}
		self._tide_last_fetch: dict[str, float] = {}

	@property
	def has_tides(self) -> bool:
		"""True when a tide API key is configured."""
		return bool(self._tide_api_key)

	async def _async_update_data(self) -> dict[str, SpotConditions]:
		"""Fetch marine and wind data for all spots concurrently."""
		sem = asyncio.Semaphore(_MAX_CONCURRENT)
		raw_marine: dict[str, dict] = {}
		raw_weather: dict[str, dict] = {}

		async def _fetch_one(spot_id: str, spot: dict) -> tuple[str, SpotConditions]:
			async with sem:
				try:
					cond, rmarine, rweather = await self._fetch_spot(spot)
					raw_marine[spot_id] = rmarine
					raw_weather[spot_id] = rweather
					return spot_id, cond
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

		self._forecasts = {}
		self._series = {}
		for spot_id in data:
			if spot_id in raw_marine:
				self._forecasts[spot_id] = _compute_forecast(
					raw_marine[spot_id].get("hourly", {}),
					raw_weather[spot_id].get("hourly", {}),
				)
				self._series[spot_id] = _build_series(
					raw_marine[spot_id].get("hourly", {}),
					raw_weather[spot_id].get("hourly", {}),
					self._tides.get(spot_id, []),
				)

		if self._tide_api_key:
			await self._fetch_tides()

		return data

	async def _fetch_tides(self) -> None:
		"""Fetch tide extremes from WorldTides API (cached per spot, 6h TTL)."""
		now = time.monotonic()
		sem = asyncio.Semaphore(_MAX_CONCURRENT)

		async def _fetch_one(spot_id: str, spot: dict) -> None:
			async with sem:
				if spot_id in self._tide_last_fetch:
					elapsed = now - self._tide_last_fetch[spot_id]
					if elapsed < TIDE_INTERVAL_HOURS * 3600:
						return
				try:
					data = await self._fetch_json(
						TIDE_URL,
						{
							TIDE_PARAMS: "",
							"lat": spot["latitude"],
							"lon": spot["longitude"],
							"length": TIDE_LENGTH,
							"key": self._tide_api_key,
						},
					)
					extremes = data.get("extremes", [])
					self._tides[spot_id] = [
						TideExtreme(
							dt=e["dt"],
							height=round(e["height"], 2),
							type=e["type"],
						)
						for e in extremes
					]
					self._tide_last_fetch[spot_id] = now
				except Exception as err:
					_LOGGER.warning("Tide fetch failed for %s: %s", spot_id, err)

		tasks = [_fetch_one(sid, s) for sid, s in self.spots.items()]
		await asyncio.gather(*tasks)

	async def _fetch_spot(self, spot: dict) -> tuple[SpotConditions, dict, dict]:
		"""Fetch marine + wind for one spot, returning raw data too."""
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
					"forecast_days": FORECAST_DAYS,
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
					"forecast_days": FORECAST_DAYS,
				},
			),
		)

		return (
			SpotConditions(
				wave_height=_current_or_none(marine, "wave_height"),
				wave_period=_current_or_none(marine, "wave_period"),
				wave_direction=_current_or_none(marine, "wave_direction"),
				wave_height_max=_max_or_none(marine, "wave_height"),
				wave_period_max=_max_or_none(marine, "wave_period"),
				wind_speed=_current_or_none(weather, "wind_speed_10m"),
				wind_direction=_current_or_none(weather, "wind_direction_10m"),
				wind_speed_max=_max_or_none(weather, "wind_speed_10m"),
			),
			marine,
			weather,
		)

	async def _fetch_json(self, url: str, params: dict) -> dict[str, Any]:
		"""GET JSON from an API endpoint."""
		async with self._session.get(url, params=params, timeout=self._timeout) as resp:
			resp.raise_for_status()
			return await resp.json()

	def get_forecast(self, spot_id: str, metric_key: str, day_offset: int) -> float | None:
		"""Return the daily max forecast for a metric on a given day offset."""
		vals = self._forecasts.get(spot_id, {}).get(metric_key, [])
		if day_offset < len(vals):
			return vals[day_offset]
		return None

	def get_series(self, spot_id: str) -> list[dict[str, float | None]] | None:
		"""Return the full hourly forecast series for a spot, or None if missing."""
		return self._series.get(spot_id)

	def get_tides(self, spot_id: str) -> list[TideExtreme]:
		"""Return tide extremes for a spot, or empty list."""
		return self._tides.get(spot_id, [])


def _build_series(
	marine_hourly: dict,
	weather_hourly: dict,
	tides: list[TideExtreme] | None = None,
) -> list[dict[str, float | None]]:
	"""Build hourly forecast series from marine + weather raw data.

	Returns a list of dicts with compact keys suitable for apexcharts:
	t=datetime, h=wave_height, p=wave_period, wd=wave_direction,
	ws=wind_speed, wdi=wind_direction, ti=tide_height (if tide data available).
	"""
	times = marine_hourly.get("time", [])
	if not times:
		return []

	wh = marine_hourly.get("wave_height", [])
	wp = marine_hourly.get("wave_period", [])
	wdir = marine_hourly.get("wave_direction", [])
	ws = weather_hourly.get("wind_speed_10m", [])
	wd = weather_hourly.get("wind_direction_10m", [])

	tide_ts: dict[int, float] = {}
	if tides:
		for ex in tides:
			tide_ts[ex.dt] = ex.height

	series: list[dict[str, float | None]] = []
	m = max(len(times), len(wh), len(wp), len(wdir), len(ws), len(wd))
	for i in range(m):
		tt = times[i] if i < len(times) else None
		point: dict[str, float | None] = {"t": tt}
		if i < len(wh) and wh[i] is not None:
			point["h"] = round(wh[i], 1)
		if i < len(wp) and wp[i] is not None:
			point["p"] = round(wp[i], 1)
		if i < len(wdir) and wdir[i] is not None:
			point["wd"] = round(wdir[i], 1)
		if i < len(ws) and ws[i] is not None:
			point["ws"] = round(ws[i], 1)
		if i < len(wd) and wd[i] is not None:
			point["wdi"] = round(wd[i], 1)
		if tide_ts and tt:
			point["ti"] = _interp_tide(tt, tide_ts)
		series.append(point)
	return series


def _interp_tide(iso: str, extremes: dict[int, float]) -> float | None:
	"""Linear interpolation of tide height at a given ISO time between nearest extremes."""
	try:
		from datetime import UTC, datetime

		t = datetime.fromisoformat(iso).replace(tzinfo=UTC).timestamp()
	except ValueError, OSError:
		return None

	sorted_ts = sorted(extremes.keys())
	if not sorted_ts:
		return None
	if t <= sorted_ts[0]:
		return round(extremes[sorted_ts[0]], 2)
	if t >= sorted_ts[-1]:
		return round(extremes[sorted_ts[-1]], 2)

	for i in range(len(sorted_ts) - 1):
		if sorted_ts[i] <= t <= sorted_ts[i + 1]:
			t1, t2 = sorted_ts[i], sorted_ts[i + 1]
			h1, h2 = extremes[t1], extremes[t2]
			if t2 == t1:
				return round(h1, 2)
			frac = (t - t1) / (t2 - t1)
			return round(h1 + frac * (h2 - h1), 2)
	return None


def _compute_forecast(marine_hourly: dict, weather_hourly: dict) -> dict[str, list[float | None]]:
	"""Compute daily max values from hourly data."""
	marine_times = marine_hourly.get("time", [])
	weather_times = weather_hourly.get("time", [])
	return {
		"wave_height": _daily_max(marine_hourly.get("wave_height", []), marine_times),
		"wave_period": _daily_max(marine_hourly.get("wave_period", []), marine_times),
		"wind_speed": _daily_max(weather_hourly.get("wind_speed_10m", []), weather_times),
	}


def _daily_max(values: list[float | None], times: list[str]) -> list[float | None]:
	"""Group hourly values by day, return max per day chronologically."""
	if not values or not times:
		return []
	days: OrderedDict[str, list[float]] = OrderedDict()
	for v, t in zip(values, times, strict=False):
		if v is not None:
			day = t[:10]
			if day not in days:
				days[day] = []
			days[day].append(v)
	return [round(max(vals), 1) for vals in days.values()]


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
