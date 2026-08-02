"""HA Surfcaster — surf condition monitoring for Home Assistant.

Fetches surf conditions from the Open-Meteo Marine API for configured
surf spots and exposes them as Home Assistant sensors.
"""

from dataclasses import dataclass

DOMAIN = "surfcaster"
NAME = "Surfcaster"
VERSION = "0.1.0"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_NAME = "name"
CONF_SPOTS = "spots"

DEFAULT_SPOTS = {
	"spo": {
		"name": "Sankt Peter-Ording",
		"latitude": 54.30,
		"longitude": 8.65,
	},
	"vorupor": {
		"name": "Nørre Vorupør",
		"latitude": 56.95,
		"longitude": 8.37,
	},
	"hvidesande": {
		"name": "Hvide Sande",
		"latitude": 55.99,
		"longitude": 8.13,
	},
	"sylt": {
		"name": "Sylt-Brandenburg",
		"latitude": 54.91,
		"longitude": 8.31,
	},
	"weissenhaus": {
		"name": "Weißenhäuser Strand",
		"latitude": 54.31,
		"longitude": 10.95,
	},
	"timmendorf": {
		"name": "Timmendorfer Strand",
		"latitude": 53.99,
		"longitude": 10.83,
	},
	"kuehlungsborn": {
		"name": "Kühlungsborn",
		"latitude": 54.15,
		"longitude": 11.75,
	},
}

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
MARINE_PARAMS = "wave_height,wave_direction,wave_period"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_PARAMS = "wind_speed_10m,wind_direction_10m"

API_TIMEOUT = 15
UPDATE_INTERVAL_MINUTES = 30


@dataclass
class SpotConditions:
	"""Current conditions for a single surf spot."""

	wave_height: float | None = None
	wave_period: float | None = None
	wave_direction: float | None = None
	wave_height_max: float | None = None
	wave_period_max: float | None = None
	wind_speed: float | None = None
	wind_direction: float | None = None
	wind_speed_max: float | None = None


@dataclass
class SensorDef:
	"""Describes a sensor entity for a spot."""

	key_suffix: str
	name_suffix: str
	unit: str | None = None
	device_class: str | None = None
	icon: str = "mdi:waves"
	state_class: str | None = "measurement"


SENSORS: list[SensorDef] = [
	SensorDef(
		key_suffix="wave_height",
		name_suffix="Wave Height",
		unit="m",
		device_class="distance",
		icon="mdi:waves",
	),
	SensorDef(
		key_suffix="wave_period",
		name_suffix="Wave Period",
		unit="s",
		icon="mdi:timeline-clock",
	),
	SensorDef(
		key_suffix="wave_direction",
		name_suffix="Wave Direction",
		unit="°",
		icon="mdi:compass",
	),
	SensorDef(
		key_suffix="wave_height_max",
		name_suffix="Wave Height Max",
		unit="m",
		device_class="distance",
		icon="mdi:waves-arrow-up",
	),
	SensorDef(
		key_suffix="wave_period_max",
		name_suffix="Wave Period Max",
		unit="s",
		icon="mdi:timeline-clock-fast",
	),
	SensorDef(
		key_suffix="wind_speed",
		name_suffix="Wind Speed",
		unit="kn",
		device_class="wind_speed",
		icon="mdi:weather-windy",
	),
	SensorDef(
		key_suffix="wind_direction",
		name_suffix="Wind Direction",
		unit="°",
		icon="mdi:windsock",
	),
	SensorDef(
		key_suffix="wind_speed_max",
		name_suffix="Wind Speed Max",
		unit="kn",
		device_class="wind_speed",
		icon="mdi:weather-windy-variant",
	),
]
