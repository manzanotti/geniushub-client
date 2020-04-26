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


class GeniusZoneWarmUpTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, warmup data.
        """

    _device_id = "Device Id"
    _zone_name = "Zone Name"
    _warmup_rise_rate = 0.5
    _warmup_lag_time = 2420
    _warmup_rise_time = 300
    _warmup_total_time = 2720

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

    def test_warmup_enabled_set_to_true(self):
        "Check that warmup is enabled"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertTrue(genius_zone.warmup.enabled)

    def test_warmup_calcs_enabled_set_to_true(self):
        "Check that calcs_enabled is true"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertTrue(genius_zone.warmup.calcs_enabled)

    def test_warmup_lag_time_set_correctly(self):
        "Check that the warmup lag time set"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.warmup.lag_time, self._warmup_lag_time)

    def test_warmup_rise_rate_set_correctly(self):
        "Check that the warmup rise rate set"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.warmup.rise_rate, self._warmup_rise_rate)

    def test_warmup_rise_time_set_correctly(self):
        "Check that the warmup rise time set"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.warmup.rise_time, self._warmup_rise_time)

    def test_warmup_total_time_set_correctly(self):
        "Check that the warmup total time set"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.warmup.total_time, self._warmup_total_time)
