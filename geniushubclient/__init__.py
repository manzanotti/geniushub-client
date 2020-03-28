"""Python client library for the Genius Hub API.

   see: https://my.geniushub.co.uk/docs
   """

import asyncio
import json
import logging
from datetime import datetime
from hashlib import sha256
from typing import Dict, List  # Any, Optional, Set, Tuple

import aiohttp

from .const import (
    DEFAULT_TIMEOUT_V1,
    DEFAULT_TIMEOUT_V3,
    HUB_SW_VERSIONS,
    ISSUE_DESCRIPTION,
    ISSUE_TEXT,
    ZONE_MODE,
)
import os
import sys

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(".")))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.realpath("."))
print(sys.path)
_LOGGER.warning("%s", sys.path)
try:
    from .zone import GeniusZone, natural_sort
    from .device import GeniusDevice
except ModuleNotFoundError:
    try:
        from ..zone import GeniusZone, natural_sort
        from ..device import GeniusDevice
    except ModuleNotFoundError:
        try:
            from . import GeniusZone, natural_sort
            from . import GeniusDevice
        except ImportError:
            import GeniusZone

# Debugging flags - all False for production releases
DEBUG_LOGGING = False
DEBUG_MODE = False

if DEBUG_LOGGING is True:
    _LOGGER.setLevel(logging.DEBUG)

if DEBUG_MODE is True:
    import ptvsd  # pylint: disable=import-error

    _LOGGER.warning("Waiting for debugger to attach...")
    ptvsd.enable_attach(address=("172.27.0.138", 5679), redirect_output=True)
    ptvsd.wait_for_attach()
    _LOGGER.debug("Debugger is attached!")


def _zones_via_v3_zones(raw_json) -> List[Dict]:
    """Extract Zones from /v3/zones JSON."""
    return raw_json["data"]


def _devices_via_v3_data_mgr(raw_json) -> List[Dict]:
    """Extract Devices from /v3/data_manager JSON."""
    result = []
    for site in [
        x for x in raw_json["data"]["childNodes"].values() if x["addr"] != "WeatherData"
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


def _version_via_v3_zones(raw_json) -> str:
    """Extract Version from /v3/zones JSON (a hack)."""
    build_date = datetime.strptime(raw_json["data"][0]["strBuildDate"], "%b %d %Y")

    for date_time_idx in HUB_SW_VERSIONS:
        if datetime.strptime(date_time_idx, "%b %d %Y") <= build_date:
            return HUB_SW_VERSIONS[date_time_idx]


class GeniusService:
    """Class that deals with all communication to the physical hub.

        Does no conversion of data, purely API calls
        """

    def __init__(self, hub_id, username=None, password=None, session=None) -> None:

        self._session = session if session else aiohttp.ClientSession()

        if username or password:  # use the v3 Api
            sha = sha256()
            sha.update((username + password).encode("utf-8"))
            self._auth = aiohttp.BasicAuth(login=username, password=sha.hexdigest())
            self._url_base = f"http://{hub_id}:1223/v3/"
            self._headers = {"Connection": "close"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
        else:
            self._auth = None
            self._url_base = "https://my.geniushub.co.uk/v1/"
            self._headers = {"authorization": f"Bearer {hub_id}"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)

    async def request(self, method, url, data=None):
        """Perform a request."""
        _LOGGER.debug("_request(method=%s, url=%s, data=%s)", method, url, data)

        http_method = {
            "GET": self._session.get,
            "PATCH": self._session.patch,
            "POST": self._session.post,
            "PUT": self._session.put,
        }.get(method)

        try:
            async with http_method(
                self._url_base + url,
                auth=self._auth,
                headers=self._headers,
                json=data,
                raise_for_status=True,
                timeout=self._timeout,
            ) as resp:
                response = await resp.json(content_type=None)

        except aiohttp.ServerDisconnectedError as exc:
            _LOGGER.debug(
                "_request(): ServerDisconnectedError (msg=%s), retrying.", exc
            )
            async with http_method(
                self._url_base + url,
                auth=self._auth,
                headers=self._headers,
                json=data,
                raise_for_status=True,
                timeout=self._timeout,
            ) as resp:
                response = await resp.json(content_type=None)

        if method != "GET":
            _LOGGER.debug("_request(): response=%s", response)
        return response

    @property
    def use_v1_api(self) -> bool:
        """Make a fake docstring."""
        return self._auth is None


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
        """Make a fake docstring."""
        return json.dumps(self.version)

    @property
    def verbosity(self) -> int:
        """Get/Set the level of detail."""
        return self._verbose

    @verbosity.setter
    def verbosity(self, value):
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

    async def _update(self):
        """Update the Hub with its latest state data."""

        def populate_objects(
            obj_list, obj_key, obj_by_id, ObjectClass
        ) -> List:  # pylint: disable=invalid-name
            """Create the current list of GeniusHub objects (zones/devices)."""
            entities = []  # list of converted zones/devices
            key = "id" if self.genius_service.use_v1_api else obj_key
            for raw_json in obj_list:
                try:  # does the hub already know about this zone/device?
                    entity = obj_by_id[raw_json[key]]
                except KeyError:  # this is a new zone/device
                    entity = ObjectClass(raw_json[key], raw_json, self)
                else:
                    entity._convert(raw_json)  # pylint: disable=protected-access
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
            _LOGGER.info("An Issue is now resolved: %s", issue)

    async def update(self):
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

            self._zones = _zones_via_v3_zones(zones)
            self._devices = _devices_via_v3_data_mgr(data_manager)
            self._issues = _issues_via_v3_zones(zones)
            self._version = auth["data"]["release"]

            self.uid = auth["data"]["UID"]

        await self._update()  # now convert all the raw JSON

    async def reboot(self):
        """Reboot the hub."""
        # x.post("/v3/system/reboot", { username: e, password: t, json:{} })
        raise NotImplementedError


class GeniusTestHub(GeniusHub):
    """The test class for a Genius Hub - uses a test file."""

    def __init__(self, zones_json, device_json, session=None, debug=None) -> None:
        super().__init__(
            "test_hub", username="test", password="xx", session=session, debug=debug
        )
        _LOGGER.info("Using GeniusTestHub()")

        self._test_json["zones"] = zones_json
        self._test_json["devices"] = device_json

    async def update(self):
        """Update the Hub with its latest state data."""
        self._zones = self._test_json["zones"]
        self._devices = self._test_json["devices"]
        self._issues = _issues_via_v3_zones({"data": self._zones})
        self._version = _version_via_v3_zones({"data": self._zones})  # a hack

        await self._update()  # now convert all the raw JSON
