"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.const import ZONE_MODE, ZONE_TYPE
from geniushubclient.zone import GeniusZone


class GeniusZoneDataTests(unittest.TestCase):
    """
    Test for the GeniusZone Class, general data.
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
            "lstSP": [
                {"fSP": 16.0, "iDay": 0, "iTm": 0},
                {"fSP": 14.0, "iDay": 0, "iTm": 23400},
                {"fSP": 20.0, "iDay": 0, "iTm": 59700},
                {"fSP": 14.0, "iDay": 0, "iTm": 75000},
                {"fSP": 16.0, "iDay": 0, "iTm": 75600},
            ],
            "objReactive": {"fActivityLevel": 0.0},
        },
        "objTimer": [{"fSP": 14.0, "iDay": 0, "iTm": -1}],
        "trigger": {"reactive": 0, "output": 0},
        "warmupDuration": {
            "bEnable": "true",
            "bEnableCalcs": "true",
            "fRiseRate": 0.5,
            "iLagTime": 2420,
            "iRiseTime": 300,
            "iTotalTime": 2720,
        },
        "zoneReactive": {"fActivityLevel": 0},
        "zoneSubType": 1,
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_raw_json_is_stored(self):
        "Check that the raw json is set on the class"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone._raw, self.raw_json)

    def test_id_is_set_correctly_test(self):
        "Check that the id is set on the data object"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.data["id"], self._device_id)

    def test_name_is_set_correctly(self):
        "Check that the name is set on the data object"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)
        self.assertEqual(genius_zone.data["name"], self._zone_name)
