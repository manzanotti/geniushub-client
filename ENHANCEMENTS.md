# Genius Hub Client - Enhanced Device Parsing

## Summary

Successfully extended the Genius Hub Python library to parse comprehensive device information from the v3 API's `/data_manager` endpoint.

## What Was Added

### 1. Additional Diagnostic Fields Extracted

The library now extracts these additional fields from devices:

- **sku**: Device model/SKU (e.g., "DA-WRV-B", "HO-WRT-B") - derived from device hash
- **hash**: Device hash identifier
- **ApplicationVersion**: Firmware application version
- **ProtocolVersion**: Z-Wave protocol version
- **LibraryType**: Device library type (e.g., "Controller", "Routing Slave", "Enhanced Slave")
- **health**: Device health status indicator
- **manfID**: Manufacturer ID
- **wakeupTargetNode**: Target node for wake-up commands
- **protectionState**: Protection state for radiator valves
- **clockTime**: Device clock information (hour, minute, weekday) for devices that have it

All these fields are now stored in `device.data["_diagnostics"]`.

### 2. Convenience Property Accessors

Added easy-to-use property accessors to the `GeniusDevice` class:

```python
device.battery_level          # Battery percentage (int or None)
device.last_communication     # Unix timestamp of last communication
device.measured_temperature   # Current measured temperature in °C
device.setpoint              # Target temperature in °C
device.valve_offset          # Valve hidden offset (setback) in °C
device.wakeup_interval       # Wake-up interval in seconds
device.protocol_version      # Protocol version string
device.application_version   # Application/firmware version string
device.device_model          # Device model/SKU (e.g., "DA-WRV-B")
device.location              # Device location/zone name
```

### 3. New Convenience Methods

Added to `GeniusHub` class:

```python
hub.get_devices()            # Returns list of GeniusDevice objects
hub.get_device(device_id)    # Returns specific GeniusDevice by ID
```

## Usage Examples

### Basic Usage

```python
import asyncio
import aiohttp
from geniushubclient import GeniusHub

async def main():
    async with aiohttp.ClientSession() as session:
        hub = GeniusHub(
            hub_id="192.168.20.3",
            username="your_username",
            password="your_password",
            session=session
        )

        await hub.update()

        # Get all devices
        devices = hub.get_devices()

        for device in devices:
            print(f"{device.id}: {device.type} in {device.location}")
            print(f"  Battery: {device.battery_level}%")
            print(f"  Last seen: {device.last_communication}")
            print(f"  Setpoint: {device.setpoint}°C")
            print(f"  Current temp: {device.measured_temperature}°C")
            print(f"  Valve offset: {device.valve_offset}°C")
            print(f"  Protocol: {device.protocol_version}")
            print(f"  Firmware: {device.application_version}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Get Specific Device

```python
# Get device by ID
device = hub.get_device("10")

if device:
    print(f"Device Type: {device.type}")
    print(f"Location: {device.location}")
    print(f"Battery: {device.battery_level}%")

    # Access full diagnostics
    if "_diagnostics" in device.data:
        print(f"Diagnostics: {device.data['_diagnostics']}")
```

### Home Assistant Integration

This enhanced device information is perfect for Home Assistant integration:

```python
# Battery sensor
battery_level = device.battery_level

# Last seen sensor
from datetime import datetime
last_seen = datetime.fromtimestamp(device.last_communication)

# Temperature sensors
current_temp = device.measured_temperature
target_temp = device.setpoint

# Device attributes
attributes = {
    "protocol_version": device.protocol_version,
    "app_version": device.application_version,
    "valve_offset": device.valve_offset,
    "wakeup_interval": device.wakeup_interval,
    "health": device.data.get("_diagnostics", {}).get("health"),
    "manufacturer": device.data.get("_diagnostics", {}).get("manfID"),
}
```

## Files Modified

1. **geniushubclient/device.py**
   - Enhanced device data extraction to include diagnostics
   - Added property accessors for common device attributes

2. **geniushubclient/__init__.py**
   - Added `get_devices()` method
   - Added `get_device(device_id)` method

## Backward Compatibility

All changes are fully backward compatible:

- Existing `device.data` structure remains unchanged
- New fields are added as optional (`_diagnostics` section)
- Existing code using `hub.devices`, `hub.device_by_id`, etc. continues to work
- New properties return `None` if data is not available

## Testing

Tested successfully with a real Genius Hub at 192.168.20.3:
- 10 devices detected (Room Thermostats, Radiator Valves, Smart Plugs)
- All diagnostic fields extracted correctly
- All property accessors working as expected
- Both `get_devices()` and `get_device()` methods functioning properly

## Test Scripts

- `test_data_manager.py` - Fetches and saves raw data for inspection
- `test_enhanced_devices.py` - Demonstrates all new functionality

## Notes

- **Device Neighbours**: Not available in the local v3 API. The Genius Hub app displays device neighbours (e.g., "1, 12, 14, 20") but this information is not exposed through any of the local v3 API endpoints (`/data_manager`, `/zones`, etc.). This data likely comes from the cloud API or requires Z-Wave mesh network scanning that's not available locally.
- Some devices may not have all fields (e.g., Smart Plugs don't have battery)
- All property accessors safely return `None` if the field is not available
- Device models (SKU) are derived from the device hash using the `SKU_BY_HASH` mapping in const.py
