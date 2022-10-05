"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.const import ITYPE_TO_TYPE, ZONE_MODE, ZONE_TYPE
from geniushubclient.zone import GeniusZone


class GeniusZoneDataPropertiesTests(unittest.TestCase):
    """
    Test for the GeniusZone Class, properties data.
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

    def test_when_iType_set_then_data_type_is_set_correctly(self):
        "Check that the type_name is set on the properties object"

        for zone_type, zone_type_text in ITYPE_TO_TYPE.items():
            with self.subTest(zone_type=zone_type, zone_type_text=zone_type_text):
                self.raw_json["iType"] = zone_type
                self.raw_json["zoneSubType"] = 1
                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                self.assertEqual(genius_zone.data["type"], zone_type_text)

    def test_when_iType_TPI_and_subzonetype_zero_then_properties_type_set_to_wet_underfloor(
        self,
    ):  # noqa: E501
        """Check that the type_name is set to wet underfloor when zone type is TPI
        and zone subtype is 0"""

        self.raw_json["iType"] = ZONE_TYPE.TPI
        self.raw_json["zoneSubType"] = 0
        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        zone_type_text = ITYPE_TO_TYPE[ZONE_TYPE.ControlOnOffPID]
        self.assertEqual(genius_zone.data["type"], zone_type_text)
