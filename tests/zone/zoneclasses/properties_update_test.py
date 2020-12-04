"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    ITYPE_TO_TYPE,
    ZONE_KIT,
    ZONE_TYPE
)
from geniushubclient.zoneclasses.properties import Properties


class PropertiesTests(unittest.TestCase):
    """
        Test for the zone Properties Class.
        """

    _device_id = 27
    _zone_name = "Zone Name"

    raw_json = {
        "iID": _device_id,
        "strName": _zone_name,
        "iFlagExpectedKit": 517,
        "iType": ZONE_TYPE.OnOffTimer,
        "zoneSubType": 1
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_sets_id(self):
        "Check that the id is set"

        self.raw_json["iId"] = self._device_id
        properties = Properties()

        properties.update(self.raw_json)

        self.assertEqual(properties.id, self._device_id)

    def test_sets_name(self):
        "Check that the name is set"

        self.raw_json["strName"] = self._zone_name
        properties = Properties()

        properties.update(self.raw_json)

        self.assertEqual(properties.name, self._zone_name)

    def test_when_iType_set_then_properties_zone_type_is_set_correctly(self):
        "Check that the zone_type is set on the properties object"

        test_values = {
            ZONE_TYPE.Manager,
            ZONE_TYPE.OnOffTimer,
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.ControlOnOffPID,
            ZONE_TYPE.TPI,
            ZONE_TYPE.Surrogate
        }

        for zone_type in test_values:
            with self.subTest(zone_type=zone_type):  # noqa: E501
                self.raw_json["iType"] = zone_type
                self.raw_json["zoneSubType"] = 1
                properties = Properties()

                properties.update(self.raw_json)

                self.assertEqual(properties.zone_type, zone_type)

    def test_when_iType_set_then_properties_type_name_is_set_correctly(self):
        "Check that the type_name is set on the properties object"

        test_values = {
            ZONE_TYPE.Manager,
            ZONE_TYPE.OnOffTimer,
            ZONE_TYPE.ControlSP,
            ZONE_TYPE.ControlOnOffPID,
            ZONE_TYPE.TPI,
            ZONE_TYPE.Surrogate
        }

        for zone_type in test_values:
            zone_type_text = ITYPE_TO_TYPE[zone_type]
            with self.subTest(zone_type=zone_type, zone_type_text=zone_type_text):  # noqa: E501
                self.raw_json["iType"] = zone_type
                self.raw_json["zoneSubType"] = 1
                properties = Properties()

                properties.update(self.raw_json)

                self.assertEqual(properties.type_name, zone_type_text)

    def test_when_iType_TPI_and_subzonetype_zero_then_properties_type_set_to_wet_underfloor(self):  # noqa: E501
        """Check that the zone_type is set to ControlOnOffPID

        when zone type is TPI and zone subtype is 0"""

        self.raw_json["iType"] = ZONE_TYPE.TPI
        self.raw_json["zoneSubType"] = 0
        properties = Properties()

        properties.update(self.raw_json)

        self.assertEqual(properties.zone_type, ZONE_TYPE.ControlOnOffPID)

    def test_when_iType_TPI_and_subzonetype_zero_then_properties_type_name_set_to_wet_underfloor(self):  # noqa: E501
        """Check that the type_name is set to wet underfloor

        when zone type is TPI and zone subtype is 0"""

        self.raw_json["iType"] = ZONE_TYPE.TPI
        self.raw_json["zoneSubType"] = 0
        properties = Properties()

        properties.update(self.raw_json)

        self.assertEqual(properties.type_name, "wet underfloor")

    def test_when_zone_does_not_have_room_sensor_then_has_room_sensor_false(self):  # noqa: E501
        "Check that has_room_sensor set to false when zone does not have a room sensor"

        self.raw_json["iType"] = ZONE_TYPE.TPI
        self.raw_json["zoneSubType"] = 0
        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.Valve
        properties = Properties()

        properties.update(self.raw_json)

        self.assertFalse(properties.has_room_sensor)

    def test_when_zone_does_have_room_sensor_then_has_room_sensor_true(self):  # noqa: E501
        "Check that has_room_sensor set to true when zone does have a room sensor"

        self.raw_json["iType"] = ZONE_TYPE.TPI
        self.raw_json["zoneSubType"] = 0
        self.raw_json["iFlagExpectedKit"] = ZONE_KIT.PIR
        properties = Properties()

        properties.update(self.raw_json)

        self.assertTrue(properties.has_room_sensor)
