"""
    Tests for the GeniusZone class
    """

import unittest
from unittest.mock import Mock

from geniushubclient.issue import GeniusIssue


class GeniusIssueTests(unittest.TestCase):
    """
    Test for the GeniusIssue Class, override data.
    """

    _id = "Issue Id"
    _device_id = 12
    _zone_name = "Kitchen"
    _description = "The {device_type} in {zone_name} can not been found by the Hub"
    _device_type = "Room Sensor"

    _general_errors = {
        "manager:no_boiler_controller": "The hub does not have a boiler controller assigned",
        "manager:no_boiler_comms": "The hub has lost communication with the boiler controller",
        "manager:no_temp": "The hub does not have a valid temperature",
        "manager:weather": "Unable to fetch the weather data",  # correct
        "manager:weather_data": "Weather data -",
    }  # from app.js, search for: "node:, "zone:, "manager:

    _zone_errors = {
        "zone:using_weather_temp": "{zone_name} is currently using the outside temperature",  # correct
        "zone:using_assumed_temp": "{zone_name} is currently using the assumed temperature",
        "zone:tpi_no_temp": "{zone_name} currently has no valid temperature",  # correct
    }  # from app.js, search for: "node:, "zone:, "manager:

    _device_errors = {
        "node:no_comms": "The {device_type} has lost communication with the Hub",
        "node:warn_battery": "The battery for the {device_type} is low",
        "node:assignment_limit_exceeded": "{device_type} has been assigned to too many zones",  # for DCR channels
    }  # from app.js, search for: "node:, "zone:, "manager:

    _zone_and_device_errors = {
        "node:not_seen": "The {device_type} in {zone_name} can not been found by the Hub",  # correct
        "node:low_battery": "The battery for the {device_type} in {zone_name} is dead and needs to be replaced",  # correct
    }  # from app.js, search for: "node:, "zone:, "manager:

    raw_json = {
        "data": {
            "location": _zone_name,
            "nodeHash": "0x0000000200040005",
            "nodeID": _device_id,
        },
        "id": "node:not_seen",
        "level": 2,
    }

    def setUp(self):
        zone = Mock()
        zone.data = {}
        zone.data["type"] = self._device_type
        self.zone = zone

    def test_when_unknown_error_for_known_device_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that unknown errors for known devices are handled"

        device_by_id = {self._device_id: self.zone}

        unknown_error_id = "error:who_knows"
        self.raw_json["id"] = unknown_error_id
        genius_issue = GeniusIssue(self.raw_json, device_by_id)

        error_message = (
            "Unknown error for {device_type} in {zone_name} returned by hub: {error_id}"
        )
        self.assertEqual(
            genius_issue.data["description"],
            error_message.format(
                device_type=self._device_type,
                zone_name=self._zone_name,
                error_id=unknown_error_id,
            ),
        )

    def test_when_unknown_error_for_unknown_device_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that unknown errors for unknown devices are handled"

        device_by_id = {1: ""}

        unknown_error_id = "error:who_knows"
        self.raw_json["id"] = unknown_error_id
        genius_issue = GeniusIssue(self.raw_json, device_by_id)

        error_message = (
            "Unknown error for {device_type} in {zone_name} returned by hub: {error_id}"
        )
        self.assertEqual(
            genius_issue.data["description"],
            error_message.format(
                device_type="Unknown device",
                zone_name=self._zone_name,
                error_id=unknown_error_id,
            ),
        )

    def test_when_general_error_then_issue_message_correct(self):  # noqa: E501
        "Check that general errors are handled"

        device_by_id = {self._device_id: self.zone}

        for error_id, error_message in self._general_errors.items():
            with self.subTest(error_id=error_id, error_message=error_message):
                self.raw_json["id"] = error_id
                genius_issue = GeniusIssue(self.raw_json, device_by_id)

                self.assertEqual(genius_issue.data["description"], error_message)

    def test_when_zone_error_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that zone errors are handled"

        device_by_id = {self._device_id: self.zone}

        for error_id, error_message in self._zone_errors.items():
            with self.subTest(error_id=error_id, error_message=error_message):
                self.raw_json["id"] = error_id
                genius_issue = GeniusIssue(self.raw_json, device_by_id)

                self.assertEqual(
                    genius_issue.data["description"],
                    error_message.format(zone_name=self._zone_name),
                )

    def test_when_device_error_for_known_device_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that device errors for known devices are handled"

        device_by_id = {self._device_id: self.zone}

        for error_id, error_message in self._device_errors.items():
            with self.subTest(error_id=error_id, error_message=error_message):
                self.raw_json["id"] = error_id
                genius_issue = GeniusIssue(self.raw_json, device_by_id)

                self.assertEqual(
                    genius_issue.data["description"],
                    error_message.format(device_type=self._device_type),
                )

    def test_when_device_error_for_unknown_device_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that device errors for unknown devices are handled"

        device_by_id = {1: ""}

        for error_id, error_message in self._device_errors.items():
            with self.subTest(error_id=error_id, error_message=error_message):
                self.raw_json["id"] = error_id
                genius_issue = GeniusIssue(self.raw_json, device_by_id)

                self.assertEqual(
                    genius_issue.data["description"],
                    error_message.format(device_type="Unknown device"),
                )

    def test_when_zone_and_device_error_for_known_device_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that zone and device errors for known devices are handled"

        device_by_id = {self._device_id: self.zone}

        for error_id, error_message in self._zone_and_device_errors.items():
            with self.subTest(error_id=error_id, error_message=error_message):
                self.raw_json["id"] = error_id
                genius_issue = GeniusIssue(self.raw_json, device_by_id)

                self.assertEqual(
                    genius_issue.data["description"],
                    error_message.format(
                        device_type=self._device_type, zone_name=self._zone_name
                    ),
                )

    def test_when_zone_and_device_error_for_unknown_device_then_issue_message_correct(
        self,
    ):  # noqa: E501
        "Check that zone and device errors for unknown devices are handled"

        device_by_id = {1: ""}

        for error_id, error_message in self._zone_and_device_errors.items():
            with self.subTest(error_id=error_id, error_message=error_message):
                self.raw_json["id"] = error_id
                genius_issue = GeniusIssue(self.raw_json, device_by_id)

                self.assertEqual(
                    genius_issue.data["description"],
                    error_message.format(
                        device_type="Unknown device", zone_name=self._zone_name
                    ),
                )
