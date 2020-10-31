"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock
from geniushubclient.const import (
    ITYPE_TO_TYPE,
    ZONE_KIT,
    ZONE_MODE,
    ZONE_TYPE
)
from geniushubclient.zoneclasses.properties import Properties


class GeniusZoneDataPropertiesTests(unittest.TestCase):
    """
        Test for the GeniusZone Class, properties data.
        """

    _device_id = 27
    _zone_name = "Zone Name"

    raw_json = {
        "iID": _device_id,
        "strName": _zone_name,
        "iFlagExpectedKit": ZONE_KIT.Valve,
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
        data = {}

        properties.populate_v1_data(data)

        self.assertEqual(data['id'], self._device_id)

    def test_sets_name(self):
        "Check that the name is set"

        self.raw_json["strName"] = self._zone_name
        properties = Properties()
        properties.update(self.raw_json)
        data = {}

        properties.populate_v1_data(data)

        self.assertEqual(data['name'], self._zone_name)

    def test_when_iType_set_then_data_type_is_set_correctly(self):
        "Check that the type_name is set on the properties object"

        for zone_type, zone_type_text in ITYPE_TO_TYPE.items():
            with self.subTest(zone_type=zone_type, zone_type_text=zone_type_text):
                self.raw_json["iType"] = zone_type
                self.raw_json["zoneSubType"] = 1
                properties = Properties()
                properties.update(self.raw_json)
                data = {}

                properties.populate_v1_data(data)

                self.assertEqual(data['type'], zone_type_text)

    def test_when_iType_TPI_and_subzonetype_zero_then_properties_type_set_to_wet_underfloor(self):  # noqa: E501
        """Check that the type_name is set to wet underfloor when zone type is TPI
        and zone subtype is 0"""

        self.raw_json["iType"] = ZONE_TYPE.TPI
        self.raw_json["zoneSubType"] = 0
        properties = Properties()
        properties.update(self.raw_json)
        data = {}

        properties.populate_v1_data(data)

        zone_type_text = ITYPE_TO_TYPE[ZONE_TYPE.ControlOnOffPID]
        self.assertEqual(data['type'], zone_type_text)
