"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.const import IMODE_TO_MODE, ZONE_MODE, ZONE_TYPE
from geniushubclient.zone import GeniusZone


class GeniusZoneDataStateTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, state data.
        """

    _device_id = "Device Id"
    _zone_name = "Zone Name"

    raw_json = {
        "iID": _device_id,
        "strName": _zone_name,
        "bIsActive": 0,
        "bInHeatEnabled": 0,
        "bOutRequestHeat": 0,
        "fBoostSP": 0,
        "fPV": 21.0,
        "fPV_offset": 0.0,
        "fSP": 14.0,
        "iBoostTimeRemaining": 0,
        "iFlagExpectedKit": 517,
        "iType": ZONE_TYPE.OnOffTimer,
        "iMode": ZONE_MODE.Off,
        "objFootprint": {
            "bIsNight": 0,
            "fFootprintAwaySP": 14.0,
            "iFootprintTmNightStart": 75600,
            "iProfile": 1,
            "lstSP": [{
                "fSP": 16.0,
                "iDay": 0,
                "iTm": 0
            }, {
                "fSP": 14.0,
                "iDay": 0,
                "iTm": 23400
            }, {
                "fSP": 20.0,
                "iDay": 0,
                "iTm": 59700
            }, {
                "fSP": 14.0,
                "iDay": 0,
                "iTm": 75000
            }, {
                "fSP": 16.0,
                "iDay": 0,
                "iTm": 75600
            }
            ],
            "objReactive": {
                "fActivityLevel": 0.0
            }
        },
        "objTimer": [{
            "fSP": 14.0,
            "iDay": 0,
            "iTm": -1
        }],
        "trigger": {
            "reactive": 0,
            "output": 0
        },
        "warmupDuration": {
            "bEnable": "true",
            "bEnableCalcs": "true",
            "fRiseRate": 0.5,
            "iLagTime": 2420,
            "iRiseTime": 300,
            "iTotalTime": 2720
        },
        "zoneReactive": {
            "fActivityLevel": 0
        },
        "zoneSubType": 1
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_when_bIsActive_is_false_then_state_bIsActive_false(self):
        "Check that the bIsActive is correctly set to false"

        self.raw_json["bIsActive"] = 0

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.data["_state"]["bIsActive"])

    def test_when_bIsActive_is_true_then_state_bIsActive_true(self):
        "Check that the bIsActive is correctly set to true"

        self.raw_json["bIsActive"] = 1

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertTrue(genius_zone.data["_state"]["bIsActive"])

    def test_when_bOutRequestHeat_is_false_then_output_false(self):
        "Check that the output is correctly set to false"

        self.raw_json["bOutRequestHeat"] = 0

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["output"], 0)

    def test_when_bOutRequestHeat_is_true_then_output_true(self):
        "Check that the output is correctly set to true"

        self.raw_json["bOutRequestHeat"] = 1

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertEqual(genius_zone.data["output"], 1)

    def test_when_iMode_set_then_state_mode_is_set_correctly(self):
        "Check that the mode is set on the class"

        for zone_mode, zone_mode_text in IMODE_TO_MODE.items():
            with self.subTest(zone_mode=zone_mode, zone_mode_text=zone_mode_text):
                self.raw_json["iMode"] = zone_mode
                self.raw_json["zoneSubType"] = 1

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertEqual(genius_zone.data["mode"], zone_mode_text)

    def test_when_iType_should_set_temperature_state_temperature_set_correctly(self):
        "Check that the temperature is set for certain values of iType"

        temperature = 20.0
        self.raw_json["fPV"] = temperature

        test_values = (
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI,
            ZONE_TYPE.Manager
        )

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertEqual(genius_zone.data["temperature"], temperature)

    def test_when_iType_should_not_set_temperature_state_temperature_not_set(self):
        "Check that the temperature is not set for certain values of iType"

        self.raw_json["fPV"] = 20.0

        test_values = (
            ZONE_TYPE.OnOffTimer,
            ZONE_TYPE.ControlOnOffPID,
            ZONE_TYPE.Surrogate
        )

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertFalse("temperature" in genius_zone.data)

    def test_when_iType_should_set_setpoint_state_setpoint_set_correctly(self):
        "Check that the setpoint is set for certain values of iType"

        setpoint = 21.0
        self.raw_json["fSP"] = setpoint

        test_values = (
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI
        )

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertEqual(genius_zone.data["setpoint"], setpoint)

    def test_when_iType_should_not_set_setpoint_state_setpoint_not_set(self):
        "Check that the setpoint is not set for certain values of iType"

        self.raw_json["fSP"] = 21.0

        test_values = (
            ZONE_TYPE.Manager,
            ZONE_TYPE.ControlOnOffPID,
            ZONE_TYPE.Surrogate
        )

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertFalse("setpoint" in genius_zone.data)

    def test_when_iType_OnOffTimer_fSP_not_zero_setpoint_state_setpoint_set_true(self):
        """Check that the setpoint is set to true when iType is OnOffTimer

        and fSP is not zero"""

        self.raw_json["fSP"] = 1.0
        self.raw_json["iType"] = ZONE_TYPE.OnOffTimer

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertTrue(genius_zone.data["setpoint"])

    def test_when_iType_OnOffTimer_fSP_zero_setpoint_state_setpoint_set_false(self):
        """Check that the setpoint is set to false when iType is OnOffTimer

        and fSP is zero"""

        self.raw_json["fSP"] = 0.0
        self.raw_json["iType"] = ZONE_TYPE.OnOffTimer

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.data["setpoint"])
