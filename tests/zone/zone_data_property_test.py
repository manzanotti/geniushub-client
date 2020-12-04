"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock, patch

from geniushubclient.const import ZONE_MODE, ZONE_TYPE
from geniushubclient.zone import GeniusZone
from geniushubclient.zoneclasses.properties import Properties


class GeniusZoneGetV1DataTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, dataproperty population.
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
        "iFlagExpectedKit": 2,
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

    def test_data_calls_properties_populate_method(self):
        "Check that calling the data property calls the properties get_V1_data method"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        with patch.object(genius_zone, '_properties') as mock_properties:
            properties = Properties()
            mock_properties.return_value = properties

            genius_zone.data

            mock_properties._get_v1_data.assert_called_once()

    def test_update_sets_id(self):
        "Check that the data property has id set correctly"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        with patch.object(genius_zone._properties, '_get_v1_data') as mock_properties:
            mock_properties.return_value = {}

            self.assertEqual(genius_zone.data["id"], self._device_id)

    def test_update_sets_name(self):
        "Check that the data property has name set correctly"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        with patch.object(genius_zone._properties, '_get_v1_data') as mock_properties:
            mock_properties.return_value = {
                "name": self._zone_name}

            self.assertEqual(genius_zone.data["name"], self._zone_name)

    def test_update_sets_type(self):
        "Check that the data property has type set correctly"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        with patch.object(genius_zone._properties, '_get_v1_data') as mock_properties:
            zone_type = "radiator"
            mock_properties.return_value = {
                "type": zone_type}

            self.assertEqual(genius_zone.data["type"], zone_type)
