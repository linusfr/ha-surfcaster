"""Sensor platform for Surfcaster."""

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FORECAST_DAYS, FORECAST_METRICS, SENSORS, SensorDef, SpotConditions
from .coordinator import SurfcasterCoordinator

_DAY_LABELS: dict[int, str] = {0: "Today", 1: "Tomorrow"}

for d in range(2, FORECAST_DAYS):
	_DAY_LABELS[d] = f"Day {d}"


class SurfcasterSensor(SensorEntity):
	"""Sensor for a single surf condition metric at one spot."""

	_attr_should_poll = False

	def __init__(
		self,
		coordinator: SurfcasterCoordinator,
		spot_id: str,
		spot_name: str,
		sensor_def: SensorDef,
	) -> None:
		"""Initialize sensor."""
		self._spot_id = spot_id
		self._key = sensor_def.key_suffix
		self._attr_translation_key = sensor_def.key_suffix
		self._attr_unique_id = f"{spot_id}_{sensor_def.key_suffix}"
		self._attr_name = f"{spot_name} {sensor_def.name_suffix}"
		self._attr_native_unit_of_measurement = sensor_def.unit
		self._attr_icon = sensor_def.icon
		self._attr_state_class = sensor_def.state_class
		if sensor_def.device_class:
			self._attr_device_class = SensorDeviceClass(sensor_def.device_class)
		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN, spot_id)},
			name=spot_name,
			manufacturer="Open-Meteo",
			model="Marine API",
		)

		self.coordinator = coordinator

	@property
	def available(self) -> bool:
		"""Return False when coordinator failed or spot data missing."""
		if not super().available:
			return False
		return self._spot_id in (self.coordinator.data or {})

	@property
	def native_value(self) -> float | None:
		"""Return current value."""
		if self.coordinator.data is None:
			return None
		conditions: SpotConditions | None = self.coordinator.data.get(self._spot_id)
		if conditions is None:
			return None
		return getattr(conditions, self._key, None)

	async def async_added_to_hass(self) -> None:
		"""Register callbacks."""
		self.async_on_remove(
			self.coordinator.async_add_listener(self.async_write_ha_state),
		)


class SurfcasterForecastSensor(SensorEntity):
	"""Sensor for a daily max forecast value (Today, Tomorrow, Day N)."""

	_attr_should_poll = False

	def __init__(
		self,
		coordinator: SurfcasterCoordinator,
		spot_id: str,
		spot_name: str,
		metric: dict,
		day_offset: int,
	) -> None:
		"""Initialize forecast sensor."""
		self._spot_id = spot_id
		self._metric_key = metric["key"]
		self._day_offset = day_offset

		day_label = _DAY_LABELS.get(day_offset, f"Day {day_offset}")
		self._attr_unique_id = f"{spot_id}_{metric['key']}_d{day_offset}"
		self._attr_name = f"{spot_name} {metric['name']} {day_label}"
		self._attr_native_unit_of_measurement = metric.get("unit")
		self._attr_icon = metric.get("icon")
		if metric.get("device_class"):
			self._attr_device_class = SensorDeviceClass(metric["device_class"])
		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN, spot_id)},
			name=spot_name,
			manufacturer="Open-Meteo",
			model="Marine API",
		)

		self.coordinator = coordinator

	@property
	def available(self) -> bool:
		"""Return False when coordinator failed or forecast missing."""
		if not super().available:
			return False
		if self._spot_id not in (self.coordinator.data or {}):
			return False
		return self.coordinator.get_forecast(self._spot_id, self._metric_key, self._day_offset) is not None

	@property
	def native_value(self) -> float | None:
		"""Return forecast max for this day."""
		return self.coordinator.get_forecast(self._spot_id, self._metric_key, self._day_offset)

	async def async_added_to_hass(self) -> None:
		"""Register callbacks."""
		self.async_on_remove(
			self.coordinator.async_add_listener(self.async_write_ha_state),
		)


class SurfcasterSeriesSensor(SensorEntity):
	"""Sensor exposing the full hourly forecast series as an attribute.

	State is current wave height. The ``forecast`` attribute holds the
	full 7-day hourly time series for apexcharts ``data_generator``.
	"""

	_attr_should_poll = False

	def __init__(
		self,
		coordinator: SurfcasterCoordinator,
		spot_id: str,
		spot_name: str,
	) -> None:
		"""Initialize series sensor."""
		self._spot_id = spot_id
		self._attr_unique_id = f"{spot_id}_forecast_series"
		self._attr_name = f"{spot_name} Forecast"
		self._attr_icon = "mdi:waves"
		self._attr_native_unit_of_measurement = "m"
		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN, spot_id)},
			name=spot_name,
			manufacturer="Open-Meteo",
			model="Marine API",
		)
		self.coordinator = coordinator

	@property
	def available(self) -> bool:
		"""Return False when coordinator failed or spot data missing."""
		if not super().available:
			return False
		return self._spot_id in (self.coordinator.data or {})

	@property
	def native_value(self) -> float | None:
		"""Return current wave height as the sensor state."""
		if self.coordinator.data is None:
			return None
		conditions: SpotConditions | None = self.coordinator.data.get(self._spot_id)
		if conditions is None:
			return None
		return conditions.wave_height

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		"""Expose the full hourly forecast series."""
		series = self.coordinator.get_series(self._spot_id)
		return {"forecast": series} if series else {}

	async def async_added_to_hass(self) -> None:
		"""Register callbacks."""
		self.async_on_remove(
			self.coordinator.async_add_listener(self.async_write_ha_state),
		)


class SurfcasterTideSensor(SensorEntity):
	"""Sensor for tide predictions — next high/low times and heights."""

	_attr_should_poll = False

	def __init__(
		self,
		coordinator: SurfcasterCoordinator,
		spot_id: str,
		spot_name: str,
	) -> None:
		"""Initialize tide sensor."""
		self._spot_id = spot_id
		self._attr_unique_id = f"{spot_id}_tide"
		self._attr_name = f"{spot_name} Tide"
		self._attr_icon = "mdi:waves-arrow-up"
		self._attr_native_unit_of_measurement = "m"
		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN, spot_id)},
			name=spot_name,
			manufacturer="Open-Meteo",
			model="Marine API",
		)
		self.coordinator = coordinator

	@property
	def available(self) -> bool:
		"""Available when coordinator has data."""
		if not super().available:
			return False
		return self._spot_id in (self.coordinator.data or {})

	@property
	def native_value(self) -> float | None:
		"""Return current tide height (nearest extreme)."""
		tides = self.coordinator.get_tides(self._spot_id)
		if not tides:
			return None
		now = __import__("time").time()
		nearest = min(tides, key=lambda e: abs(e.dt - now), default=None)
		return nearest.height if nearest else None

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		"""Expose tide extremes."""
		now = __import__("time").time()
		tides = list(self.coordinator.get_tides(self._spot_id))
		future = [t for t in tides if t.dt > now]
		result: dict[str, Any] = {"extremes": [{"dt": t.dt, "height": t.height, "type": t.type} for t in tides[:16]]}
		if future:
			highs = [t for t in future if t.type == "High"]
			lows = [t for t in future if t.type == "Low"]
			if highs:
				result["next_high"] = {"dt": highs[0].dt, "height": highs[0].height}
			if lows:
				result["next_low"] = {"dt": lows[0].dt, "height": lows[0].height}
		return result

	async def async_added_to_hass(self) -> None:
		"""Register callbacks."""
		self.async_on_remove(
			self.coordinator.async_add_listener(self.async_write_ha_state),
		)


async def async_setup_entry(
	hass: HomeAssistant,
	entry: ConfigEntry,
	async_add_entities: AddEntitiesCallback,
) -> None:
	"""Set up Surfcaster sensors."""
	coordinator: SurfcasterCoordinator = hass.data[DOMAIN][entry.entry_id]

	entities: list[SurfcasterSensor | SurfcasterForecastSensor | SurfcasterSeriesSensor | SurfcasterTideSensor] = []
	for spot_id in coordinator.spots:
		spot = coordinator.spots[spot_id]
		spot_name = spot.get("name", spot_id)
		for sensor_def in SENSORS:
			entities.append(SurfcasterSensor(coordinator, spot_id, spot_name, sensor_def))
		for metric in FORECAST_METRICS:
			for day_offset in range(FORECAST_DAYS):
				entities.append(SurfcasterForecastSensor(coordinator, spot_id, spot_name, metric, day_offset))
		entities.append(SurfcasterSeriesSensor(coordinator, spot_id, spot_name))
		if coordinator.has_tides:
			entities.append(SurfcasterTideSensor(coordinator, spot_id, spot_name))

	async_add_entities(entities)
