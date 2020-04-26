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


class GeniusZoneTriggerTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, timer data.
        """

    _device_id = "Device Id"
    _zone_name = "Zone Name"
    _output = 20

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
            "output": _output
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

    def test_trigger_enabled_set_to_false(self):
        "Check that reactive is false on the trigger"

        self.raw_json["trigger"]["reactive"] = 0
        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertFalse(genius_zone.trigger.reactive)

    def test_trigger_enabled_set_to_true(self):
        "Check that reactive is true on the trigger"

        self.raw_json["trigger"]["reactive"] = 1
        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertTrue(genius_zone.trigger.reactive)

    def test_trigger_output_set(self):
        "Check that output is set on the trigger"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.trigger.output, self._output)
