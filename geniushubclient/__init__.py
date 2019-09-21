"""Python client library for the Genius Hub API.

   see: https://my.geniushub.co.uk/docs
   """
import asyncio
from datetime import datetime
from hashlib import sha256
import json
from typing import Dict, List  # Any, Optional, Set, Tuple

import logging
import re

import aiohttp

from .const import (
    ATTRS_DEVICE,
    ATTRS_ZONE,
    DEFAULT_TIMEOUT_V1,
    DEFAULT_TIMEOUT_V3,
    DEVICE_HASH_TO_TYPE,
    FOOTPRINT_MODES,
    HUB_SW_VERSIONS,
    IDAY_TO_DAY,
    IMODE_TO_MODE,
    ISSUE_DESCRIPTION,
    ISSUE_TEXT,
    ITYPE_TO_TYPE,
    MODE_TO_IMODE,
    STATE_ATTRS,
    TYPE_TO_ITYPE,
    ZONE_KIT,
    ZONE_MODE,
    ZONE_TYPE,
)

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

DEBUG_MODE = False

if DEBUG_MODE is True:
    import ptvsd  # pylint: disable=import-error

    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.debug("Waiting for debugger to attach...")
    ptvsd.enable_attach(address=("172.27.0.138", 5679), redirect_output=True)
    ptvsd.wait_for_attach()
    _LOGGER.debug("Debugger is attached!")


def natural_sort(dict_list, dict_key) -> List[Dict]:
    """Return a case-insensitively sorted list with '11' after '2-2'."""

    def _alphanum_key(k):
        return [
            int(c) if c.isdigit() else c.lower()
            for c in re.split("([0-9]+)", k[dict_key])
        ]

    return sorted(dict_list, key=_alphanum_key)


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


def _version_via_v3_auth(raw_json) -> str:
    """Extract Version from /v3/zones JSON."""
    return raw_json["data"]["release"]


def _version_via_v3_zones(raw_json) -> str:
    """Extract Version from /v3/zones JSON (a hack)."""
    build_date = datetime.strptime(raw_json["data"][0]["strBuildDate"], "%b %d %Y")

    for date_time_idx in HUB_SW_VERSIONS:
        if datetime.strptime(date_time_idx, "%b %d %Y") <= build_date:
            return HUB_SW_VERSIONS[date_time_idx]


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

        self._session = session if session else aiohttp.ClientSession()

        self.api_version = 3 if username or password else 1
        if self.api_version == 1:
            self._auth = None
            self._url_base = "https://my.geniushub.co.uk/v1/"
            self._headers = {"authorization": f"Bearer {hub_id}"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)
        else:  # self.api_version == 3
            sha = sha256()
            sha.update((username + password).encode("utf-8"))
            self._auth = aiohttp.BasicAuth(login=username, password=sha.hexdigest())
            self._url_base = f"http://{hub_id}:1223/v3/"
            self._headers = {"Connection": "close"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)

        self._verbose = 1

        self.issues = []
        self.version = self._sense_mode = None
        self._zones = self._devices = self._issues = self._version = None
        self._test_json = {}  # used with GeniusTestHub

        self.zone_by_id = self.device_by_id = {}
        self.zone_objs = self.zone_by_name = self.device_objs = None

    def __repr__(self) -> str:
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

        except aiohttp.ServerDisconnectedError as err:
            _LOGGER.debug(
                "_request(): ServerDisconnectedError (msg=%s), retrying.", err
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
        ):  # pylint: disable=invalid-name
            """Create the current list of GeniusHub objects (zones/devices)."""
            entities = []  # list of converted zones/devices
            key = "id" if self.api_version == 1 else obj_key
            for raw_json in obj_list:
                try:  # does the hub already know about this zone/device?
                    entity = obj_by_id[raw_json[key]]
                except KeyError:
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

        if self.api_version == 1:
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
        if self.api_version == 1:
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
        if self.api_version == 1:
            get_list = ["zones", "devices", "issues", "version"]
            self._zones, self._devices, self._issues, self._version = await asyncio.gather(
                *[self.request("GET", g) for g in get_list]
            )

        else:  # self.api_version == 3:
            get_list = ["zones", "data_manager", "auth/release"]
            zones, data_manager, auth = await asyncio.gather(
                *[self.request("GET", g) for g in get_list]
            )

            self._zones = _zones_via_v3_zones(zones)
            self._devices = _devices_via_v3_data_mgr(data_manager)
            self._issues = _issues_via_v3_zones(zones)
            self._version = _version_via_v3_auth(auth)

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


class GeniusObject:
    """The base class for any Genius object: Zone, Device or Issue."""

    def __init__(self, hub, object_attrs) -> None:
        self._hub = hub
        self._attrs = object_attrs

        self.data = self._raw = {}

    def __repr__(self) -> str:
        return json.dumps(
            {k: v for k, v in self.data.items() if k in self._attrs["summary_keys"]}
        )

    @property
    def info(self) -> Dict:
        """Return all information for the object."""
        if self._hub.verbosity == 3:
            return self._raw

        if self._hub.verbosity == 2:
            return self.data

        keys = self._attrs["summary_keys"]
        if self._hub.verbosity == 1:
            keys += self._attrs["detail_keys"]

        return {k: v for k, v in self.data.items() if k in keys}


class GeniusZone(GeniusObject):
    """The class for a Genius Zone."""

    def __init__(self, zone_id, raw_json, hub) -> None:
        super().__init__(hub, ATTRS_ZONE)

        self.id = zone_id  # pylint: disable=invalid-name

        self.device_objs = []
        self.device_by_id = {}

        self._convert(raw_json)

    def _convert(self, raw_json) -> None:
        """Convert a zone's v3 JSON to the v1 schema."""
        self._raw = raw_json
        if self._hub.api_version == 1:
            self.data = raw_json
            return

        def _is_occupied(node) -> bool:  # from web app v5.2.4
            """Occupancy vs Activity (code from app.js, search for 'occupancyIcon').

                R = occupancy not detected (valid in any mode)
                O = occupancy detected (valid in any mode)
                A = occupancy detected, sufficient to call for heat (iff in Sense/FP mode)

                l = null != i.settings.experimentalFeatures && i.settings.experimentalFeatures.timerPlus,
                p = parseInt(n.iMode) === e.zoneModes.Mode_Footprint || l,           # in FP/sense mode
                u = parseInt(n.iFlagExpectedKit) & e.equipmentTypes.Kit_PIR,         # has a PIR
                d = n.trigger.reactive && n.trigger.output,                          #
                c = parseInt(n.zoneReactive.fActivityLevel) || 0,
                s = t.isInFootprintNightMode(n),                                     # night time

                occupancyIcon() = p && u && d && !s ? a : c > 0 ? o : r

                Hint: the following returns "XX">> true ? "XX" : "YY"
            """
            # pylint: disable=invalid-name
            A = O = True  # noqa: E741
            R = False

            l = True  # noqa: E741                                         TODO: WIP
            p = node["iMode"] == ZONE_MODE.Footprint | l  # #                    Checked
            u = node["iFlagExpectedKit"] & ZONE_KIT.PIR  # #                     Checked
            d = node["trigger"]["reactive"] & node["trigger"]["output"]  # #     Checked
            c = node["zoneReactive"]["fActivityLevel"]  # # needs int()?   TODO: WIP
            s = node["objFootprint"]["bIsNight"]  # #                      TODO: WIP

            return A if p and u and d and (not s) else (O if c > 0 else R)

        def _timer_schedule(raw_json) -> Dict:
            root = {"weekly": {}}
            day = -1

            setpoints = raw_json["objTimer"]
            for idx, setpoint in enumerate(setpoints):
                tm_next = setpoint["iTm"]
                sp_next = setpoint["fSP"]
                if raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                    sp_next = bool(sp_next)

                if setpoint["iDay"] > day:
                    day += 1
                    node = root["weekly"][IDAY_TO_DAY[day]] = {}
                    node["defaultSetpoint"] = sp_next
                    node["heatingPeriods"] = []

                elif sp_next != node["defaultSetpoint"]:
                    tm_last = setpoints[idx + 1]["iTm"]
                    # reactive = self._hub._sense_mode & bool(setpoint.get("bReactive"))

                    node["heatingPeriods"].append(
                        {"end": tm_last, "start": tm_next, "setpoint": sp_next}
                    )

            return root

        def _footprint_schedule(raw_json) -> Dict:
            root = {"weekly": {}}
            day = -1

            setpoints = raw_json["objFootprint"]
            for idx, setpoint in enumerate(setpoints["lstSP"]):
                tm_next = setpoint["iTm"]
                sp_next = setpoint["fSP"]

                if setpoint["iDay"] > day:
                    day += 1
                    node = root["weekly"][IDAY_TO_DAY[day]] = {}
                    node["defaultSetpoint"] = setpoints["fFootprintAwaySP"]
                    node["heatingPeriods"] = []

                if sp_next != setpoints["fFootprintAwaySP"]:
                    if tm_next == setpoints["iFootprintTmNightStart"]:
                        tm_last = 86400  # 24 * 60 * 60
                    else:
                        tm_last = setpoints["lstSP"][idx + 1]["iTm"]

                    node["heatingPeriods"].append(
                        {"end": tm_last, "start": tm_next, "setpoint": sp_next}
                    )

            return root

        self.data = result = {}
        result["id"] = raw_json["iID"]
        result["name"] = raw_json["strName"]

        try:
            result["type"] = ITYPE_TO_TYPE[raw_json["iType"]]
            if raw_json["iType"] == ZONE_TYPE.TPI and raw_json["zoneSubType"] == 0:
                result["type"] = ITYPE_TO_TYPE[ZONE_TYPE.ControlOnOffPID]

            result["mode"] = IMODE_TO_MODE[raw_json["iMode"]]

            if raw_json["iType"] in [ZONE_TYPE.ControlSP, ZONE_TYPE.TPI]:
                if raw_json["activeTemperatureDevices"]:
                    result["temperature"] = raw_json["fPV"]
                result["setpoint"] = raw_json["fSP"]

            elif raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                result["setpoint"] = bool(raw_json["fSP"])

            if self._has_pir:
                if TYPE_TO_ITYPE[result["type"]] == ZONE_TYPE.ControlSP:
                    result["occupied"] = _is_occupied(raw_json)
                else:
                    result["_occupied"] = _is_occupied(raw_json)

            if raw_json["iType"] in [
                ZONE_TYPE.OnOffTimer,
                ZONE_TYPE.ControlSP,
                ZONE_TYPE.TPI,
            ]:
                result["override"] = {}
                result["override"]["duration"] = raw_json["iBoostTimeRemaining"]
                if raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                    result["override"]["setpoint"] = raw_json["fBoostSP"] != 0
                else:
                    result["override"]["setpoint"] = raw_json["fBoostSP"]

            result["schedule"] = {"timer": {}, "footprint": {}}  # for all zone types

            if raw_json["iType"] not in [
                ZONE_TYPE.Manager,
                ZONE_TYPE.Surrogate,
            ]:  # timer = {} if: Manager, Group
                result["schedule"]["timer"] = _timer_schedule(raw_json)

            if raw_json["iType"] in [ZONE_TYPE.ControlSP]:
                # footprint={...} iff: ControlSP, _even_ if no PIR, otherwise ={}
                result["schedule"]["footprint"] = _footprint_schedule(raw_json)
                result["_schedule"] = {
                    "footprint": {
                        "profile": FOOTPRINT_MODES[raw_json["objFootprint"]["iProfile"]]
                    }
                }

        except (
            AttributeError,
            LookupError,
            TypeError,
            UnboundLocalError,
            ValueError,
        ) as err:
            _LOGGER.exception(
                "Failed to fully convert Zone %s, message: %s.", result["id"], err
            )

    @property
    def _has_pir(self) -> bool:
        """Return True if the zone has a PIR (movement sensor)."""
        if self._hub.api_version == 1:
            return "occupied" in self.data
        return self._raw["iFlagExpectedKit"] & ZONE_KIT.PIR

    @property
    def name(self) -> str:
        """Return the name of the zone, which can change."""
        return self.data["name"]

    @property
    def devices(self) -> List:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        key = "addr" if self._hub.verbosity == 3 else "id"
        return natural_sort([d.info for d in self.device_objs], key)

    @property
    def issues(self) -> List:
        """Return a list of Issues known to the Zone."""
        raise NotImplementedError

    async def set_mode(self, mode):
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        allowed_modes = [ZONE_MODE.Off, ZONE_MODE.Override, ZONE_MODE.Timer]

        if self._has_pir:
            allowed_modes += [ZONE_MODE.Footprint]
        allowed_mode_strs = [IMODE_TO_MODE[i] for i in allowed_modes]

        if isinstance(mode, int) and mode in allowed_modes:
            mode_str = IMODE_TO_MODE[mode]
        elif isinstance(mode, str) and mode in allowed_mode_strs:
            mode_str = mode
            mode = MODE_TO_IMODE[mode_str]
        else:
            raise TypeError(f"Zone.set_mode(): mode='{mode}' isn't valid.")

        _LOGGER.debug(
            "Zone(%s).set_mode(mode=%s, mode_str='%s')...", self.id, mode, mode_str
        )

        if self._hub.api_version == 1:
            url = f"zones/{self.id}/mode"  # v1 API uses strings
            resp = await self._hub.request("PUT", url, data=mode_str)
        else:  # self._hub.api_version == 3
            url = (
                f"zone/{self.id}"
            )  # v3 API uses dicts  # TODO: check: is it PUT(POST?) vs PATCH
            resp = await self._hub.request("PATCH", url, data={"iMode": mode})

        if resp:  # for v1, resp = None?
            resp = resp["data"] if resp["error"] == 0 else resp
        _LOGGER.debug("Zone(%s).set_mode(): response = %s", self.id, resp)

    async def set_override(self, setpoint=None, duration=None):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        assert setpoint is not None or duration is not None

        _LOGGER.debug(
            "Zone(%s).set_override(setpoint=%s, duration=%s)...",
            self.id,
            setpoint,
            duration,
        )

        if self._hub.api_version == 1:
            url = f"zones/{self.id}/override"
            data = {"setpoint": setpoint, "duration": duration}
            resp = await self._hub.request("POST", url, data=data)
        else:  # self._hub.api_version == 3
            url = f"zone/{self.id}"
            data = {
                "iMode": ZONE_MODE.Boost,
                "fBoostSP": setpoint,
                "iBoostTimeRemaining": duration,
            }
            resp = await self._hub.request("PATCH", url, data=data)

        if resp:  # for v1, resp = None?
            resp = resp["data"] if resp["error"] == 0 else resp
        _LOGGER.debug("Zone(%s).set_override_temp(): response = %s", self.id, resp)


class GeniusDevice(GeniusObject):
    """The class for a Genius Device."""

    def __init__(self, device_id, raw_json, hub) -> None:
        super().__init__(hub, ATTRS_DEVICE)

        self.id = device_id  # pylint: disable=invalid-name

        self._convert(raw_json)

    def _convert(self, raw_json) -> None:
        """Convert a device's v3 JSON to the v1 schema."""
        self._raw = raw_json
        if self._hub.api_version == 1:
            self.data = raw_json
            return

        self.data = result = {}
        result["id"] = raw_json["addr"]

        try:
            node = raw_json["childValues"]
            if "hash" in node:
                result["type"] = DEVICE_HASH_TO_TYPE[node["hash"]["val"]]
            elif node["SwitchBinary"]["path"].count("/") == 3:
                result["type"] = f"Dual Channel Receiver - Channel {result['id'][-1]}"
            else:
                result["type"] = None

            result["assignedZones"] = [{"name": None}]
            if node["location"]["val"]:
                result["assignedZones"] = [{"name": node["location"]["val"]}]

            result["state"] = state = {}
            state.update(
                [(v, node[k]["val"]) for k, v in STATE_ATTRS.items() if k in node]
            )
            if "outputOnOff" in state:  # this one should be a bool
                state["outputOnOff"] = bool(state["outputOnOff"])

            result["_state"] = _state = {}
            for val in ["lastComms", "setback"]:
                if val in node:
                    _state[val] = node[val]["val"]
            if "WakeUp_Interval" in node:
                _state["wakeupInterval"] = node["WakeUp_Interval"]["val"]

            node = raw_json["childNodes"]["_cfg"]["childValues"]
            result["_config"] = _config = {}
            for val in ["max_sp", "min_sp", "sku"]:
                if val in node:
                    _config[val] = node[val]["val"]

        except (
            AttributeError,
            LookupError,
            TypeError,
            UnboundLocalError,
            ValueError,
        ) as err:
            _LOGGER.exception(
                "Failed to fully convert Device %s, message: %s.", result["id"], err
            )

    @property
    def type(self) -> str:
        """Return the type of the device, which can change."""
        return self.data["type"]

    @property
    def assigned_zone(self) -> object:
        """Return the primary assigned zone, which can change."""
        try:
            return self._hub.zone_by_name[self.data["assignedZones"][0]["name"]]
        except KeyError:
            return None
