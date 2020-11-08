"""
    Tests for the zone State class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    IMODE_TO_MODE,
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zoneclasses.state import State


class StateDataTests(unittest.TestCase):
    """
        Tests for the zone State Class populate method,

        which converts the class to v1 json.
        """

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_when_is_active_false_then_bIsActive_false(self):
        "Check that bIsActive is correctly set to false"

        state = State()
        state.is_active = 0
        data = {}

        state.populate_v1_data(data)

        self.assertFalse(data["_state"]["bIsActive"])

    def test_when_is_active_true_then_bIsActive_true(self):
        "Check that bIsActive is correctly set to true"

        state = State()
        state.is_active = 1
        data = {}

        state.populate_v1_data(data)

        self.assertTrue(data["_state"]["bIsActive"])

    def test_when_is_requesting_heat_false_then_bOutRequestHeat_false(self):
        "Check that bOutRequestHeat is set to false"

        state = State()
        state.is_requesting_heat = 0
        data = {}

        state.populate_v1_data(data)

        self.assertFalse(data["output"])

    def test_when_is_requesting_heat_true_then_bOutRequestHeat_true(self):
        "Check that bOutRequestHeat is set to true"

        state = State()
        state.is_requesting_heat = 1
        data = {}

        state.populate_v1_data(data)

        self.assertTrue(data["output"])

    def test_mode_set_correctly(self):
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
                state = State()
                mode_name = IMODE_TO_MODE[zone_mode]
                state.mode_name = mode_name
                data = {}

                state.populate_v1_data(data)

                self.assertEqual(data["mode"], mode_name)

    def test_when_temperature_none_then_temperature_not_returned(self):
        "Check that temperature is not set on returned object when temperature is None"

        state = State()
        state.temperature = None
        data = {}

        state.populate_v1_data(data)

        self.assertFalse("temperature" in data)

    def test_when_temperature_set_then_temperature_returned(self):
        "Check that temperature is set on returned object when temperature is not None"

        temperature = 21.0
        state = State()
        state.temperature = temperature
        data = {}

        state.populate_v1_data(data)

        self.assertEqual(data["temperature"], temperature)

    def test_when_setpoint_none_then_setpoint_not_returned(self):
        "Check that setpoint is not set on returned object when setpoint is None"

        state = State()
        state.setpoint = None
        data = {}

        state.populate_v1_data(data)

        self.assertFalse("setpoint" in data)

    def test_when_setpoint_set_and_zone_type_not_OnOffTimer_then_setpoint_returned_as_float(self):  # noqa:E501
        "Check that setpoint is set on returned object when setpoint is not None"

        setpoint = 21.0
        state = State()
        state.setpoint = setpoint
        data = {}

        state.populate_v1_data(data)

        self.assertEqual(data["setpoint"], setpoint)

    def test_when_setpoint_set_and_zone_type_OnOffTimer_then_setpoint_returned_as_bool(self):  # noqa:E501
        "Check that setpoint is set on returned object when setpoint is not None"

        setpoint = 21.0
        state = State()
        state._zone_type = ZONE_TYPE.OnOffTimer
        state.setpoint = setpoint
        data = {}

        state.populate_v1_data(data)

        self.assertTrue(data["setpoint"])

    def test_when_heat_in_enabled_none_then_bInHeatEnabled_not_returned(self):
        """Check that bInHeatEnabled is not set on returned object

        when heat_in_enabled is None"""

        state = State()
        state.heat_in_enabled = None
        data = {}

        state.populate_v1_data(data)

        self.assertFalse("bInHeatEnabled" in data["_state"])

    def test_when_heat_in_enabled_set_then_bInHeatEnabled_returned(self):
        """Check that bInHeatEnabled is set on returned object

        when heat_in_enabled is set"""

        state = State()
        state.heat_in_enabled = 1
        data = {}

        state.populate_v1_data(data)

        self.assertTrue(data["_state"]["bInHeatEnabled"])
