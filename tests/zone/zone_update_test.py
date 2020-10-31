"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import (
    Mock,
    patch
)
from geniushubclient.const import (
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zone import GeniusZone
from geniushubclient.zoneclasses.properties import Properties


class GeniusZoneUpdateTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, update method.
        """

    _device_id = 27
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
        self.hub = Mock()
        self.hub.api_version = 3

    def test_update_calls_properties_update_method(self):
        "Check that calling the update method calls the properties update method"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        with patch.object(genius_zone, '_properties') as mock_properties:
            mock_properties.return_value = Properties()

            genius_zone.update(self.raw_json)

            mock_properties.update.assert_called_once()
