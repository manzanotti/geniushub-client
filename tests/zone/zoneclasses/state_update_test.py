"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    IMODE_TO_MODE,
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zoneclasses.state import State


class GeniusZoneStateTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, state data.
        """

    zone_type = ZONE_TYPE.OnOffTimer

    raw_json = {
        "bIsActive": 0,
        "bInHeatEnabled": 0,
        "bOutRequestHeat": 0,
        "fPV": 21.0,
        "fSP": 14.0,
        "iMode": ZONE_MODE.Off
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_when_bIsActive_is_false_then_is_active_false(self):
        "Check that is_active is correctly set to false"

        self.raw_json["bIsActive"] = 0
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertFalse(state.is_active)

    def test_when_bIsActive_is_true_then_is_active_true(self):
        "Check that is_active is correctly set to true"

        self.raw_json["bIsActive"] = 1
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertTrue(state.is_active)

    def test_when_bOutRequestHeat_is_false_then_is_requesting_heat_false(self):
        "Check that is_requesting_heat_out is correctly set to false"

        self.raw_json["bOutRequestHeat"] = 0
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertFalse(state.is_requesting_heat)

    def test_when_bOutRequestHeat_is_true_then_is_requesting_heat_true(self):
        "Check that is_requesting_heat_out is correctly set to true"

        self.raw_json["bOutRequestHeat"] = 1
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertTrue(state.is_requesting_heat)

    def test_when_iMode_set_then_mode_is_set(self):
        "Check that the mode is set on the class"

        test_values = {
            ZONE_MODE.Off,
            ZONE_MODE.Timer,
            ZONE_MODE.Footprint,
            ZONE_MODE.Away,
            ZONE_MODE.Boost,
            ZONE_MODE.Override,
            ZONE_MODE.Early,
            ZONE_MODE.Test,
            ZONE_MODE.Linked,
            ZONE_MODE.Other
        }

        for zone_mode in test_values:
            with self.subTest(zone_mode=zone_mode):
                self.raw_json["iMode"] = zone_mode
                self.raw_json["zoneSubType"] = 1
                state = State()

                state.update(self.raw_json, self.zone_type)

                self.assertEqual(state.mode, zone_mode)

    def test_when_iMode_set_then_mode_name_is_set(self):
        "Check that the name is set on the class"

        test_values = {
            ZONE_MODE.Off,
            ZONE_MODE.Timer,
            ZONE_MODE.Footprint,
            ZONE_MODE.Away,
            ZONE_MODE.Boost,
            ZONE_MODE.Override,
            ZONE_MODE.Early,
            ZONE_MODE.Test,
            ZONE_MODE.Linked,
            ZONE_MODE.Other
        }

        for zone_mode in test_values:
            zone_mode_text = IMODE_TO_MODE[zone_mode]
            with self.subTest(zone_mode=zone_mode, zone_mode_text=zone_mode_text):
                self.raw_json["iMode"] = zone_mode
                self.raw_json["zoneSubType"] = 1
                state = State()

                state.update(self.raw_json, self.zone_type)

                self.assertEqual(state.mode_name, zone_mode_text)

    def test_when_iType_ControlSP_or_TPI_then_temperature_set(self):
        "Check that the temperature is set on the state when the iType is ControlSP"

        temperature = 20.0
        setpoint = 21.0
        test_values = [
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI
        ]
        self.raw_json["fPV"] = temperature
        self.raw_json["fSP"] = setpoint

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.zone_type = zone_type
                state = State()

                state.update(self.raw_json, self.zone_type)

                self.assertEqual(state.temperature, temperature)

    def test_when_iType_ControlSP_or_TPI_then_setpoint_set(self):
        "Check that the setpoint is set on the state when the iType is ControlSP"

        temperature = 20.0
        setpoint = 21.0
        test_values = [
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.TPI
        ]
        self.raw_json["fPV"] = temperature
        self.raw_json["fSP"] = setpoint

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                self.zone_type = zone_type
                state = State()

                state.update(self.raw_json, self.zone_type)

                self.assertEqual(state.setpoint, setpoint)

    def test_when_iType_Manager_then_temperature_set(self):
        "Check that the temperature is set on the state when the iType is ControlSP"

        temperature = 20.0
        setpoint = 21.0
        self.raw_json["fPV"] = temperature
        self.raw_json["fSP"] = setpoint
        self.zone_type = ZONE_TYPE.Manager
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertEqual(state.temperature, temperature)

    def test_when_iType_Manager_then_setpoint_not_set(self):
        "Check that the setpoint is not set on the state when the iType is Manager"

        temperature = 20.0
        setpoint = 21.0
        self.raw_json["fPV"] = temperature
        self.raw_json["fSP"] = setpoint
        self.zone_type = ZONE_TYPE.Manager
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertIsNone(state.setpoint)

    def test_when_iType_OnOffTimer_then_temperature_not_set(self):
        "Check that the temperature is not set on the state when the iType is OnOffTimer"  # noqa: E501

        temperature = 20.0
        setpoint = 21.0
        self.raw_json["fPV"] = temperature
        self.raw_json["fSP"] = setpoint
        self.zone_type = ZONE_TYPE.OnOffTimer
        state = State()

        state.update(self.raw_json, self.zone_type)

        self.assertIsNone(state.temperature)

    def test_when_zone_type_not_ControlSP_then_heat_in_enabled_not_set(self):
        """Check that heat_in_enabled is not set on the class"

        when the zone type is not ControlSP"""

        test_values = {
            ZONE_TYPE.Manager,
            ZONE_TYPE.OnOffTimer,
            ZONE_TYPE.ControlOnOffPID,
            ZONE_TYPE.TPI,
            ZONE_TYPE.Surrogate
        }

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):
                state = State()

                state.update(self.raw_json, zone_type)

                self.assertIsNone(state.heat_in_enabled)

    def test_when_zone_type_ControlSP_then_heat_in_enabled_set(self):
        """Check that heat_in_enabled is set on the class"

        when the zone type is ControlSP"""

        zone_type = ZONE_TYPE.ControlSP
        self.raw_json["bInHeatEnabled"] = 1
        state = State()

        state.update(self.raw_json, zone_type)

        self.assertTrue(state.heat_in_enabled)
