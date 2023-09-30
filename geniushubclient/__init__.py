"""Python client library for the Genius Hub API.

see: https://github.com/manzanotti/geniushub-client
see: https://my.geniushub.co.uk/docs
"""

import asyncio
import json
import logging
from datetime import datetime as dt
from typing import Dict, List, Tuple  # Any, Optional, Set

from .const import HUB_SW_VERSIONS, ZONE_MODE
from .device import GeniusDevice
from .issue import GeniusIssue
from .session import GeniusService
from .zone import GeniusZone, natural_sort

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


class GeniusHubBase:
    """The class for a Genius Hub."""

    def __init__(self, hub_id, username=None, debug=False) -> None:
        if debug is True:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("Debug mode is explicitly enabled.")
        else:
            _LOGGER.debug(
                "Debug mode is not explicitly enabled (but may be enabled elsewhere)."
            )

        self.genius_service = self.request = None
        self.api_version = 3 if username else 1
        self._sense_mode = None
        self._verbose = 1

        self._zones = self._devices = self._issues = self._version = None
        self._test_json = {}  # v3_zones(raw_json) used by GeniusTestHub

        self.zone_objs = []
        self.device_objs = []
        self.issues = []
        self.version = {}
        self.uid = None

        self.zone_by_id = {}
        self.zone_by_name = {}
        self.device_by_id = {}

    def __str__(self) -> str:
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
        build_date = dt.strptime(raw_json["data"][0]["strBuildDate"], "%b %d %Y")

        for date_time_idx in HUB_SW_VERSIONS:
            if dt.strptime(date_time_idx, "%b %d %Y") <= build_date:
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
        return [z.info for z in self.zone_objs]

    @property
    def devices(self) -> List:
        """Return a list of Devices known to the Hub.

        v1/devices/summary: id, type
        v1/devices:         id, type, assignedZones, state
        """
        key = "addr" if self.verbosity == 3 else "id"
        return natural_sort([d.info for d in self.device_objs], key)

    def update(self):
        """Update the Hub with its latest state data."""

        def populate_objects(
            obj_list, obj_key, obj_by_id, GeniusObject
        ) -> Tuple[List, Dict]:
            """Create the current list of GeniusHub objects (zones/devices)."""
            entities = []  # list of converted zones/devices
            key = "id" if self.api_version == 1 else obj_key
            for raw_json in obj_list:
                entity = obj_by_id.get(
                    raw_json[key], GeniusObject(raw_json[key], raw_json, self)
                )
                entity._data, entity._raw = None, raw_json
                entities.append(entity)
            return entities, {e.id: e for e in entities}

        if self.api_version == 1:
            self._sense_mode = None  # currently, no way to tell
        else:  # self.api_version == 3:
            manager = [z for z in self._zones if z["iID"] == 0][0]
            self._sense_mode = bool(manager["lOptions"] & ZONE_MODE.Other)

        # TODO: this looks dodgy: replacing rather than updating entities
        self.zone_objs, self.zone_by_id = populate_objects(
            self._zones, "iID", self.zone_by_id, GeniusZone
        )
        self.zone_by_name = {z.name: z for z in self.zone_objs}

        for zone in self.zone_objs:  # TODO: this need checking
            zone.device_objs = [
                d for d in self.device_objs if d.assigned_zone == zone.name
            ]
            zone.device_by_id = {d.id: d for d in zone.device_objs}

        self.device_objs, self.device_by_id = populate_objects(
            self._devices, "addr", self.device_by_id, GeniusDevice
        )

        old_issues = self.issues
        if self.api_version == 1:
            self.issues = self._issues
            self.version = self._version
        else:  # self.api_version == 3:
            self.issues = [
                GeniusIssue(raw_json, self.device_by_id).data
                for raw_json in self._issues
            ]
            self.version = {
                "hubSoftwareVersion": self._version,
                "earliestCompatibleAPI": "https://my.geniushub.co.uk/v1",
                "latestCompatibleAPI": "https://my.geniushub.co.uk/v1",
            }

        for issue in [i for i in self.issues if i not in old_issues]:
            _LOGGER.warning("An Issue has been found: %s", issue)
        for issue in [i for i in old_issues if i not in self.issues]:
            _LOGGER.info("An Issue is now resolved: %s", issue)

    async def reboot(self) -> None:
        """Reboot the hub."""
        # x.post("/v3/system/reboot", { username: e, password: t, json:{} })
        raise NotImplementedError


class GeniusHub(GeniusHubBase):
    """The class for a Genius Hub."""

    def __init__(
        self, hub_id, username=None, password=None, session=None, debug=False
    ) -> None:
        super().__init__(hub_id, username=username, debug=debug)

        self.genius_service = GeniusService(hub_id, username, password, session)
        self.request = self.genius_service.request

    async def update(self) -> None:
        """Update the Hub with its latest state data."""
        if self.genius_service.use_v1_api:
            (
                self._zones,
                self._devices,
                self._issues,
                self._version,
            ) = await asyncio.gather(
                *[
                    self.genius_service.request("GET", g)
                    for g in ("zones", "devices", "issues", "version")
                ]
            )

        else:  # self.api_version == 3:
            zones, data_manager, auth = await asyncio.gather(
                *[
                    self.genius_service.request("GET", g)
                    for g in ("zones", "data_manager", "auth/release")
                ]
            )

            self._zones = self._zones_via_v3_zones(zones)
            self._devices = self._devices_via_v3_data_mgr(data_manager)
            self._issues = self._issues_via_v3_zones(zones)
            self._version = auth["data"]["release"]

            self.uid = auth["data"]["UID"]

        super().update()  # now parse all the JSON


class GeniusTestHub(GeniusHubBase):
    """The test class for a Genius Hub - uses a test file."""

    def __init__(self, zones_json, device_json, debug=None) -> None:
        super().__init__("test_hub", username="test", debug=debug)
        _LOGGER.info("Using GeniusTestHub()")

        self._test_json["zones"] = zones_json
        self._test_json["devices"] = device_json

    async def update(self) -> None:
        """Update the Hub with its latest state data."""
        self._zones = self._test_json["zones"]
        self._devices = self._test_json["devices"]
        self._issues = self._issues_via_v3_zones({"data": self._zones})
        self._version = self._version_via_v3_zones({"data": self._zones})  # a hack

        super().update()  # now parse all the JSON
