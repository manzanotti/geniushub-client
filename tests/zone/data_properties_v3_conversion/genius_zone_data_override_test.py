"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.const import ZONE_MODE, ZONE_TYPE
from geniushubclient.zone import GeniusZone


class GeniusZoneDataOverrideTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, override data.
        """

    _device_id = "Device Id"
    _zone_name = "Zone Name"
    _override_duration = 100
    _override_setpoint = 21.0

    raw_json = {
        "iID": _device_id,
        "strName": _zone_name,
        "bIsActive": 0,
        "bInHeatEnabled": 0,
        "bOutRequestHeat": 0,
        "fBoostSP": _override_setpoint,
        "fPV": 21.0,
        "fPV_offset": 0.0,
        "fSP": 14.0,
        "iBoostTimeRemaining": _override_duration,
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
            "fActivityLevel": 0.0
        },
        "zoneSubType": 1
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_when_override_not_applicable_for_iType_set_then_override_is_none(self):  # noqa: E501
        "Check that the override property is set to None"

        test_values = {
            ZONE_TYPE.Manager,
            ZONE_TYPE.ControlOnOffPID,
            ZONE_TYPE.Surrogate
        }

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type
                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertFalse("override" in genius_zone.data)

    def test_when_override_applicable_for_iType_set_and_setpoint_is_zero_then_override_is_none(self):  # noqa: E501
        "Check that the override property is not set to None"

        test_values = {
            ZONE_TYPE.OnOffTimer,
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI
        }

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type
                self.raw_json["iBoostTimeRemaining"] = 0

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertTrue("override" in genius_zone.data)

    def test_when_override_applicable_for_iType_set_and_setpoint_is_not_zero_then_override_duration_is_set(self):  # noqa: E501
        "Check that the override property is not set to None"

        test_values = {
            ZONE_TYPE.OnOffTimer,
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI
        }

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type
                self.raw_json["iBoostTimeRemaining"] = self._override_duration

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                override_duration = genius_zone.data["override"]["duration"]
                self.assertEqual(override_duration, self._override_duration)

    def test_when_override_applicable_for_iType_set_and_setpoint_is_not_zero_then_override_setpoint_is_set(self):  # noqa: E501
        "Check that the override property is not set to None"

        test_values = {
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI
        }

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.raw_json["iType"] = zone_type
                self.raw_json["iBoostTimeRemaining"] = self._override_duration
                self.raw_json["fBoostSP"] = self._override_setpoint

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                override_setpoint = genius_zone.data["override"]["setpoint"]
                self.assertEqual(override_setpoint, self._override_setpoint)

    def test_when_override_applicable_for_iType_set_and_setpoint_is_not_zero_then_override_setpoint_is_true(self):  # noqa: E501
        "Check that the override property is not set to None"

        self.raw_json["iType"] = ZONE_TYPE.OnOffTimer
        self.raw_json["iBoostTimeRemaining"] = self._override_duration
        self.raw_json["fBoostSP"] = self._override_setpoint
        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertTrue(genius_zone.data["override"]["setpoint"])
