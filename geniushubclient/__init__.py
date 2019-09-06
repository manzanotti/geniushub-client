"""Python client library for the Genius Hub API.

   see: https://my.geniushub.co.uk/docs
   """
from datetime import datetime
from hashlib import sha256
import json
from typing import Dict, Optional, List  # Any, Set, Tuple

import logging
import re

import aiohttp

from .const import (
    ATTRS_DEVICE,
    ATTRS_ZONE,
    STATE_ATTRS,
    DEFAULT_TIMEOUT_V1,
    DEFAULT_TIMEOUT_V3,
    HUB_SW_VERSIONS,
    ITYPE_TO_TYPE,
    IMODE_TO_MODE,
    MODE_TO_IMODE,
    IDAY_TO_DAY,
    ISSUE_TEXT,
    ISSUE_DESCRIPTION,
    ZONE_TYPES,
    ZONE_MODES,
    KIT_TYPES,
)

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)

# pylint3 --max-line-length=100
# pylint: disable=fixme, too-many-branches, too-many-locals, too-many-statements


def natural_sort(dict_list, dict_key) -> List[Dict]:
    """Return a case-insensitively sorted list, with '11' after '2-2'."""
    # noqa; pylint: disable=missing-docstring, multiple-statements
    def alphanum_key(k):
        return [
            int(c) if c.isdigit() else c.lower()
            for c in re.split("([0-9]+)", k[dict_key])
        ]

    return sorted(dict_list, key=alphanum_key)


def _zones_via_zones_v3(raw_json) -> List:
    """Extract Zones from /v3/zones JSON."""
    return raw_json["data"]


def _devices_via_data_mgr_v3(raw_json) -> List:
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


def _issues_via_zones_v3(raw_json) -> List:
    """Extract Issues from /v3/zones JSON."""
    result = []
    for zone in raw_json["data"]:
        for issue in zone["lstIssues"]:
            if "data" not in issue:  # issues only have this data if there's a device?
                issue["data"] = {}
            issue["data"]["location"] = zone["strName"]
            # sue['data']['nodeType'] = hub.device_by_id[zone['data']['nodeID']].data['type']
            result.append(issue)
    return result


def _version_via_zones_v3(raw_json) -> Dict:
    """Extract Version from /v3/zones JSON."""
    build_date = datetime.strptime(raw_json["data"][0]["strBuildDate"], "%b %d %Y")

    for date_time_idx in HUB_SW_VERSIONS:
        if datetime.strptime(date_time_idx, "%b %d %Y") <= build_date:
            result = {"hubSoftwareVersion": HUB_SW_VERSIONS[date_time_idx]}
            break
    return result


class GeniusHub:  # pylint: disable=too-many-instance-attributes
    """The class for a connection to a Genius Hub."""

    # pylint: disable=too-many-arguments
    def __init__(
        self, hub_id, username=None, password=None, session=None, debug=False
    ) -> None:
        if debug is True:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("Debug mode is explicitly enabled.")
        else:
            _LOGGER.debug(
                "Debug mode is not explicitly enabled "
                "(but may be enabled elsewhere)."
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

        self.issues = self.version = None
        self._zones = self._devices = self._issues = None
        self._test_json = {}  # used with GeniusTestHub

        self.zone_objs = []
        self.zone_by_id = {}
        self.zone_by_name = {}

        self.device_by_id = {}
        self.device_objs = []

        self.issue_objs = []

    def __repr__(self) -> str:
        return json.dumps(self.info)

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
                f"{value} is not valid for verbosity. The permissible range is (0-3)."
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
                json=data,
                headers=self._headers,
                auth=self._auth,
                timeout=self._timeout,
                raise_for_status=True,
            ) as resp:
                response = await resp.json(content_type=None)
            # await self._session.close()

        except aiohttp.ServerDisconnectedError as err:
            _LOGGER.debug(
                "_request(): ServerDisconnectedError (msg=%s), retrying.", err
            )
            async with http_method(
                self._url_base + url,
                json=data,
                headers=self._headers,
                auth=self._auth,
                timeout=self._timeout,
                raise_for_status=True,
            ) as resp:
                response = await resp.json(content_type=None)

        if method != "GET":
            _LOGGER.debug("_request(): response=%s", response)
        return response

    @property
    def info(self) -> Dict:
        """Return all information for the hub."""
        # x.get("/v3/auth/test", { username: e, password: t, timeout: n })
        return self.version

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

        def _convert_issue(raw_dict) -> Dict:
            """Convert a issues's v3 JSON to the v1 schema."""
            _LOGGER.debug("Found an (v3) Issue: %s)", raw_dict)

            description = ISSUE_DESCRIPTION.get(raw_dict["id"], raw_dict["id"])
            level = ISSUE_TEXT.get(raw_dict["level"], str(raw_dict["level"]))

            if "{zone_name}" in description:
                zone_name = raw_dict["data"]["location"]
            if "{device_type}" in description:
                device_type = self.device_by_id[raw_dict["data"]["nodeID"]].data["type"]

            if "{zone_name}" in description and "{device_type}" in description:
                description = description.format(
                    zone_name=zone_name, device_type=device_type
                )
            elif "{zone_name}" in description:
                description = description.format(zone_name=zone_name)
            elif "{device_type}" in description:
                description = description.format(device_type=device_type)

            return {"description": description, "level": level}

        for raw_zone in self._zones:
            key = "id" if self.api_version == 1 else "iID"
            try:  # does the hub already know about this zone?
                zone = self.zone_by_id[raw_zone[key]]
            except KeyError:
                zone = GeniusZone(raw_zone, self)

                self.zone_objs.append(zone)
                self.zone_by_id[zone.data["id"]] = zone
                self.zone_by_name[zone.data["name"]] = zone

        for raw_device in self._devices:
            key = "id" if self.api_version == 1 else "addr"
            try:  # does the Hub already know about this device?
                device = self.device_by_id[raw_device[key]]
            except KeyError:
                device = GeniusDevice(raw_device, self)

                self.device_objs.append(device)
                self.device_by_id[device.data["id"]] = device

            zone_name = device.data["assignedZones"][0]["name"]
            if zone_name:
                zone = self.zone_by_name[zone_name]
                try:  # does the parent Zone already know about this device?
                    device = zone.device_by_id[
                        device.data["id"]
                    ]  # TODO: what happends if None???
                except KeyError:
                    zone.device_objs.append(device)
                    zone.device_by_id[device.data["id"]] = device

        if self.api_version == 1:
            self.issues = self._issues
        else:
            self.issues = [_convert_issue(raw_issue) for raw_issue in self._issues]

    async def update(self):
        """Update the Hub with its latest state data."""
        if self.api_version == 1:
            self._zones = await self.request("GET", "zones")
            self._devices = await self.request("GET", "devices")
            self._issues = await self.request("GET", "issues")
            self.version = await self.request("GET", "version")

        else:  # self.api_version == 3:
            self._zones = _zones_via_zones_v3(await self.request("GET", "zones"))
            self._devices = _devices_via_data_mgr_v3(
                await self.request("GET", "data_manager")
            )
            self._issues = _issues_via_zones_v3({"data": self._zones})
            self.version = _version_via_zones_v3({"data": self._zones})

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
        self._issues = _issues_via_zones_v3({"data": self._zones})
        self.version = _version_via_zones_v3({"data": self._zones})

        await self._update()  # now convert all the raw JSON


class GeniusObject:  # pylint: disable=too-few-public-methods, too-many-instance-attributes
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

        if self._hub.verbosity == 2:  # probably same as verbosity == 1:
            # return {k: v for k, v in self.data.items() if k[:1] != '_' and
            #         k not in ['device_objs', 'device_by_id', 'assigned_zone']}
            return self.data

        keys = self._attrs["summary_keys"]
        if self._hub.verbosity == 1:
            keys += self._attrs["detail_keys"]

        return {k: v for k, v in self.data.items() if k in keys}


class GeniusZone(GeniusObject):
    """The class for a Genius Zone."""

    def __init__(self, raw_dict, hub) -> None:
        super().__init__(hub, ATTRS_ZONE)

        self._raw = raw_dict
        self.data = raw_dict if self._hub.api_version == 1 else self._convert(raw_dict)

        self.id = self.data["id"]  # pylint: disable=invalid-name

        self.device_objs = []
        self.device_by_id = {}

    def _convert(self, raw_dict) -> Dict:  # pylint: disable=no-self-use
        """Convert a zone's v3 JSON to the v1 schema."""
        result = {}
        result["id"] = raw_dict["iID"]
        result["name"] = raw_dict["strName"]
        result["type"] = ITYPE_TO_TYPE[raw_dict["iType"]]
        result["mode"] = IMODE_TO_MODE[raw_dict["iMode"]]

        if raw_dict["iType"] in [ZONE_TYPES.ControlSP, ZONE_TYPES.TPI]:
            if not (
                raw_dict["iType"] == ZONE_TYPES.TPI
                and not raw_dict["activeTemperatureDevices"]
            ):
                result["temperature"] = raw_dict["fPV"]
            result["setpoint"] = raw_dict["fSP"]

        elif raw_dict["iType"] == ZONE_TYPES.OnOffTimer:
            result["setpoint"] = bool(raw_dict["fSP"])

        # pylint: disable=pointless-string-statement
        """Occupancy vs Activity (code from ap.js, search for occupancyIcon).

            The occupancy symbol is affected by the mode of the zone:
                Greyed out: no occupancy detected
                Hollow icon: occupancy detected
            In Footprint Mode:
                Solid icon: occupancy detected; sufficient to call for heat

            l = parseInt(i.iFlagExpectedKit) & e.equipmentTypes.Kit_PIR          # has a PIR
            u = parseInt(i.iMode) === e.zoneModes.Mode_Footprint                 # in Footprint mode
            d = null != (s=i.zoneReactive) ? s.bTriggerOn: void 0                # ???
            c = parseInt(i.iActivity) || 0                                       # ???
            o = t.isInFootprintNightMode(i)                                      # night time

            u && l && d && !o ? n : c > 0 ? r : a

            n = "<i class='icon hg-icon-full-man   occupancy active' data-clickable='true'></i>"
            r = "<i class='icon hg-icon-hollow-man occupancy active' data-clickable='true'></i>"
            a = "<i class='icon hg-icon-full-man   occupancy'        data-clickable='false'></i>"
        """
        if raw_dict["iFlagExpectedKit"] & KIT_TYPES.PIR:
            # pylint: disable=invalid-name
            u = raw_dict["iMode"] == ZONE_MODES.Footprint
            d = raw_dict["zoneReactive"]["bTriggerOn"]
            c = raw_dict["iActivity"] or 0
            o = raw_dict["objFootprint"]["bIsNight"]
            result["occupied"] = (
                True if u and d and (not o) else True if c > 0 else False
            )

        if raw_dict["iType"] in [
            ZONE_TYPES.OnOffTimer,
            ZONE_TYPES.ControlSP,
            ZONE_TYPES.TPI,
        ]:
            result["override"] = {}
            result["override"]["duration"] = raw_dict["iBoostTimeRemaining"]
            if raw_dict["iType"] == ZONE_TYPES.OnOffTimer:
                result["override"]["setpoint"] = raw_dict["fBoostSP"] != 0
            else:
                result["override"]["setpoint"] = raw_dict["fBoostSP"]

        # pylint: disable=pointless-string-statement
        """Schedules - What is known:
             timer={} if: Manager
             footprint={...} iff: ControlSP, _even_ if no PIR, otherwise ={}
        """
        result["schedule"] = {"timer": {}, "footprint": {}}

        # Timer schedule...
        if raw_dict["iType"] != ZONE_TYPES.Manager:
            root = result["schedule"]["timer"] = {"weekly": {}}
            day = -1

            try:  # TODO: confirm creation of zone despite exception
                setpoints = raw_dict["objTimer"]
                for idx, setpoint in enumerate(setpoints):
                    tm_next = setpoint["iTm"]
                    sp_next = setpoint["fSP"]
                    if raw_dict["iType"] == ZONE_TYPES.OnOffTimer:
                        sp_next = bool(sp_next)

                    if setpoint["iDay"] > day:
                        day += 1
                        node = root["weekly"][IDAY_TO_DAY[day]] = {}
                        node["defaultSetpoint"] = sp_next
                        node["heatingPeriods"] = []

                    elif sp_next != node["defaultSetpoint"]:
                        tm_last = setpoints[idx + 1]["iTm"]
                        node["heatingPeriods"].append(
                            {"end": tm_last, "start": tm_next, "setpoint": sp_next}
                        )

            except (
                AttributeError,
                LookupError,
                TypeError,
                NameError,
                ValueError,
            ) as err:
                _LOGGER.exception(
                    "Failed to convert Timer schedule for Zone %s, message: %s"
                    "Note that the Zone's Timer schedule may not be correct.",
                    result["id"],
                    err,
                )

        # Footprint schedule...
        if raw_dict["iType"] in [ZONE_TYPES.ControlSP]:
            root = result["schedule"]["footprint"] = {"weekly": {}}
            day = -1

            try:  # TODO: confirm creation of zone despite exception
                setpoints = raw_dict["objFootprint"]
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

            except (
                AttributeError,
                LookupError,
                TypeError,
                UnboundLocalError,
                ValueError,
            ) as err:
                _LOGGER.exception(
                    "Failed to convert Footprint schedule for Zone %s, message: %s. "
                    "Note that the Zone's Footprint schedule may not be correct.",
                    result["id"],
                    err,
                )

        return result

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
        allowed_modes = [ZONE_MODES.Off, ZONE_MODES.Override, ZONE_MODES.Timer]

        if hasattr(self, "occupied"):  # has a PIR (movement sensor)
            allowed_modes += [ZONE_MODES.Footprint]
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
        else:  # self._hub.api_version == 1
            url = (
                f"zone/{self.id}"
            )  # v3 API uses dicts  # TODO: check: is it PUT(POST?) vs PATCH
            resp = await self._hub.request("PATCH", url, data={"iMode": mode})

        if resp:  # for v1, resp = None?
            resp = resp["data"] if resp["error"] == 0 else resp
        _LOGGER.debug("Zone(%s).set_mode(): response = %s", self.id, resp)

    async def set_override(self, setpoint=None, duration=3600):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        setpoint = (
            setpoint if setpoint is not None else self.setpoint
        )  # pylint: disable=no-member

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
        else:
            url = f"zone/{self.id}"
            data = {
                "iMode": ZONE_MODES.Boost,
                "fBoostSP": setpoint,
                "iBoostTimeRemaining": duration,
            }
            resp = await self._hub.request("PATCH", url, data=data)

        if resp:  # for v1, resp = None?
            resp = resp["data"] if resp["error"] == 0 else resp
        _LOGGER.debug("Zone(%s).set_override_temp(): response = %s", self.id, resp)


class GeniusDevice(GeniusObject):  # pylint: disable=too-few-public-methods
    """The class for a Genius Device."""

    def __init__(self, raw_dict, hub) -> None:
        super().__init__(hub, ATTRS_DEVICE)

        self._raw = raw_dict
        self.data = raw_dict if self._hub.api_version == 1 else self._convert(raw_dict)

        self.id = self.data["id"]  # pylint: disable=invalid-name

    def _convert(self, raw_dict) -> Dict:  # pylint: disable=no-self-use
        """Convert a device's v3 JSON to the v1 schema."""

        def _check_fingerprint(node, device) -> Optional[str]:
            """Check the device type against its 'fingerprint'."""
            # pylint: disable=invalid-name
            fp = None

            if "Battery" in node and "SwitchBinary" not in node:
                if "Motion" in node:  # or 'Tamper': PH-WRS-B
                    fp = "Room Sensor"
                elif "setback" in node:  # DA-WRV-C (else DA-WRV-B)
                    fp = "Genius Valve" if "TEMPERATURE" in node else "Radiator Valve"
                else:  # DA-WRT-C (else HO-WRT-B)
                    fp = "Room Thermostat" if "Indicator" in node else "Room Thermostat"

            elif "SwitchBinary" in node and "Battery" not in node:  # TODO: HO-SCR-C ?
                if "SwitchAllMode" in node:  # PH-PLG-C
                    fp = "Smart Plug"
                elif "TEMPERATURE" in node:  # HO-ESW-D
                    fp = "Electric Switch"
                elif node["SwitchBinary"]["path"].count("/") == 3:
                    fp = f"Dual Channel Receiver - Channel {device['id'][-1]}"
                else:  # HO-DCR-C
                    fp = "Dual Channel Receiver"

            if not device["_type"] or fp != device["_type"][:21]:
                msg = f"Device {device['id']} (SKU={device['_sku']}): assigned type "

                if fp is None:  # no/invalid device fingerprint!
                    msg += f"('{device['_type']}') is ignored as no fingerprint!"
                    _LOGGER.warning(msg)
                elif not device["_type"]:
                    msg += f"only via its fingerprint ('{fp}')."
                    _LOGGER.debug(msg)
                else:
                    msg += f"('{device['_type']}') doesn't match fingerprint ('{fp}')!"
                    _LOGGER.warning(msg)
                    fp = device["_type"]  # prefer type over fingerprint

            return fp

        result = {}

        result["id"] = raw_dict["addr"]  # 1. Set id (addr)

        node = raw_dict["childNodes"]["_cfg"]["childValues"]
        result["_type"] = node["name"]["val"] if node else None
        result["_sku"] = node["sku"]["val"] if node else None

        node = raw_dict["childValues"]
        device_type = _check_fingerprint(node, result)
        result["type"] = device_type if device_type else "Unrecognised Device"

        result["assignedZones"] = [{"name": None}]  # 3. Set assignedZones...
        if node["location"]["val"]:
            result["assignedZones"] = [{"name": node["location"]["val"]}]

        result["state"] = state = {}  # 4. Set state...

        # the following order should be preserved
        state.update([(v, node[k]["val"]) for k, v in STATE_ATTRS.items() if k in node])
        if "outputOnOff" in state:  # this one should be a bool
            state["outputOnOff"] = bool(state["outputOnOff"])

        return result

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
