"""Python client library for the Genius Hub API.

    see: https://github.com/zxdavb/geniushub-client
    see: https://my.geniushub.co.uk/docs
    """

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List  # Any, Optional, Set, Tuple

from .const import HUB_SW_VERSIONS, ISSUE_DESCRIPTION, ISSUE_TEXT, ZONE_MODE
from .session import GeniusService
from .zone import GeniusZone, natural_sort
from .device import GeniusDevice

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

# Debugging flags - all False for production releases
DEBUG_LOGGING = False
DEBUG_MODE = False

if DEBUG_LOGGING is True:
    _LOGGER.setLevel(logging.DEBUG)

if DEBUG_MODE is True:
    import ptvsd

    _LOGGER.warning("Waiting for debugger to attach...")
    ptvsd.enable_attach(address=("127.0.0.1", 5678), redirect_output=True)
    ptvsd.wait_for_attach()
    _LOGGER.debug("Debugger is attached!")


class GeniusHub:
    """The class for a connection to a Genius Hub."""

    def __init__(
        self, hub_id, username=None, password=None, session=None, debug=False
    ) -> None:
        if debug is True:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("Debug mode is explicitly enabled.")
        else:
            _LOGGER.debug(
                "Debug mode is not explicitly enabled (but may be enabled elsewhere)."
            )

        self.genius_service = GeniusService(hub_id, username, password, session)
        self.api_version = 3 if username or password else 1

        self._verbose = 1

        self._sense_mode = None
        self._zones = self._devices = self._issues = self._version = None
        self._test_json = {}  # used with GeniusTestHub

        self.zone_objs = []
        self.device_objs = []
        self.issues = []
        self.version = {}
        self.uid = None

        self.zone_by_id = {}
        self.zone_by_name = {}
        self.device_by_id = {}

    def __repr__(self) -> str:
        return json.dumps(self.version)

    @staticmethod
    def _zones_via_v3_zones(raw_json) -> List[Dict]:
        """Extract Zones from /v3/zones JSON."""
        return raw_json["data"]

    @staticmethod
    def _devices_via_v3_data_mgr(raw_json) -> List[Dict]:
        """Extract Devices from /v3/data_manager JSON."""
        result = []
        for site in [
            x
            for x in raw_json["data"]["childNodes"].values()
            if x["addr"] != "WeatherData"
        ]:
            for device in [x for x in site["childNodes"].values() if x["addr"] != "1"]:
                result.append(device)
                for channel in [
                    x for x in device["childNodes"].values() if x["addr"] != "_cfg"
                ]:
                    temp = dict(channel)
                    temp["addr"] = f"{device['addr']}-{channel['addr']}"
                    result.append(temp)
        return result

    @staticmethod
    def _issues_via_v3_zones(raw_json) -> List[Dict]:
        """Extract Issues from /v3/zones JSON."""
        result = []
        for zone in raw_json["data"]:
            for issue in zone["lstIssues"]:
                if "data" not in issue:
                    issue["data"] = {}
                issue["data"]["location"] = zone["strName"]
                result.append(issue)
        return result

    @staticmethod
    def _version_via_v3_zones(raw_json) -> str:
        """Extract Version from /v3/zones JSON (a hack)."""
        build_date = datetime.strptime(raw_json["data"][0]["strBuildDate"], "%b %d %Y")

        for date_time_idx in HUB_SW_VERSIONS:
            if datetime.strptime(date_time_idx, "%b %d %Y") <= build_date:
                return HUB_SW_VERSIONS[date_time_idx]

    @property
    def verbosity(self) -> int:
        """Get/Set the level of detail."""
        return self._verbose

    @verbosity.setter
    def verbosity(self, value) -> None:
        if 0 <= value <= 3:
            self._verbose = value
        else:
            raise ValueError(
                f"{value} is not valid for verbosity, the permissible range is (0-3)."
            )

    @property
    def zones(self) -> List:
        """Return a list of Zones known to the Hub.

          v1/zones/summary: id, name
          v1/zones:         id, name, type, mode, temperature, setpoint,
          occupied, override, schedule
        """
        return [z.data for z in self.zone_objs]

    @property
    def devices(self) -> List:
        """Return a list of Devices known to the Hub.

          v1/devices/summary: id, type
          v1/devices:         id, type, assignedZones, state
        """
        key = "addr" if self.verbosity == 3 else "id"
        return natural_sort([d.data for d in self.device_objs], key)

    def _update(self):
        """Update the Hub with its latest state data."""

        def populate_objects(obj_list, obj_key, obj_by_id, GeniusObject) -> List:
            """Create the current list of GeniusHub objects (zones/devices)."""
            entities = []  # list of converted zones/devices
            key = "id" if self.genius_service.use_v1_api else obj_key
            for raw_json in obj_list:
                try:  # does the hub already know about this zone/device?
                    entity = obj_by_id[raw_json[key]]
                except KeyError:  # this is a new zone/device
                    entity = GeniusObject(raw_json[key], raw_json, self)
                else:
                    entity._convert(raw_json)
                entities.append(entity)
            return entities

        def convert_issue(raw_json) -> Dict:
            """Convert a issues's v3 JSON to the v1 schema."""
            description = ISSUE_DESCRIPTION.get(raw_json["id"], raw_json["id"])
            level = ISSUE_TEXT.get(raw_json["level"], str(raw_json["level"]))

            if "{zone_name}" in description:
                zone_name = raw_json["data"]["location"]
            if "{device_type}" in description:
                # don't use nodeHash, it won't pick up (e.g. DCR - Channel 1)
                # vice_type = DEVICE_HASH_TO_TYPE[raw_json["data"]["nodeHash"]]
                device_type = self.device_by_id[raw_json["data"]["nodeID"]].data["type"]

            if "{zone_name}" in description and "{device_type}" in description:
                description = description.format(
                    zone_name=zone_name, device_type=device_type
                )
            elif "{zone_name}" in description:
                description = description.format(zone_name=zone_name)
            elif "{device_type}" in description:
                description = description.format(device_type=device_type)

            return {"description": description, "level": level}

        if self.genius_service.use_v1_api:
            self._sense_mode = None  # currently, no way to tell
        else:  # self.api_version == 3:
            manager = [z for z in self._zones if z["iID"] == 0][0]
            self._sense_mode = bool(manager["lOptions"] & ZONE_MODE.Other)

        zones = self.zone_objs = populate_objects(
            self._zones, "iID", self.zone_by_id, GeniusZone
        )
        devices = self.device_objs = populate_objects(
            self._devices, "addr", self.device_by_id, GeniusDevice
        )

        self.zone_by_id = {z.id: z for z in self.zone_objs}
        self.zone_by_name = {z.name: z for z in self.zone_objs}
        self.device_by_id = {d.id: d for d in self.device_objs}

        for zone in zones:  # TODO: this need checking
            zone.device_objs = [
                d for d in devices if d.data["assignedZones"][0]["name"] == zone.name
            ]
            zone.device_by_id = {d.id: d for d in zone.device_objs}

        old_issues = self.issues
        if self.genius_service.use_v1_api:
            self.issues = self._issues
            self.version = self._version
        else:  # self.api_version == 3:
            self.issues = [convert_issue(raw_json) for raw_json in self._issues]
            self.version = {
                "hubSoftwareVersion": self._version,
                "earliestCompatibleAPI": "https://my.geniushub.co.uk/v1",
                "latestCompatibleAPI": "https://my.geniushub.co.uk/v1",
            }

        for issue in [i for i in self.issues if i not in old_issues]:
            _LOGGER.warning("An Issue has been found: %s", issue)
        for issue in [i for i in old_issues if i not in self.issues]:
            _LOGGER.data("An Issue is now resolved: %s", issue)

    async def update(self) -> None:
        """Update the Hub with its latest state data."""
        if self.genius_service.use_v1_api:
            get_list = ["zones", "devices", "issues", "version"]
            (
                self._zones,
                self._devices,
                self._issues,
                self._version,
            ) = await asyncio.gather(
                *[self.genius_service.request("GET", g) for g in get_list]
            )

        else:  # self.api_version == 3:
            get_list = ["zones", "data_manager", "auth/release"]
            zones, data_manager, auth = await asyncio.gather(
                *[self.genius_service.request("GET", g) for g in get_list]
            )

            self._zones = self._zones_via_v3_zones(zones)
            self._devices = self._devices_via_v3_data_mgr(data_manager)
            self._issues = self._issues_via_v3_zones(zones)
            self._version = auth["data"]["release"]

            self.uid = auth["data"]["UID"]

        self._update()  # now parse all the JSON

    async def reboot(self) -> None:
        """Reboot the hub."""
        # x.post("/v3/system/reboot", { username: e, password: t, json:{} })
        raise NotImplementedError


class GeniusTestHub(GeniusHub):
    """The test class for a Genius Hub - uses a test file."""

    def __init__(self, zones_json, device_json, session=None, debug=None) -> None:
        super().__init__(
            "test_hub", username="test", password="xx", session=session, debug=debug
        )
        _LOGGER.data("Using GeniusTestHub()")

        self._test_json["zones"] = zones_json
        self._test_json["devices"] = device_json

    async def update(self) -> None:
        """Update the Hub with its latest state data."""
        self._zones = self._test_json["zones"]
        self._devices = self._test_json["devices"]
        self._issues = self._issues_via_v3_zones({"data": self._zones})
        self._version = self._version_via_v3_zones({"data": self._zones})  # a hack

        self._update()  # now parse all the JSON
