"""Sensor platform for Surfcaster."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSORS, SensorDef, SpotConditions
from .coordinator import SurfcasterCoordinator


class SurfcasterSensor(SensorEntity):
	"""Sensor for a single surf condition metric at one spot."""

	_attr_has_entity_name = True
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
		self._attr_name = sensor_def.name_suffix
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


async def async_setup_entry(
	hass: HomeAssistant,
	entry: ConfigEntry,
	async_add_entities: AddEntitiesCallback,
) -> None:
	"""Set up Surfcaster sensors."""
	coordinator: SurfcasterCoordinator = hass.data[DOMAIN][entry.entry_id]

	entities: list[SurfcasterSensor] = []
	for spot_id in coordinator.spots:
		spot = coordinator.spots[spot_id]
		spot_name = spot.get("name", spot_id)
		for sensor_def in SENSORS:
			entities.append(SurfcasterSensor(coordinator, spot_id, spot_name, sensor_def))

	async_add_entities(entities)
