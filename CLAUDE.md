# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **geniushubclient_enhanced**, a Python library providing async access to Genius Hub home heating systems via their RESTful API. It's a fork of the original `geniushub-client` with enhanced device diagnostics and OpenTherm support.

**Key Context:**
- Package name changed from `geniushubclient` to `geniushubclient_enhanced` to avoid conflicts with the core Home Assistant integration
- This library is used by a Home Assistant custom integration at `/config/custom_components/geniushub_enhanced/` (on HA instance)
- Local copy of the HA integration source: `/Users/andrew/code/homeassistant/geniushub/`
- Supports two API modes: v1 (cloud, token-based) and v3 (local hub, username/password)

## Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .
```

## Testing

### Run Unit Tests
```bash
# Run all tests
python -m unittest discover -p "*_test.py"

# Tests follow Arrange/Act/Assert pattern
# See tests/README.md for detailed testing conventions
```

### Ad-hoc Testing with ghclient.py
```bash
# Using hub token (v1 API, cloud)
python ghclient.py ${HUB_TOKEN} zones

# Using local hub (v3 API, direct)
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} devices -v

# Raw v3 API responses (not converted to v1 schema)
python ghclient.py ${HUB_ADDRESS} -u ${USERNAME} -p ${PASSWORD} zones -vvv
```

### Ad-hoc Test Scripts
- `test_enhanced_devices.py` - Test enhanced device properties (battery, humidity, etc.)
- `test_data_manager.py` - Dump raw device data for inspection

## Architecture

### Core Classes

**GeniusHub** (`__init__.py`)
- Main entry point and coordinator
- Manages zones, devices, and issues
- Handles API v1 ↔ v3 conversion
- Key methods: `update()`, `get_devices()`, `get_device(device_id)`

**GeniusZone** (`zone.py`)
- Represents heating zones (radiators, on/off, OpenTherm boilers)
- Converts v3 zone data to v1 schema
- Handles special case: OpenTherm zones (iType 7) have no `objTimer`
- Key property: `data` - converted zone data

**GeniusDevice** (`device.py`)
- Represents physical devices (TRVs, thermostats, smart plugs)
- Enhanced properties: `battery_level`, `humidity`, `measured_temperature`, `setpoint`, `valve_offset`, `last_communication`, `protocol_version`, `application_version`, `device_model`
- Extracts diagnostics from v3 `/data_manager` endpoint

**GeniusService** (`session.py`)
- HTTP client wrapper using aiohttp
- Handles v1 (cloud) and v3 (local) endpoints

### Data Flow

```
v3 API Raw JSON → GeniusHub.update()
                     ↓
                  _zones_via_v3_zones()      → GeniusZone objects
                  _devices_via_v3_data_mgr() → GeniusDevice objects
                  _issues_via_v3_zones()     → GeniusIssue objects
                     ↓
                  Convert to v1 schema (where possible)
                     ↓
                  Expose via .data property
```

### Important Constants (`const.py`)

- `ZONE_TYPE` - Zone type enum (OnOffTimer, ControlSP, TPI, Surrogate, Manager, TPI+, OpenTherm)
- `ITYPE_TO_TYPE` - Maps numeric iType (0-7) to zone type names
- `SKU_BY_HASH` - Maps device hash to model SKU (e.g., "GH-WRT-A", "DA-WRV-B")
- `DEVICE_HASH_TO_TYPE` - Maps device hash to device type
- `STATE_ATTRS` - Device state attribute mappings for v3 → v1 conversion

## Home Assistant Integration Deployment

The custom HA integration lives on the HA instance at `/config/custom_components/geniushub_enhanced/`.

### Deploy Changes to HA
```bash
# Files are deployed via SSH to <SSH_USER>@<HA_HOST>
# Use cat piping (scp doesn't work on this system):

cat local_file.py | ssh <SSH_USER>@<HA_HOST> "cat > /config/custom_components/geniushub_enhanced/file.py"

# Restart Home Assistant via API
curl -X POST \
  -H "Authorization: Bearer $(cat <TOKEN_PATH>)" \
  -H "Content-Type: application/json" \
  http://<HA_HOST>:8123/api/services/homeassistant/restart
```

### HA Integration Files
- `__init__.py` - Entry point, device registry creation, service setup
- `sensor.py` - Battery, OpenTherm, diagnostic, humidity sensors
- `climate.py` - Heating zone climate entities
- `switch.py` - Smart plug switch entities
- `water_heater.py` - Hot water control
- `entity.py` - Base classes (GeniusEntity, GeniusDevice, GeniusZone, GeniusHeatingZone)
- `const.py` - **Single line to change for core PR**: `DOMAIN = "geniushub_enhanced"` → `DOMAIN = "geniushub"`
- `manifest.json` - Integration metadata, requires `geniushubclient_enhanced @ git+...@v0.8.4`

## Key Enhancements

### 1. Device Diagnostics (ENHANCEMENTS.md)
Added comprehensive device properties:
- Battery level, last communication timestamp
- Measured temperature, setpoint, valve offset
- Protocol version, application version, device model
- Health status, manufacturer ID, wakeup interval

All stored in `device.data["_diagnostics"]` with convenience property accessors.

### 2. OpenTherm Support (OPENTHERM_HA_INTEGRATION.md)
- Added iType 7 (OpenTherm) zone type
- Exposes `opentherm` field with 45+ boiler metrics
- HA integration creates 9 sensors: flow/return temps, modulation, flame status, CH pressure, DHW temp, CH/DHW active
- Zone parsing handles missing `objTimer` for OpenTherm zones

### 3. Humidity Support
- Added `humidity` property to GeniusDevice
- Reads from `device.data["state"].get("humidity")`
- Device model mapping via `SKU_BY_HASH` (e.g., Device 20 = "GH-WRT-A" thermostat)

## Package Naming Context

**Why "geniushubclient_enhanced"?**
- Home Assistant core integration requires `geniushub-client==0.7.1` from PyPI
- Python normalizes `geniushub-client` and `geniushubclient` as the same package
- Custom integration using git+url would be ignored (already satisfied by core's 0.7.1)
- Renaming package breaks the conflict completely
- Custom integration uses different domain (`geniushub_enhanced`) to prevent core from loading

## Important Implementation Notes

### Device Identifiers in HA
All device identifiers use `DOMAIN` constant from `const.py`:
```python
# Hub device
(DOMAIN, f"hub_{unique_id}")

# Physical devices
(DOMAIN, f"device_{device.id}")

# OpenTherm zone devices
(DOMAIN, f"zone_{zone.id}")
```

### Entity Naming Pattern
- Entity name = descriptive label only (e.g., "Battery", "Temperature")
- Device name = full context (e.g., "Kitchen TRV (10)")
- Unique ID = `{hub_uid}_device_{device_id}_{sensor_type}`

### OpenTherm Sensor Configuration
Defined in `sensor.py` as `OPENTHERM_SENSORS` dict:
```python
{
    "field_key": {
        "name": "Display Name",
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:icon-name",
        "precision": 0  # Optional, for temperature rounding
    }
}
```

### Z-Wave Limitations
- Device IDs change when TRVs are removed and re-paired
- Z-Wave devices don't expose persistent unique identifiers
- This is a Genius Hub/Z-Wave protocol limitation, not fixable in software

## API v1 vs v3

**v1 API (Cloud)**
- Token-based: `https://my.geniushub.co.uk/v1/*`
- Well-documented, stable
- Slower (round-trip to Heat Genius servers)

**v3 API (Local)**
- Username/password to local hub: `http://{hub_ip}:1223/v3/*`
- Undocumented, reverse-engineered from web app
- Faster (direct hub access)
- Library converts v3 → v1 schema for compatibility
- Endpoints: `/v3/zones`, `/v3/data_manager`

## Open Pull Requests (Upstream)

### PR #93: Add support for OpenTherm zone type (iType 7) - MERGED
- Merged into upstream v0.7.3 (2026-02-14)
- URL: https://github.com/manzanotti/geniushub-client/pull/93
- Note: field renamed from `_opentherm` to `opentherm` during review

### PR #94: Add enhanced device parsing from v3 API - OPEN
- Branch: `enhanced-device-parsing` (rebased onto v0.7.3)
- Adds device diagnostics via `/data_manager` endpoint
- URL: https://github.com/manzanotti/geniushub-client/pull/94

To rebase again if needed:
```bash
git fetch upstream
git checkout <branch-name>
git rebase upstream/main
git push origin <branch-name> --force
```

## Git Tagging

Version tags follow semantic versioning (e.g., `v0.8.4`):
```bash
git tag v0.8.4
git push origin v0.8.4
```

Manifest references specific tag:
```json
"requirements": ["geniushubclient_enhanced @ git+https://github.com/warksit/geniushub-client.git@v0.8.4"]
```

## Version Management

`setup.py` contains hardcoded version (not dynamic):
```python
VERSION = "0.8.4"
```

Update this manually when creating releases. The GITHUB_REF_NAME environment variable approach was removed to avoid CI issues.
