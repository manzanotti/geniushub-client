"""Python client library for the Genius Hub API."""

import logging
from typing import Dict

_LOGGER = logging.getLogger(__name__)


class GeniusIssue:
    """Class to hold information on any issues the hub is reporting"""

    # Example errors
    # {'id': 'node:low_battery',        'level': 2, 'data': {'location': 'Room 2.2',
    #        'nodeHash': '0x00000002A0107FFF', 'nodeID': '27', 'batteryLevel': 255}}
    # {'id': 'node:not_seen',           'level': 2, 'data': {'location': 'Kitchen',
    #         'nodeHash': '0x0000000000000000', 'nodeID':  '4'}}
    # {'id': 'zone:tpi_no_temp',        'level': 2, 'data': {'location': 'Temp'}}
    # {'id': 'zone:using_weather_temp', 'level': 1, 'data': {'location': 'Test Rad'}}

    def __init__(self, raw_json, device_by_id) -> None:
        self.id = id
        self._raw = raw_json
        self._device_by_id = device_by_id

        self._data = {}
        self._issue_level = {0: "information", 1: "warning", 2: "error"}
        self._issue_description = {
            "manager:no_boiler_controller": "The hub does not have a boiler controller assigned",
            "manager:no_boiler_comms": "The hub has lost communication with the boiler controller",
            "manager:no_temp": "The hub does not have a valid temperature",
            "manager:weather": "Unable to fetch the weather data",  # correct
            "manager:weather_data": "Weather data -",
            "zone:using_weather_temp": "{zone_name} is currently using the outside temperature",  # correct
            "zone:using_assumed_temp": "{zone_name} is currently using the assumed temperature",
            "zone:tpi_no_temp": "{zone_name} currently has no valid temperature",  # correct
            "node:no_comms": "The {device_type} has lost communication with the Hub",
            "node:not_seen": "The {device_type} in {zone_name} can not been found by the Hub",  # correct
            "node:low_battery": "The battery for the {device_type} in {zone_name} is dead and needs to be replaced",  # correct
            "node:warn_battery": "The battery for the {device_type} is low",
            "node:assignment_limit_exceeded": "{device_type} has been assigned to too many zones",  # for DCR channels
        }  # from app.js, search for: "node:, "zone:, "manager:

    @property
    def data(self) -> Dict:
        def convert_issue(raw_json) -> Dict:
            """Convert a issues's v3 JSON to the v1 schema."""
            unknown_error_message = (
                "Unknown error for {device_type} in {zone_name} returned by hub: "
                + raw_json["id"]
            )
            description = self._issue_description.get(
                raw_json["id"], unknown_error_message
            )
            level = self._issue_level.get(raw_json["level"], str(raw_json["level"]))

            if "{zone_name}" in description:
                zone_name = raw_json["data"]["location"]
            if "{device_type}" in description:
                # don't use nodeHash, it won't pick up (e.g. DCR - Channel 1)
                # vice_type = DEVICE_HASH_TO_TYPE[raw_json["data"]["nodeHash"]]
                device_id = raw_json["data"]["nodeID"]
                if device_id in self._device_by_id.keys():
                    device = self._device_by_id[device_id]
                    device_type = device.data["type"]
                else:
                    device_type = "Unknown device"

            if "{zone_name}" in description and "{device_type}" in description:
                description = description.format(
                    zone_name=zone_name, device_type=device_type
                )
            elif "{zone_name}" in description:
                description = description.format(zone_name=zone_name)
            elif "{device_type}" in description:
                description = description.format(device_type=device_type)

            return {"description": description, "level": level}

        return convert_issue(self._raw)
