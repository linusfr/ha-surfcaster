# Surfcaster

Surf condition monitoring for Home Assistant. Know when to paddle out.

Surfcaster pulls real-time swell, wind, and water temp data from the
[Open-Meteo Marine API](https://open-meteo.com/en/docs/marine-api) and serves it
up as Home Assistant sensors. No API key needed — Open-Meteo is free and open.

## What You Get

| Sensor | What It Tells You |
|---|---|
| Wave height | How big the surf is right now |
| Wave period | Seconds between sets — longer = more powerful |
| Wave direction | Where the swell is coming from |
| Wind speed & direction | Onshore mess or offshore glass? |
| 7-day daily max forecast | Peak each day for wave height, period, wind |
| Hourly forecast series | Full 168-hour time series (for apexcharts graph) |

## Default Spots

Seven North Sea / Baltic breaks ship out of the box:

| Spot | Coordinates | Why It's Here |
|---|---|---|
| **Sankt Peter-Ording** | 54.30, 8.65 | Classic North Sea beachie. Works on W–NW swell. |
| **Nørre Vorupør** | 56.95, 8.37 | Danish reef break. Long-period North Sea groundswell magnet. |
| **Hvide Sande** | 55.99, 8.13 | Narrow peninsula — offshore wind on both sides. |
| **Sylt-Brandenburg** | 54.91, 8.31 | Germany's most consistent surf. Winter swell machine. |
| **Weißenhäuser Strand** | 54.31, 10.95 | Baltic beachie. NE windswell spot. |
| **Timmendorfer Strand** | 53.99, 10.83 | Lübeck Bay. Works on NE–E wind. |
| **Kühlungsborn** | 54.15, 11.75 | Mecklenburg coast. Long fetch when Baltic cooperates. |

Add your own spots in the integration options — any lat/lon that Open-Meteo covers.

## Installation

### HACS (Recommended)

1. Add this repo as a custom repository in HACS
2. Search for "Surfcaster" in Integrations
3. Install and restart Home Assistant

### Manual

```bash
cd /path/to/your/config
git clone https://github.com/linusfr/ha-surfcaster.git custom_components/surfcaster
```

Then restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "Surfcaster"
3. Select which spots to monitor (all defaults are pre-selected)
4. Sensors appear — one entity per metric per spot

Update interval: **30 minutes**. Open-Meteo updates its marine model every 6 hours,
so this is plenty.

### Recorder

The forecast series sensors carry large attribute payloads (168 hourly data points).
Exclude them from the recorder to keep your database lean:

```yaml
# configuration.yaml
recorder:
  exclude:
    entity_globs:
      - sensor.*_forecast
```

## Automation Ideas

```yaml
# Notify when Pipeline breaks overhead
alias: "Pipeline is firing"
trigger:
  - trigger: numeric_state
    entity_id: sensor.pipeline_wave_height
    above: 2.5
action:
  - action: notify.mobile_app_your_phone
    data:
      title: "Pipeline is pumping!"
      message: "Wave height: {{ states('sensor.pipeline_wave_height') }}m. Paddle out."
```

```yaml
# Offshore wind = glassy conditions
alias: "Offshore alert"
trigger:
  - trigger: state
    entity_id: sensor.pipeline_wave_height
    to: null
condition:
  - condition: template
    value_template: >
      {{ states('sensor.pipeline_wind_speed') | float(0) < 15
         and states('sensor.pipeline_wave_height') | float(0) > 0.6 }}
action:
  - action: light.turn_on
    target:
      entity_id: light.surf_lamp
    data:
      color_name: green
```

## Dashboard

Surfcaster **auto-creates** a forecast dashboard when the integration is first
set up. The dashboard appears in your sidebar as "Surf Forecast" with two views
(North Sea / Baltic Sea), each showing one apexcharts card per spot with wave
height (filled area), wave period (line), and wind speed (line) over a 7-day
3-hourly forecast.

### Prerequisites

Install [apexcharts-card](https://github.com/RomRider/apexcharts-card) from
HACS **before** adding the Surfcaster integration, or the cards will show as
"custom element not found" until you install it and refresh.

```
HACS → Frontend → apexcharts-card
```

### Rebuilding

If you change your spot selection later, call the service
`surfcaster.create_dashboard` (Developer Tools → Services) to rebuild the
dashboard with the updated spot list.

## Blueprint

**Surf Weekend Alert** — checks all your spots Friday morning and notifies if any are firing.

1. Settings → Automations & Scenes → Blueprints → Surf Weekend Check
2. Pick your Surfcaster wave height sensors, set thresholds, pick notification target
3. Done — no YAML needed

Or use this automation with your YAML sensors:

```yaml
# Friday 08:00 — notify if any spot has surfable waves -->
<!-- this is in the blueprint link -->
```

[Open blueprint](blueprints/automation/surfcaster-surf-weekend-check.yaml)

## Development

```bash
# Requires: hermit (auto-bootstrapped), just

just              # list commands
just lint         # ruff check
just format       # ruff format
just ci           # full lint + format-check + yaml-lint
just test         # run pytest
just hooks-install  # install git hooks
```

Hermit pins dev tools (python, ruff, gitleaks, prek) to this repo. Activate with
`source bin/activate-hermit` or let `just` handle it.

## Architecture

```
custom_components/surfcaster/
├── __init__.py      # Integration setup/unload
├── manifest.json    # HA integration metadata
├── const.py         # Constants, default spots, sensor attributes
├── config_flow.py   # UI config flow (select spots)
├── coordinator.py   # DataUpdateCoordinator — polls Open-Meteo every 30min
└── sensor.py        # Sensor platform — per-spot sensors + forecast series
blueprints/
└── automation/surfcaster-surf-weekend-check.yaml
surfcaster-card.js   # Legacy custom card (prefer apexcharts)
```

Each spot gets:
- **8 current-condition sensors** (wave height/period/direction/max, wind speed/direction/max)
- **21 daily-max forecast sensors** (wave height/period/wind × 7 days)
- **1 forecast series sensor** (`sensor.<spot>_forecast`) with the full 7-day hourly time series as an attribute — built for apexcharts `data_generator`

A single `DataUpdateCoordinator` fetches both Open-Meteo Marine and Weather APIs
concurrently for all spots. The blueprint ships a pre-built weekend-check automation.

## License

MIT. Go surf.
