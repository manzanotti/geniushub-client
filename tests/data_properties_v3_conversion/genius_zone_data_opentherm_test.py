"""
Tests for the GeniusZone class - OpenTherm zone type (iType 7)
"""

import unittest
from unittest.mock import Mock

from geniushubclient.zone import GeniusZone


class GeniusZoneDataOpenThermTests(unittest.TestCase):
    """
    Test for the GeniusZone Class, OpenTherm zone data.
    """

    _zone_id = 1
    _zone_name = "OpenTherm Zone"

    # Raw v3 API JSON for an OpenTherm zone (iType 7)
    # Captured from a real Genius Hub with OpenTherm module
    raw_json = {
        "bIsActive": True,
        "bOutRequestHeat": True,
        "bOverrideLimitingAllowed": False,
        "bPrimaryZone": True,
        "fOutput": 55.0,
        "fPV": 43.19921875,
        "fSP": 55.0,
        "iBaseMode": 128,
        "iBoostTimeRemaining": 0,
        "iFlagActualKit": 0,
        "iFlagExpectedKit": 0,
        "iFlags": 256,
        "iID": 1,
        "iMode": 128,
        "iOverrideDuration": 3600,
        "iOverrideMode": 0,
        "iPriority": 7,
        "iType": 7,
        "lOptions": 0,
        "linkedSettings": {
            "bFollowActive": False,
            "bFollowOutput": True,
            "fLinkSP": 21.0,
            "lstLinkedTo": [4, 6, 7, 12, 13],
        },
        "log": [],
        "lstIssues": [],
        "maxError": 0.0,
        "maxPV": 0.0,
        "maxSP": 0.0,
        "maximumOverrideDuration": 86400,
        "meanError": 0.0,
        "opentherm": {
            "addr": "opentherm",
            "childValues": {
                "CH_active": {
                    "addr": "CH_active",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": True,
                },
                "CH_enable": {
                    "addr": "CH_enable",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": True,
                },
                "DHW_active": {
                    "addr": "DHW_active",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": False,
                },
                "DHW_enable": {
                    "addr": "DHW_enable",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": False,
                },
                "boiler_water_temp": {
                    "addr": "boiler_water_temp",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": 43.19921875,
                },
                "ch_pressure": {
                    "addr": "ch_pressure",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": 1.0,
                },
                "ch_max_sp": {
                    "addr": "ch_max_sp",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": 80.0,
                },
                "control_sp": {
                    "addr": "control_sp",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": 55.0,
                },
                "dhw_temp": {
                    "addr": "dhw_temp",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": -40.0,
                },
                "flame_status": {
                    "addr": "flame_status",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": False,
                },
                "modulation_level": {
                    "addr": "modulation_level",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": 0.0,
                },
                "return_temp": {
                    "addr": "return_temp",
                    "path": "site/opentherm",
                    "type": "Float",
                    "val": 43.19921875,
                },
                "fault_present": {
                    "addr": "fault_present",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": False,
                },
                "comms_status_opentherm": {
                    "addr": "comms_status_opentherm",
                    "path": "site/opentherm",
                    "type": "Bool",
                    "val": True,
                },
            },
            "type": "",
        },
        "strName": "OpenTherm Zone",
        "trigger": {
            "boost": 0,
            "linkChildActive": 0,
            "linkChildOutput": 0,
            "output": 1,
            "preheat": 0,
            "reactive": 0,
            "setpoint": 0,
            "test": 0,
        },
        "zoneSubType": 0,
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_opentherm_zone_type_is_set_correctly(self):
        "Check that OpenTherm zone type is correctly identified"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["type"], "opentherm")

    def test_opentherm_zone_temperature_is_set_from_fPV(self):
        "Check that temperature is set from fPV (boiler flow temp)"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["temperature"], 43.19921875)

    def test_opentherm_zone_setpoint_is_set_from_fSP(self):
        "Check that setpoint is set from fSP (control setpoint)"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["setpoint"], 55.0)

    def test_opentherm_data_is_exposed(self):
        "Check that opentherm data is exposed in zone data"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertIn("opentherm", genius_zone.data)

    def test_opentherm_child_values_accessible(self):
        "Check that opentherm childValues are accessible"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        opentherm = genius_zone.data["opentherm"]
        self.assertIn("childValues", opentherm)
        self.assertIn("flame_status", opentherm["childValues"])
        self.assertIn("boiler_water_temp", opentherm["childValues"])

    def test_opentherm_boiler_water_temp_value(self):
        "Check that boiler water temperature value is correct"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        opentherm = genius_zone.data["opentherm"]
        boiler_temp = opentherm["childValues"]["boiler_water_temp"]["val"]
        self.assertEqual(boiler_temp, 43.19921875)

    def test_opentherm_flame_status_value(self):
        "Check that flame status value is correct"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        opentherm = genius_zone.data["opentherm"]
        flame_status = opentherm["childValues"]["flame_status"]["val"]
        self.assertFalse(flame_status)

    def test_opentherm_ch_active_value(self):
        "Check that CH active value is correct"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        opentherm = genius_zone.data["opentherm"]
        ch_active = opentherm["childValues"]["CH_active"]["val"]
        self.assertTrue(ch_active)

    def test_opentherm_zone_without_opentherm_data(self):
        "Check that zone without opentherm data doesn't have opentherm field"

        raw_json_no_opentherm = self.raw_json.copy()
        del raw_json_no_opentherm["opentherm"]

        genius_zone = GeniusZone(self._zone_id, raw_json_no_opentherm, self.hub)

        self.assertNotIn("opentherm", genius_zone.data)

    def test_opentherm_zone_has_no_timer_schedule(self):
        "Check that OpenTherm zones don't generate timer schedules"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["schedule"]["timer"], {})

    def test_opentherm_zone_output_is_set(self):
        "Check that output is set from bOutRequestHeat"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["output"], 1)

    def test_opentherm_zone_id_is_set(self):
        "Check that zone id is set correctly"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["id"], 1)

    def test_opentherm_zone_name_is_set(self):
        "Check that zone name is set correctly"

        genius_zone = GeniusZone(self._zone_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["name"], "OpenTherm Zone")


if __name__ == "__main__":
    unittest.main()
