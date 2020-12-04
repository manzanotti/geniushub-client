"""
    Tests for the zone Properties class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.const import ITYPE_TO_TYPE, ZONE_TYPE
from geniushubclient.zoneclasses.properties import Properties


class PropertiesUpdateV1Tests(unittest.TestCase):
    """Test for the update method zone Properties Class,

    using V1 json data"""

    _device_id = 27
    _zone_name = "Zone Name"

    raw_json = {
        "id": _device_id,
        "name": _zone_name,
        "type": ITYPE_TO_TYPE[ZONE_TYPE.OnOffTimer]
    }

    def setUp(self):
        hub = Mock()
        hub.api_version = 1
        self.hub = hub

    def test_update_sets_name(self):
        "Check that the name is set"

        self.raw_json["name"] = self._zone_name
        properties = Properties()

        properties._update(self.raw_json, self.hub.api_version)

        self.assertEqual(properties.name, self._zone_name)

    def test_update_when_iType_set_then_properties_zone_type_is_set_correctly(self):
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
                self.raw_json["type"] = ITYPE_TO_TYPE[zone_type]
                properties = Properties()

                properties._update(self.raw_json, self.hub.api_version)

                self.assertEqual(properties.zone_type, zone_type)

    def test_update_when_iType_set_then_properties_type_name_is_set_correctly(self):
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
                self.raw_json["type"] = zone_type_text
                properties = Properties()

                properties._update(self.raw_json, self.hub.api_version)

                self.assertEqual(properties.type_name, zone_type_text)

    def test_update_when_zone_does_not_have_room_sensor_then_has_room_sensor_false(self):  # noqa: E501
        "Check that has_room_sensor set to false when zone does not have a room sensor"

        self.raw_json["type"] = ITYPE_TO_TYPE[ZONE_TYPE.TPI]
        # Can't guarantee the running order of the tests, so clear occupied out
        # if it's in the dictionary
        if "occupied" in self.raw_json:
            self.raw_json.pop("occupied")
        properties = Properties()

        properties._update(self.raw_json, self.hub.api_version)

        self.assertFalse(properties.has_room_sensor)

    def test_update_when_zone_does_have_room_sensor_then_has_room_sensor_true(self):  # noqa: E501
        "Check that has_room_sensor set to true when zone does have a room sensor"

        self.raw_json["type"] = ITYPE_TO_TYPE[ZONE_TYPE.TPI]
        self.raw_json["occupied"] = 1
        properties = Properties()

        properties._update(self.raw_json, self.hub.api_version)

        self.assertTrue(properties.has_room_sensor)
