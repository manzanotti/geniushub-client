"""
Tests for the GeniusDevice class
"""

import unittest
from unittest.mock import Mock

from geniushubclient.device import GeniusDevice


class GeniusDeviceDataTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class, v3 data conversion.
    """

    _device_id = "27"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "hash": {"val": "0x0000000200040005"},
            "location": {"val": "Kitchen"},
            "Battery": {"val": 85},
            "TEMPERATURE": {"val": 21.5},
            "HEATING_1": {"val": 20.0},
            "lastComms": {"val": 1677000000},
            "setback": {"val": -0.5},
            "WakeUp_Interval": {"val": 300},
            "ApplicationVersion": {"val": "4.51"},
            "ProtocolVersion": {"val": "6.17"},
            "LibraryType": {"val": "6"},
            "health": {"val": 100},
            "manfID": {"val": "2"},
            "WakeUp_TargetNode": {"val": 1},
            "ProtectionState": {"val": 0},
            "ClockHour": {"val": 14},
            "ClockMinute": {"val": 30},
            "ClockWeekday": {"val": 3},
        },
        "childNodes": {
            "_cfg": {
                "childValues": {
                    "sku": {"val": "DA-WRV-B"},
                    "max_sp": {"val": 30.0},
                    "min_sp": {"val": 5.0},
                }
            }
        },
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_id_is_set_correctly(self):
        "Check that the id is set on the data object"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["id"], self._device_id)

    def test_type_is_set_from_hash(self):
        "Check that the device type is determined from the hash"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["type"], "Radiator Valve")

    def test_type_property(self):
        "Check that the type property returns the device type"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.type, "Radiator Valve")

    def test_assigned_zone_name(self):
        "Check that the assigned zone name is set from location"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["assignedZones"], [{"name": "Kitchen"}])

    def test_location_property(self):
        "Check that the location property returns the zone name"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.location, "Kitchen")

    def test_state_battery_level(self):
        "Check that battery level is set in state"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["state"]["batteryLevel"], 85)

    def test_battery_level_property(self):
        "Check that the battery_level property returns the battery level"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.battery_level, 85)

    def test_state_measured_temperature(self):
        "Check that measured temperature is set in state"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["state"]["measuredTemperature"], 21.5)

    def test_measured_temperature_property(self):
        "Check that the measured_temperature property returns the temperature"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.measured_temperature, 21.5)

    def test_state_set_temperature(self):
        "Check that set temperature is set in state"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["state"]["setTemperature"], 20.0)

    def test_setpoint_property(self):
        "Check that the setpoint property returns the set temperature"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.setpoint, 20.0)


class GeniusDeviceStateTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class, _state data.
    """

    _device_id = "27"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "hash": {"val": "0x0000000200040005"},
            "location": {"val": "Kitchen"},
            "Battery": {"val": 85},
            "TEMPERATURE": {"val": 21.5},
            "lastComms": {"val": 1677000000},
            "setback": {"val": -0.5},
            "WakeUp_Interval": {"val": 300},
        },
        "childNodes": {
            "_cfg": {
                "childValues": {
                    "sku": {"val": "DA-WRV-B"},
                    "max_sp": {"val": 30.0},
                    "min_sp": {"val": 5.0},
                }
            }
        },
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_last_comms_is_set(self):
        "Check that lastComms is set in _state"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_state"]["lastComms"], 1677000000)

    def test_last_communication_property(self):
        "Check that the last_communication property returns the timestamp"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.last_communication, 1677000000)

    def test_setback_is_set(self):
        "Check that setback is set in _state"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_state"]["setback"], -0.5)

    def test_valve_offset_property(self):
        "Check that the valve_offset property returns the setback value"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.valve_offset, -0.5)

    def test_wakeup_interval_is_set(self):
        "Check that wakeupInterval is set in _state"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_state"]["wakeupInterval"], 300)

    def test_wakeup_interval_property(self):
        "Check that the wakeup_interval property returns the interval"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.wakeup_interval, 300)


class GeniusDeviceConfigTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class, _config data.
    """

    _device_id = "27"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "hash": {"val": "0x0000000200040005"},
            "location": {"val": "Kitchen"},
        },
        "childNodes": {
            "_cfg": {
                "childValues": {
                    "sku": {"val": "DA-WRV-B"},
                    "max_sp": {"val": 30.0},
                    "min_sp": {"val": 5.0},
                }
            }
        },
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_config_sku_is_set(self):
        "Check that SKU is set in _config"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_config"]["sku"], "DA-WRV-B")

    def test_config_max_sp_is_set(self):
        "Check that max_sp is set in _config"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_config"]["max_sp"], 30.0)

    def test_config_min_sp_is_set(self):
        "Check that min_sp is set in _config"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_config"]["min_sp"], 5.0)


class GeniusDeviceDiagnosticsTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class, _diagnostics data.
    """

    _device_id = "27"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "hash": {"val": "0x0000000200040005"},
            "location": {"val": "Kitchen"},
            "ApplicationVersion": {"val": "4.51"},
            "ProtocolVersion": {"val": "6.17"},
            "LibraryType": {"val": "6"},
            "health": {"val": 100},
            "manfID": {"val": "2"},
            "WakeUp_TargetNode": {"val": 1},
            "ProtectionState": {"val": 0},
            "ClockHour": {"val": 14},
            "ClockMinute": {"val": 30},
            "ClockWeekday": {"val": 3},
        },
        "childNodes": {"_cfg": {"childValues": {}}},
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_diagnostics_sku_from_hash(self):
        "Check that SKU is derived from device hash"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["sku"], "DA-WRV-B")

    def test_device_model_property(self):
        "Check that the device_model property returns the SKU"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.device_model, "DA-WRV-B")

    def test_diagnostics_hash_is_set(self):
        "Check that the raw hash is stored in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["hash"], "0x0000000200040005")

    def test_diagnostics_application_version(self):
        "Check that ApplicationVersion is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["ApplicationVersion"], "4.51")

    def test_application_version_property(self):
        "Check that the application_version property returns the version"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.application_version, "4.51")

    def test_diagnostics_protocol_version(self):
        "Check that ProtocolVersion is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["ProtocolVersion"], "6.17")

    def test_protocol_version_property(self):
        "Check that the protocol_version property returns the version"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.protocol_version, "6.17")

    def test_diagnostics_library_type(self):
        "Check that LibraryType is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["LibraryType"], "6")

    def test_diagnostics_health(self):
        "Check that health is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["health"], 100)

    def test_diagnostics_manufacturer_id(self):
        "Check that manfID is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["manfID"], "2")

    def test_diagnostics_wakeup_target_node(self):
        "Check that wakeupTargetNode is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["wakeupTargetNode"], 1)

    def test_diagnostics_protection_state(self):
        "Check that protectionState is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["protectionState"], 0)

    def test_diagnostics_clock_time(self):
        "Check that clockTime is set in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(
            device.data["_diagnostics"]["clockTime"],
            {"hour": 14, "minute": 30, "weekday": 3},
        )


class GeniusDeviceMinimalDataTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class with minimal v3 data.
    Ensures missing optional fields are handled gracefully.
    """

    _device_id = "5"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "location": {"val": ""},
        },
        "childNodes": {"_cfg": {"childValues": {}}},
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_type_is_none_when_no_hash(self):
        "Check that type is None when hash is not present"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.data["type"])

    def test_empty_location_sets_no_zone(self):
        "Check that empty location results in no assigned zone name"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["assignedZones"], [{"name": None}])

    def test_battery_level_none_when_missing(self):
        "Check that battery_level is None when Battery is not in data"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.battery_level)

    def test_measured_temperature_none_when_missing(self):
        "Check that measured_temperature is None when TEMPERATURE is not in data"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.measured_temperature)

    def test_setpoint_none_when_missing(self):
        "Check that setpoint is None when HEATING_1 is not in data"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.setpoint)

    def test_last_communication_none_when_missing(self):
        "Check that last_communication is None when lastComms is not in data"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.last_communication)

    def test_valve_offset_none_when_missing(self):
        "Check that valve_offset is None when setback is not in data"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.valve_offset)

    def test_wakeup_interval_none_when_missing(self):
        "Check that wakeup_interval is None when WakeUp_Interval is not in data"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.wakeup_interval)

    def test_protocol_version_none_when_missing(self):
        "Check that protocol_version is None when not in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.protocol_version)

    def test_application_version_none_when_missing(self):
        "Check that application_version is None when not in diagnostics"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.application_version)

    def test_device_model_none_when_no_hash(self):
        "Check that device_model is None when hash is not present"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.device_model)

    def test_location_none_when_empty(self):
        "Check that location is None when location value is empty"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.location)


class GeniusDeviceClockWithoutWeekdayTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class when clock data has no weekday.
    """

    _device_id = "15"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "location": {"val": "Hallway"},
            "ClockHour": {"val": 9},
            "ClockMinute": {"val": 45},
        },
        "childNodes": {"_cfg": {"childValues": {}}},
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_clock_time_without_weekday(self):
        "Check that clockTime is set without weekday when ClockWeekday is missing"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(
            device.data["_diagnostics"]["clockTime"],
            {"hour": 9, "minute": 45},
        )


class GeniusDeviceUnknownHashTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class when the hash is not in SKU_BY_HASH.
    """

    _device_id = "99"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "hash": {"val": "0xFFFFFFFFFFFFFFFF"},
            "location": {"val": "Unknown Room"},
        },
        "childNodes": {"_cfg": {"childValues": {}}},
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_type_not_set_for_unknown_hash(self):
        "Check that type key is not set when hash is not recognized"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertNotIn("type", device.data)

    def test_diagnostics_hash_still_stored(self):
        "Check that the raw hash is stored even when unrecognized"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["_diagnostics"]["hash"], "0xFFFFFFFFFFFFFFFF")

    def test_device_model_none_for_unknown_hash(self):
        "Check that device_model is None when hash is not in SKU_BY_HASH"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIsNone(device.device_model)


class GeniusDeviceSwitchBinaryTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class with a switch binary device (e.g., smart plug).
    """

    _device_id = "8"

    raw_json = {
        "addr": _device_id,
        "childValues": {
            "location": {"val": "Office"},
            "SwitchBinary": {"val": 1, "path": "nodes/8/1/37"},
        },
        "childNodes": {"_cfg": {"childValues": {}}},
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_switch_binary_output_is_bool(self):
        "Check that outputOnOff is converted to a boolean"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertIs(device.data["state"]["outputOnOff"], True)

    def test_dual_channel_receiver_type_detection(self):
        "Check that dual channel receiver type is detected from path depth"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data["type"], "Dual Channel Receiver - Channel 8")


class GeniusDeviceV1ApiTests(unittest.TestCase):
    """
    Tests for the GeniusDevice class with v1 API data (passthrough).
    """

    _device_id = "27"

    raw_json = {
        "id": _device_id,
        "type": "Radiator Valve",
        "assignedZones": [{"name": "Kitchen"}],
        "state": {"batteryLevel": 85, "measuredTemperature": 21.5},
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 1
        self.hub = hub

    def test_v1_data_is_passed_through(self):
        "Check that v1 API data is returned as-is"

        device = GeniusDevice(self._device_id, self.raw_json, self.hub)
        self.assertEqual(device.data, self.raw_json)
