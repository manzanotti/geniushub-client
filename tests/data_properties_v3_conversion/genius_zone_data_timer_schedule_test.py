"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    IDAY_TO_DAY,
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zone import GeniusZone


class GeniusZoneDataTimerScheduleTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, timer schedule data.
        """

    _device_id = "Device Id"
    _zone_name = "Zone Name"

    _heating_period_start = 72000
    _heating_period_end = 73800
    _heating_period_setpoint = 19.0

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
                "fActivityLevel": 0.0
            }
        },
        "objTimer": [
            {
                "fSP": 14.0,
                "iDay": 0,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": _heating_period_setpoint,
                "iDay": 0,
                "iTm": _heating_period_start
            }, {
                "fSP": 14.0,
                "iDay": 0,
                "iTm": _heating_period_end
            }, {
                "bReactive": 0.0,
                "fSP": 18.0,
                "iDay": 0,
                "iTm": _heating_period_end + 200
            }, {
                "fSP": 14.0,
                "iDay": 1,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": 19.0,
                "iDay": 1,
                "iTm": 72000
            }, {
                "fSP": 14.0,
                "iDay": 2,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": 19.0,
                "iDay": 2,
                "iTm": 72000
            }, {
                "bReactive": 0.0,
                "fSP": 14.0,
                "iDay": 2,
                "iTm": 72900
            }, {
                "fSP": 14.0,
                "iDay": 3,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": 19.0,
                "iDay": 3,
                "iTm": 72000
            }, {
                "bReactive": 0.0,
                "fSP": 14.0,
                "iDay": 3,
                "iTm": 72900
            }, {
                "fSP": 14.0,
                "iDay": 4,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": 19.0,
                "iDay": 4,
                "iTm": 72000
            }, {
                "bReactive": 0.0,
                "fSP": 14.0,
                "iDay": 4,
                "iTm": 72900
            }, {
                "fSP": 14.0,
                "iDay": 5,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": 19.0,
                "iDay": 5,
                "iTm": 72000
            }, {
                "bReactive": 0.0,
                "fSP": 14.0,
                "iDay": 5,
                "iTm": 72900
            }, {
                "fSP": 14.0,
                "iDay": 6,
                "iTm": -1
            }, {
                "bReactive": 0.0,
                "fSP": 19.0,
                "iDay": 6,
                "iTm": 72900
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

    def test_when_timer_schedule_parsed_then_timer_schedule_has_seven_days(self):
        "Check that the timer schedule has seven days of data"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        days = genius_zone.data["schedule"]["timer"]["weekly"]
        self.assertEqual(len(days), 7)

    def test_when_timer_schedule_parsed_then_timer_schedule_has_seven_days_named_correctly(self):  # noqa: E501
        "Check that the timer schedule has seven days of data"

        for day_int, day_text in IDAY_TO_DAY.items():
            with self.subTest(day_int=day_int, day_text=day_text):

                genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

                days = genius_zone.data["schedule"]["timer"]["weekly"]
                self.assertTrue(day_text in days)

    def test_when_timer_schedule_parsed_then_timer_schedule_first_day_has_2_heating_periods(self):  # noqa: E501
        "Check that the first day of the timer schedule has 2 heating periods"

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        day = genius_zone.data["schedule"]["timer"]["weekly"]["sunday"]
        heating_periods = day["heatingPeriods"]
        self.assertEqual(len(heating_periods), 2)

    def test_when_timer_schedule_parsed_then_timer_schedule_first_day_first_heating_period_has_correct_setpoint(self):  # noqa: E501
        """Check that the first heating period of the first day of the timer schedule

        has the correct set point set"""

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        day = genius_zone.data["schedule"]["timer"]["weekly"]["sunday"]
        heating_period = day["heatingPeriods"][0]
        self.assertEqual(heating_period["setpoint"], self._heating_period_setpoint)

    def test_when_timer_schedule_parsed_then_timer_schedule_first_day_first_heating_period_has_correct_start(self):  # noqa: E501
        """Check that the first heating period of the first day of the timer schedule

        has the correct start time set"""

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        day = genius_zone.data["schedule"]["timer"]["weekly"]["sunday"]
        heating_period = day["heatingPeriods"][0]
        self.assertEqual(heating_period["start"], self._heating_period_start)

    def test_when_timer_schedule_parsed_then_timer_schedule_first_day_first_heating_period_has_correct_end(self):  # noqa: E501
        """Check that the first heating period of the first day of the timer schedule

        has the correct end time set"""

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        day = genius_zone.data["schedule"]["timer"]["weekly"]["sunday"]
        heating_period = day["heatingPeriods"][0]
        self.assertEqual(heating_period["end"], self._heating_period_end)

    def test_when_next_heating_period_does_not_have_start_time_then_timer_schedule_first_day_second_heating_period_has_default_end(self):  # noqa: E501
        """Check that the last heating period of the first day of the timer schedule

        has the end time set to end of day when next heating periodhas -1 start time"""

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        day = genius_zone.data["schedule"]["timer"]["weekly"]["sunday"]
        heating_period = day["heatingPeriods"][1]
        self.assertEqual(heating_period["end"], 86400)

    def test_when_last_setpoint_then_timer_schedule_last_day_last_heating_period_has_default_end(self):  # noqa: E501
        """Check that the last heating period of the last day of the timer schedule

        has the correct end time set"""

        genius_zone = GeniusZone(self._device_id, self.raw_json, self.hub)

        day = genius_zone.data["schedule"]["timer"]["weekly"]["saturday"]
        heating_period = day["heatingPeriods"][0]
        self.assertEqual(heating_period["end"], 86400)
