"""
    Tests for the zone Properties class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.const import ITYPE_TO_TYPE
from geniushubclient.zoneclasses.properties import Properties


class PropertiesGetDataTests(unittest.TestCase):
    """
        Test for the zone Properties Class get_v1_data method
        """

    _device_id = 27
    _zone_name = "Zone Name"
    _json_data = {"name": _zone_name, "type": "radiator"}

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_sets_name(self):
        "Check that the name is returned"

        properties = Properties()
        properties._name = self._zone_name

        data = properties._get_v1_data()

        self.assertEqual(data['name'], self._zone_name)

    def test_when_iType_set_then_data_type_is_set_correctly(self):
        "Check that the type is returned"

        for zone_type, zone_type_text in ITYPE_TO_TYPE.items():
            with self.subTest(zone_type=zone_type, zone_type_text=zone_type_text):
                properties = Properties()
                properties._type_name = zone_type_text

                data = properties._get_v1_data()

                self.assertEqual(data['type'], zone_type_text)
