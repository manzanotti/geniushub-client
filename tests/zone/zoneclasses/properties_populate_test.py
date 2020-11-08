"""
    Tests for the zone Properties class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    ITYPE_TO_TYPE
)
from geniushubclient.zoneclasses.properties import Properties


class PropertiesDataTests(unittest.TestCase):
    """
        Test for the zone Properties Class
        """

    _device_id = 27
    _zone_name = "Zone Name"

    def setUp(self):
        hub = Mock()
        hub.api_version = 3
        self.hub = hub

    def test_sets_id(self):
        "Check that the id is set"

        properties = Properties()
        properties.id = self._device_id
        data = {}

        properties.populate_v1_data(data)

        self.assertEqual(data['id'], self._device_id)

    def test_sets_name(self):
        "Check that the name is set"

        properties = Properties()
        properties.name = self._zone_name
        data = {}

        properties.populate_v1_data(data)

        self.assertEqual(data['name'], self._zone_name)

    def test_when_iType_set_then_data_type_is_set_correctly(self):
        "Check that the type is set"

        for zone_type, zone_type_text in ITYPE_TO_TYPE.items():
            with self.subTest(zone_type=zone_type, zone_type_text=zone_type_text):
                properties = Properties()
                properties.type_name = zone_type_text
                data = {}

                properties.populate_v1_data(data)

                self.assertEqual(data['type'], zone_type_text)
