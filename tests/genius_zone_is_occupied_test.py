"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    ZONE_KIT,
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zone import GeniusZone


class GeniusZoneIsOccupiedTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, is_occupied property data.
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

    def test_when_zone_does_not_have_room_sensor_then_is_occupied_is_false(self):  # noqa: E501
        "Check that is_occupied is false when the zone does not have a room sensor"

        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.Valve
        self.raw_json["objFootprint"]["bIsNight"] = 0
        self.raw_json["trigger"]["reactive"] = 1
        self.raw_json["trigger"]["output"] = 1

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.state.is_occupied)

    def test_when_is_night_then_is_occupied_is_false(self):  # noqa: E501
        "Check that is_occupied is false when the zone is_night true"

        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.PIR
        self.raw_json["objFootprint"]["bIsNight"] = 1
        self.raw_json["trigger"]["reactive"] = 1
        self.raw_json["trigger"]["output"] = 1

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.state.is_occupied)

    def test_when_trigger_reactive_true_then_is_occupied_is_false(self):  # noqa: E501
        "Check that is_occupied is false when the zone trigger reactive is set to true"

        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.PIR
        self.raw_json["objFootprint"]["bIsNight"] = 0
        self.raw_json["trigger"]["reactive"] = 1
        self.raw_json["trigger"]["output"] = 0

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.state.is_occupied)

    def test_when_trigger_output_true_then_is_occupied_is_false(self):  # noqa: E501
        "Check that is_occupied is false when the zone trigger output is set to true"

        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.PIR
        self.raw_json["objFootprint"]["bIsNight"] = 0
        self.raw_json["trigger"]["reactive"] = 0
        self.raw_json["trigger"]["output"] = 1

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.state.is_occupied)

    def test_when_footprint_reactive_activity_level_zero_then_is_occupied_is_false(self):  # noqa: E501
        "Check that is_occupied is false when the zone footprint reactive activity_level is above zero"  # noqa: E501

        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.PIR
        self.raw_json["objFootprint"]["bIsNight"] = 0
        self.raw_json["trigger"]["reactive"] = 1
        self.raw_json["trigger"]["output"] = 1
        self.raw_json["objFootprint"]["objReactive"]["fActivityLevel"] = 0.0

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertFalse(genius_zone.state.is_occupied)

    def test_when_all_conditions_correct_then_is_occupied_is_true(self):  # noqa: E501
        "Check that when all the conditions are met, is_occupied is true"

        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.PIR
        self.raw_json["objFootprint"]["bIsNight"] = 0
        self.raw_json["trigger"]["reactive"] = 1
        self.raw_json["trigger"]["output"] = 1
        self.raw_json["objFootprint"]["objReactive"]["fActivityLevel"] = 1.0

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        self.assertTrue(genius_zone.state.is_occupied)
