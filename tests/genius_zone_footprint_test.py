"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zone import GeniusZone


class GeniusZoneFootprintTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, footprint data.
        """

    _device_id = "Device Id"
    _zone_name = "Zone Name"
    _activity_level = 1.0

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
        "iType": ZONE_TYPE.ControlSP,
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
                "fActivityLevel": _activity_level
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
        "zoneSubType": 1
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_footprint_is_night_set_to_false(self):
        "Check that is_night is set to false on the footprint"

        self.raw_json["objFootprint"]["bIsNight"] = 0
        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertFalse(genius_zone.footprint.is_night)

    def test_footprint_is_night_set_to_true(self):
        "Check that is_night is set to true on the footprint"

        self.raw_json["objFootprint"]["bIsNight"] = 1
        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertTrue(genius_zone.footprint.is_night)

    def test_warmup_calcs_enabled_set_to_true(self):
        "Check that activity_level is set on the footprint"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.footprint.reactive.activity_level, self._activity_level)  # noqa: E501
