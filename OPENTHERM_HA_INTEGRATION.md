# OpenTherm Home Assistant Integration - Implementation Notes

## Status: Waiting for geniushub-client PR #93 to be merged

**PR Link:** https://github.com/manzanotti/geniushub-client/pull/93

## What Was Accomplished

### 1. Python Package (geniushub-client)
- ✅ Added OpenTherm zone type (iType 7) to `const.py`
- ✅ Updated `zone.py` to handle OpenTherm zones (no objTimer)
- ✅ Exposed `_opentherm` field with 45+ boiler metrics
- ✅ Fixed `setup.py` to handle missing GITHUB_REF_NAME
- ✅ Created test script: `test_opentherm.py`
- ✅ Submitted PR #93 to upstream

**Branch:** `add-opentherm-support`
**Fork:** https://github.com/warksit/geniushub-client

### 2. Home Assistant Custom Integration
**Location on HA:** `/homeassistant/custom_components/geniushub/`

**Files Modified:**
- `manifest.json` - Points to dev branch (needs updating for PR)
- `sensor.py` - Added 9 OpenTherm sensors with device grouping
- `__init__.py` - Changed SCAN_INTERVAL from 60s to 10s (needs reverting or making configurable)

**OpenTherm Sensors Created:**
1. Boiler Flow Temperature (°C)
2. Boiler Return Temperature (°C)
3. Control Setpoint (°C)
4. Modulation Level (%)
5. Flame Status (on/off)
6. CH Pressure (bar)
7. DHW Temperature (°C)
8. Central Heating Active (on/off)
9. DHW Active (on/off)

**Device Info:**
- Name: "Ideal Vogue Max" (from zone name)
- Manufacturer: "Genius Hub"
- Model: "OpenTherm Bridge"
- All sensors properly grouped under device

### 3. Testing Environment
- **Hub IP:** 192.168.20.3
- **Hub UID:** 18:CC:23:00:73:76
- **OpenTherm Zone:** Zone 1 (iType: 7)
- **HA Version:** 2025.11.1

## Next Steps (After PR #93 Merges)

### Prepare Home Assistant PR

#### 1. Clean Up for PR Submission

**Revert scan interval change** (or make it configurable):
```bash
ssh hassio@192.168.10.3
# Edit /homeassistant/custom_components/geniushub/__init__.py
# Change: SCAN_INTERVAL = timedelta(seconds=10)
# Back to: SCAN_INTERVAL = timedelta(seconds=60)
```

**Update manifest.json:**
```json
{
  "domain": "geniushub",
  "name": "Genius Hub",
  "codeowners": ["@manzanotti"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/geniushub",
  "iot_class": "local_polling",
  "loggers": ["geniushubclient"],
  "requirements": ["geniushub-client>=0.8.0"],
  "version": "2024.11.0"
}
```

#### 2. Copy Files to HA Core Repo

Clone HA core and copy updated `sensor.py`:
```bash
cd ~/geniushub-debug
git clone https://github.com/home-assistant/core.git ha-core
cd ha-core
git checkout -b add-geniushub-opentherm

# Copy the modified sensor.py from custom_components
# (Will need to download from HA instance first)
```

#### 3. Create PR Description

**Title:** Add OpenTherm support to Genius Hub integration

**Description Template:**
```markdown
## Summary
Adds support for Genius Hub OpenTherm boiler controller modules (iType 7).

## Problem
Users with OpenTherm modules were experiencing `KeyError: 7` when the integration attempted to parse OpenTherm zones.

## Solution
- Added OpenTherm zone type support to sensor platform
- Created 9 new sensor entities for OpenTherm metrics:
  - Boiler flow/return temperatures
  - Modulation level
  - Flame status
  - CH pressure
  - DHW temperature
  - CH/DHW active status
- Implemented device registry support for OpenTherm sensors
- All OpenTherm sensors grouped under device (e.g., "Ideal Vogue Max")

## Dependencies
- Requires geniushub-client >= 0.8.0 (includes OpenTherm support)

## Testing
- Tested with Genius Hub v3 API
- OpenTherm module successfully detected and sensors created
- All sensor values updating correctly
- Device grouping working as expected

## Breaking Changes
None - only adds new functionality for OpenTherm users

## Checklist
- [ ] Updated requirements in manifest.json
- [ ] Added tests (if applicable)
- [ ] Updated documentation (if applicable)
```

## File Locations

### Current Working Files
- **Custom Integration:** `/homeassistant/custom_components/geniushub/` on HA instance (192.168.10.3)
- **Python Package:** `/Users/andrew/geniushub-debug/geniushub-client/`
- **Test Script:** `/Users/andrew/geniushub-debug/geniushub-client/test_opentherm.py`

### SSH Access
```bash
ssh hassio@192.168.10.3
# Custom integration: cd /homeassistant/custom_components/geniushub/
```

## sensor.py Implementation Notes

### Key Changes Made:
1. Added `DeviceInfo` import from `homeassistant.helpers.entity`
2. Added `OPENTHERM_SENSORS` dictionary mapping field names to sensor configs
3. Created `GeniusOpenThermSensor` class with:
   - Proper unique_id using `self._unique_id`
   - Device info using `DeviceInfo()` constructor
   - Handles boolean → "on"/"off" conversion
   - Filters invalid temperature readings (-40.0)
4. Modified `async_setup_entry` to create OpenTherm sensors for zones with `type == "opentherm"`

### Important Implementation Details:
- Uses `self._unique_id` (not `self._attr_unique_id`) for compatibility with base `GeniusEntity` class
- Device identifiers: `("geniushub", f"zone_{zone.id}")`
- Sensors only created if field exists in `_opentherm.childValues`

## Issues to Consider for PR

### 1. Scan Interval
**Current:** Changed globally from 60s → 10s
**For PR:** Should either:
- Revert to 60s (conservative)
- Make configurable via integration options
- Document that OpenTherm users may want faster polling

### 2. Additional OpenTherm Fields
Currently exposing 9 key fields. Full list of 45+ available fields in `_opentherm.childValues`:
- Consider adding more sensors (exhaust_temp, room_temp, etc.)
- Or document how users can access via attributes

### 3. Device Registry for Other Zones
Currently only OpenTherm zones have device registry support.
**Future PR:** Modernize entire integration with devices for:
- Radiator zones
- Room sensors
- Valves
- Main hub device

## Contact Info
- **GitHub:** warksit
- **Python Package Fork:** https://github.com/warksit/geniushub-client
- **Branch:** add-opentherm-support
- **PR:** https://github.com/manzanotti/geniushub-client/pull/93

## Quick Reference Commands

### Check PR Status
```bash
gh pr view 93 --repo manzanotti/geniushub-client
```

### Download Current sensor.py from HA
```bash
scp hassio@192.168.10.3:/homeassistant/custom_components/geniushub/sensor.py ~/geniushub-debug/sensor_opentherm.py
```

### Test with Local Package
```bash
cd ~/geniushub-debug/geniushub-client
GITHUB_REF_NAME="0.0.0-dev" pip install -e .
python test_opentherm.py
```

## Timeline
- **2025-11-14:** Implementation completed, PR #93 submitted
- **Next:** Wait for PR #93 review/merge
- **Then:** Submit HA integration PR

---

**Note:** Keep this file updated as PR progresses. This document should contain everything needed to pick up where we left off.
