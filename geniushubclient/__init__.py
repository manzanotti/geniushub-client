"""Python client library for the Genius Hub API.

   see: https://my.geniushub.co.uk/docs
   """
# import asyncio
from hashlib import sha256
from typing import Any, Dict, List, Set, Tuple, Optional

import logging
import re

import aiohttp

from .const import (
    ATTRS_DEVICE, ATTRS_ISSUE, ATTRS_ZONE,
    DEFAULT_TIMEOUT_V1, DEFAULT_TIMEOUT_V3,
    ITYPE_TO_TYPE, IMODE_TO_MODE, MODE_TO_IMODE, IDAY_TO_DAY,
    LEVEL_TO_TEXT, DESCRIPTION_TO_TEXT,
    ZONE_TYPES, ZONE_MODES, KIT_TYPES)

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.WARNING)

# pylint3 --max-line-length=120
# pylint: disable=fixme, missing-docstring
# pylint: disable=no-member, protected-access
# pylint: disable=too-many-instance-attributes, too-few-public-methods
# pylint: disable=too-many-locals, too-many-branches, too-many-statements
# pylint: disable=too-many-arguments


def natural_sort(dict_list, dict_key):
    def alphanum_key(k): return [int(c) if c.isdigit() else c.lower()            # noqa; pylint: disable=multiple-statements
                                 for c in re.split('([0-9]+)', k[dict_key])]
    return sorted(dict_list, key=alphanum_key)


def _without_keys(dict_obj, keys) -> dict:
    _info = dict(dict_obj)
    _info = {k: v for k, v in _info.items() if k[:1] != '_'}
    _info = {k: v for k, v in _info.items() if k not in keys}
    return _info


def _get_zones_from_zones_v3(raw_json) -> list:
    """Extract Zones from /v3/zones JSON."""
    return raw_json


def _get_devices_from_data_manager(raw_json) -> list:
    """Extract Devices from /v3/data_manager JSON."""
    result = []
    for site in [x for x in raw_json['childNodes'].values()
                 if x['addr'] != 'WeatherData']:
        for device in [x for x in site['childNodes'].values()
                       if x['addr'] != '1']:
            result.append(device)
            for channel in [x for x in device['childNodes'].values()
                            if x['addr'] != '_cfg']:
                temp = dict(channel)
                temp['addr'] = '{}-{}'.format(device['addr'], channel['addr'])
                result.append(temp)

    return result


def _get_devices_from_zones_v3(raw_json) -> list:
    """Extract Devices from /v3/zones JSON."""
    result = []
    for zone in raw_json:
        for device in [x for x in zone['nodes'].values()
                       if x['addr'] not in ['WeatherData']]:  # ['1', 'WeatherData']
            result.append(device)

    return result


def _get_issues_from_zones_v3(raw_json) -> list:
    """Extract Issues from /v3/zones JSON."""
    result = []
    for zone in raw_json:
        for issue in zone['lstIssues']:
            # TODO: might better be as an ID +/- convert to a comprehension
            issue['_zone_name'] = zone['strName']  # some issues wont have this data
            result.append(issue)

    return result


class GeniusHubClient(object):
    """The class for a connection to a Genius Hub."""
    def __init__(self, hub_id, username=None, password=None, session=None,
                 debug=False) -> None:
        if debug is True:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("Debug mode is explicitly enabled.")
        else:
            _LOGGER.debug("Debug mode is not explicitly enabled "
                          "(but may be enabled elsewhere).")

        # use existing session if one was provided
        self._session = session if session else aiohttp.ClientSession()

        # if no credentials, then hub_id is a token for v1 API
        self._api_v1 = not (username or password)
        if self._api_v1:
            self._auth = None
            self._url_base = 'https://my.geniushub.co.uk/v1/'
            self._headers = {'authorization': "Bearer " + hub_id}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)
        else:  # using API ver3
            sha = sha256()
            sha.update((username + password).encode('utf-8'))
            self._auth = aiohttp.BasicAuth(
                login=username, password=sha.hexdigest())
            self._url_base = 'http://{}:1223/v3/'.format(hub_id)
            self._headers = {"Connection": "close"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)

        self._verbose = 1
        hub_id = hub_id[:8] + "..." if len(hub_id) > 20 else hub_id

        self.hub = GeniusHub(self, {'id': hub_id})

    @property
    def verbosity(self) -> int:
        return self._verbose

    @verbosity.setter
    def verbosity(self, value):
        if value >= 0 and value <= 3:
            self._verbose = value
        else:
            raise ValueError("'{}' is not valid for verbosity. "
                             "The permissible range is (0-3).".format(value))


class GeniusObject(object):
    """The base class for Genius Hub, Zone & Device."""
    def __init__(self, client, obj_dict, hub=None, assignedZone=None) -> None:
        self.id = None  # avoids no-member,                                      # noqa; pylint: disable=invalid-name

        self.__dict__.update(obj_dict)  # create self.id, etc.

        self._client = client
        self._api_v1 = client._api_v1

        if isinstance(self, GeniusHub):
            self.zone_objs = []
            self.zone_by_id = {}
            self.zone_by_name = {}

            self.device_objs = []
            self.device_by_id = {}

        elif isinstance(self, GeniusZone):
            self.hub = hub

            self.device_objs = []
            self.device_by_id = {}

        elif isinstance(self, GeniusDevice):
            self.hub = hub
            self.assignedZone = assignedZone                                     # noqa; pylint: disable=invalid-name

    def _convert_zone(self, raw_dict) -> dict:
        """Convert a v3 zone's dict/json to the v1 schema."""
        if self._api_v1:
            return raw_dict

        # _LOGGER.debug("_convert_zone(): raw_dict=%s", raw_dict)

        result = {}
        result['id'] = raw_dict['iID']
        result['type'] = ITYPE_TO_TYPE[raw_dict['iType']]
        result['name'] = raw_dict['strName']

        if raw_dict['iType'] in [ZONE_TYPES.ControlSP, ZONE_TYPES.TPI]:
            if not (raw_dict['iType'] == ZONE_TYPES.TPI and
                    not raw_dict['activeTemperatureDevices']):
                result['temperature'] = raw_dict['fPV']
            result['setpoint'] = raw_dict['fSP']

        if raw_dict['iType'] == ZONE_TYPES.OnOffTimer:
            result['setpoint'] = raw_dict['fSP'] != 0

        result['mode'] = IMODE_TO_MODE[raw_dict['iMode']]

        # pylint: disable=pointless-string-statement
        """Occupancy vs Activity (code from ap.js, search for occupancyIcon).

            The occupancy symbol is affected by the mode of the zone:
                Greyed out: no occupancy detected
                Hollow icon: occupancy detected
            In Footprint Mode:
                Solid icon: occupancy detected; sufficient to call for heat

        l = parseInt(i.iFlagExpectedKit) & e.equipmentTypes.Kit_PIR              # has a PIR
        u = parseInt(i.iMode) === e.zoneModes.Mode_Footprint                     # in Footprint mode
        d = null != (s=i.zoneReactive) ? s.bTriggerOn: void 0                    # ???
        c = parseInt(i.iActivity) || 0                                           # ???
        o = t.isInFootprintNightMode(i)                                          # night time

        u && l && d && !o ? n : c > 0 ? r : a

        n = "<i class='icon hg-icon-full-man   occupancy active' data-clickable='true'></i>"
        r = "<i class='icon hg-icon-hollow-man occupancy active' data-clickable='true'></i>"
        a = "<i class='icon hg-icon-full-man   occupancy'        data-clickable='false'></i>"
        """
        if raw_dict['iFlagExpectedKit'] & KIT_TYPES.PIR:
            # pylint: disable=invalid-name
            u = raw_dict['iMode'] == ZONE_MODES.Footprint
            d = raw_dict['zoneReactive']['bTriggerOn']
            c = raw_dict['iActivity']                                            # noqa: ignore=F841; pylint: disable=unused-variable
            o = raw_dict['objFootprint']['bIsNight']
            result['occupied'] = u and d and not o  # and c > 0

        if raw_dict['iType'] in [ZONE_TYPES.OnOffTimer,
                                 ZONE_TYPES.ControlSP,
                                 ZONE_TYPES.TPI]:
            result['override'] = {}
            result['override']['duration'] = raw_dict['iBoostTimeRemaining']
            if raw_dict['iType'] == ZONE_TYPES.OnOffTimer:
                result['override']['setpoint'] = (raw_dict['fBoostSP'] != 0)
            else:
                result['override']['setpoint'] = raw_dict['fBoostSP']

        # pylint: disable=pointless-string-statement
        """Schedules - What is known:
             timer={} if: Manager
             footprint={} if: Manager, OnOffTimer, TPI
             footprint={...} if: ControlSP, _even_ if no PIR
        """
        result['schedule'] = {'timer': {}, 'footprint': {}}

        try:
            if raw_dict['iType'] != ZONE_TYPES.Manager:
                root = result['schedule']['timer'] = {'weekly': {}}

                day = -1
                for setpoint in raw_dict['objTimer']:
                    next_time = setpoint['iTm']
                    next_temp = setpoint['fSP']
                    if raw_dict['iType'] == ZONE_TYPES.OnOffTimer:
                        next_temp = bool(setpoint['fSP'])

                    if next_time == -1:  # i.e. default SP entry
                        day += 1
                        node = root['weekly'][IDAY_TO_DAY[day]] = {}
                        node['defaultSetpoint'] = default_temp = next_temp
                        node['heatingPeriods'] = []

                    elif setpoint_temp != default_temp:                          # noqa: disable=F821; pylint: disable=used-before-assignment
                        node['heatingPeriods'].append({
                            'end': next_time,
                            'start': setpoint_time,                              # noqa: disable=F821; pylint: disable=used-before-assignment
                            'setpoint': setpoint_temp                            # noqa: disable=F821; pylint: disable=used-before-assignment
                        })

                    setpoint_time = next_time
                    setpoint_temp = next_temp

        except UnboundLocalError:
            _LOGGER.warning("Failed to convert Timer schedule for Zone %s",
                            result['id'])

        except Exception as err:
            _LOGGER.exception("Failed to convert Timer schedule for Zone %s, "
                              "message: %s", result['id'], err)

        try:
            if raw_dict['iType'] in [ZONE_TYPES.ControlSP]:
                root = result['schedule']['footprint'] = {'weekly': {}}

                away_temp = raw_dict['objFootprint']['fFootprintAwaySP']
                night_temp = raw_dict['objFootprint']['fFootprintNightSP']
                night_start = raw_dict['objFootprint']['iFootprintTmNightStart']

                day = -1
                for setpoint in raw_dict['objFootprint']['lstSP']:
                    next_time = setpoint['iTm']
                    next_temp = setpoint['fSP']

                    if next_time == 0:  # i.e. start of day
                        day += 1
                        node = root['weekly'][IDAY_TO_DAY[day]] = {}
                        node['defaultSetpoint'] = away_temp
                        node['heatingPeriods'] = []

                    elif setpoint_temp != away_temp:
                        node['heatingPeriods'].append({
                            'end': next_time,
                            'start': setpoint_time,
                            'setpoint': setpoint_temp
                        })

                    if next_time == night_start:  # e.g. 11pm
                        node['heatingPeriods'].append({
                            'end': 86400,
                            'start': night_start,
                            'setpoint': night_temp
                        })

                    setpoint_time = next_time
                    setpoint_temp = next_temp

        except Exception as err:
            _LOGGER.exception("Failed to convert Footprint schedule for Zone %s, "
                              "message: %s", result['id'], err)

        return result

    def _convert_device(self, raw_dict) -> dict:
        """Convert a v3 device's dict/json to the v1 schema.

        Sets id, type, assignedZones and state.
        """
        if self._api_v1:
            return raw_dict

        # _LOGGER.debug("_convert_device(): raw_dict=%s", raw_dict)

        def _check_fingerprint(node, device):
            """Check the device type against its 'fingerprint'."""
            if 'SwitchBinary' in node:
                if 'TEMPERATURE' in node:
                    fingerprint = "Electric Switch"
                elif 'SwitchAllMode' in node:
                    fingerprint = "Smart Plug"
                else:
                    fingerprint = "Dual Channel Receiver"

            elif 'setback' in node:
                if 'TEMPERATURE' in node:
                    fingerprint = "Genius Valve"
                else:
                    fingerprint = "Radiator Valve"

            elif 'Motion' in node:
                fingerprint = "Room Sensor"

            elif 'Indicator' in node:
                fingerprint = "Room Thermostat"

            else:  # ... no/invalid device fingerprint!
                if device['type']:
                    _LOGGER.debug(
                        "Device %s, '%s': has no confirming fingerprint!",
                        device['id'], device['type'])
                else:
                    _LOGGER.error(
                        "Device %s: has no type, and no fingerprint!",
                        device['id'])
                return

            if not device['type']:
                device['type'] = fingerprint
                _LOGGER.warning(
                    "Device %s, '%s': typed only by its fingerprint!",
                    device['id'], device['type'])

            # elif (device['type'] == fingerprint or
            elif device['type'][:21] == fingerprint:  # "Dual Channel Receiver"
                _LOGGER.debug(
                    "Device %s, '%s': matches its fingerprint.",
                    device['id'], device['type'])

            else:  # device['type'] != device_type:
                _LOGGER.error(
                    "Device %s, '%s': doesn't match its fingerprint: '%s'!",
                    device['id'], device['type'], fingerprint)

        result = {}

        result['id'] = raw_dict['addr']  # 1. Set id (addr)
        result['type'] = None  # 2. Set type...

        node = raw_dict['childNodes']['_cfg']['childValues']
        if node:
            result['type'] = node['name']['val']
            result['_sku'] = node['sku']['val']

        node = raw_dict['childValues']
        # hack: find any Dual Channel Receiver(s), to 'force' that type
        if 'SwitchBinary' in node and result['type'] is None and \
                node['SwitchBinary']['path'].count('/') == 3:
            result['type'] = 'Dual Channel Receiver - Channel {}'.format(
                result['id'][-1])
            _LOGGER.debug(
                "Device %s, '%s': typed by its fingerprint (this is OK).",
                result['id'], result['type'])
        else:
            _check_fingerprint(node, result)  # ... confirm type, set if needed

        result['assignedZones'] = [{'name': None}]  # 3. Set assignedZone...
        if node['location']['val']:
            result['assignedZones'] = [{'name': node['location']['val']}]

        result['state'] = state = {}  # 4. Set state...

        MAP = {
            'SwitchBinary': 'outputOnOff',  # #      DCCR/PLUG, RADR
            'Battery': 'batteryLevel',  # #          VALV/ROMT, RADR, ROMS
            'HEATING_1': 'setTemperature',  # #      VALV/ROMT, RADR
            'TEMPERATURE': 'measuredTemperature',  # VALV/ROMT, RADR, ROMS
            'LUMINANCE': 'luminance',  # #                            ROMS
            'Motion': 'occupancyTrigger'  # #                         ROMS
        }

        # the following order should be preserved
        state.update([(v, node[k]['val']) for k, v in MAP.items() if k in node])
        if 'SwitchBinary' in node:  # this one should be a bool
            state['outputOnOff'] = bool(node['SwitchBinary']['val'])

        return result

    def _convert_issue(self, raw_dict) -> dict:
        """Convert a v3 issues's dict/json to the v1 schema."""
        if self._api_v1:
            return raw_dict

        # _LOGGER.debug("_convert_issue(): raw_dict=%s", raw_dict)

        description = DESCRIPTION_TO_TEXT.get(raw_dict['id'], raw_dict)

        if '{zone_name}' in description and '{device_type}' in description:
            zone = raw_dict['data']['location']  # or: raw_dict['_zone_name']
            device = self.device_by_id[raw_dict['data']['nodeID']].type
            description = description.format(zone_name=zone, device_type=device)

        elif '{zone_name}' in description:
            # raw_dict['data'] is not avalable as no device?
            zone = raw_dict['_zone_name']
            description = description.format(zone_name=zone)

        elif '{device_type}' in description:
            device = self.device_by_id[raw_dict['data']['nodeID']].type
            description = description.format(device_type=device)

        level = LEVEL_TO_TEXT.get(raw_dict['level'], raw_dict['level'])

        return {'description': description, 'level': level}

    async def _request(self, method, url, data=None):
        _LOGGER.debug("_request(method=%s, url=%s, data=%s)", method, url, data)

        http_method = {
            "GET": self._client._session.get,
            "PATCH": self._client._session.patch,
            "POST": self._client._session.post,
            "PUT": self._client._session.put,
        }.get(method)

        try:
            async with http_method(
                self._client._url_base + url,
                json=data,
                headers=self._client._headers,
                auth=self._client._auth,
                timeout=self._client._timeout,
                raise_for_status=True
            ) as resp:
                response = await resp.json(content_type=None)

        # except concurrent.futures._base.TimeoutError as err:
        except aiohttp.client_exceptions.ServerDisconnectedError as err:
            _LOGGER.debug("_request(): ServerDisconnected, retrying (msg=%s)", err)
            _session = aiohttp.ClientSession()
            async with http_method(
                self._client._url_base + url,
                json=data,
                headers=self._client._headers,
                auth=self._client._auth,
                timeout=self._client._timeout,
                raise_for_status=True
            ) as resp:
                response = await resp.json(content_type=None)
            await _session.close()

        if method != 'GET':
            _LOGGER.debug("_request(): response=%s", response)
        return response

    def _subset_list(self, item_list_raw, convert_to_v1,
                     summary_keys, detail_keys) -> list:
        if self._client._verbose >= 3:
            return item_list_raw

        item_list = [convert_to_v1(i) for i in item_list_raw]

        if self._client._verbose >= 2:
            return item_list

        if self._client._verbose >= 1:
            keys = summary_keys + detail_keys
        else:
            keys = summary_keys

        result = [{k: item[k] for k in keys if k in item}
                  for item in item_list]

        return result

    def _subset_dict(self, item_dict_raw, convert_to_v1,
                     summary_keys, detail_keys):
        if self._client._verbose >= 3:
            return item_dict_raw

        item_dict = convert_to_v1(item_dict_raw)

        if self._client._verbose >= 2:
            return item_dict

        elif self._client._verbose >= 1:
            keys = summary_keys + detail_keys
        else:
            keys = summary_keys

        return {k: item_dict[k] for k in keys if k in item_dict}


class GeniusHub(GeniusObject):
    """The class for a Genius Hub."""
    # conn.post("/v3/system/reboot", { username: e, password: t, json:{} })
    # conn.get("/v3/auth/test", { username: e, password: t, timeout: n })

    def __init__(self, client, hub_dict) -> None:
        _LOGGER.info("GeniusHub()")
        super().__init__(client, hub_dict)

        self._info = {}  # Dict[str, Any] = {}
        self._zones = []  # List[dict] = []
        self._devices = []  # List[dict] = []
        self._issues = []  # List[dict] = []

        self._info_raw = None
        self._issues_raw = self._devices_raw = self._zones_raw = None

    async def update(self):
        """Update the Hub with its latest state data."""

        def _populate_zone(zone_raw):
            zone_dict = self._convert_zone(zone_raw)

            try:  # does the hub already know about this zone?
                zone = self.zone_by_id[zone_dict['id']]
            except KeyError:
                zone = GeniusZone(self._client, zone_dict, self)

                self.zone_by_id[zone.id] = zone
                self.zone_by_name[zone.name] = zone
                self.zone_objs.append(zone)
            else:
                _LOGGER.debug("Duplicate zone: %s!", zone.id)

            zone.__dict__.update(zone_dict)
            zone._info_raw = zone_raw

            return zone.id, zone

        def _populate_device(device_raw):
            device_dict = self._convert_device(device_raw)

            name = device_dict['assignedZones'][0]['name']
            zone = self.zone_by_name[name] if name else None

            try:  # does the Hub already know about this device?
                device = self.device_by_id[device_dict['id']]
            except KeyError:
                device = GeniusDevice(self._client, device_dict, self, zone)
                self.device_by_id[device.id] = device
                self.device_objs.append(device)
            else:
                _LOGGER.error("Duplicate device: %s!", device.id)

            if zone:
                try:  # does the parent Zone already know about this device?
                    device = zone.device_by_id[device_dict['id']]
                except KeyError:
                    zone.device_by_id[device.id] = device
                    zone.device_objs.append(device)
                else:
                    _LOGGER.error("Duplicate device: %s for zone: %s!",
                                  device.id, zone.id)

            device.__dict__.update(device_dict)
            device._info_raw = device_raw

            return device_dict['id'], device

        def _populate_issue(issue_raw):
            issue_dict = self._convert_issue(issue_raw)

            _LOGGER.debug("Found an Issue: %s)", issue_dict)

            return issue_dict['description'], None

        # these three must be executed in this order
        [_populate_zone(z) for z in await self._get_zones_raw]                   # noqa; pylint: disable=expression-not-assigned
        [_populate_device(d) for d in await self._get_devices_raw]               # noqa; pylint: disable=expression-not-assigned
        [_populate_issue(i) for i in await self._get_issues_raw]                 # noqa; pylint: disable=expression-not-assigned

    @property
    def info(self) -> dict:
        """Return all information for the hub."""
        keys = ['device_by_id', 'device_objs',
                'zone_by_id', 'zone_by_name', 'zone_objs']
        return _without_keys(self.__dict__, keys)

    @property
    async def _get_zones_raw(self) -> List[dict]:
        """Return a list of zones included in the system."""
        # getAllZonesData = x.get("/v3/zones", {username: e, password: t})

        if self._api_v1:
            self._zones_raw = await self._request("GET", 'zones')
        else:
            json = await self._request("GET", 'zones')
            # _LOGGER.debug("Hub()._get_zones_raw(): json = %s", json['data'])
            self._zones_raw = _get_zones_from_zones_v3(json['data'])

        _LOGGER.info("Hub: len(_zones_raw) = %s", len(self._zones_raw))
        return self._zones_raw

    @property
    def zones(self) -> list:
        """Return a list of Zones known to the Hub.

          v1/zones/summary: id, name
          v1/zones:         id, name, type, mode, temperature, setpoint,
          occupied, override, schedule
        """
        return self._subset_list(
            self._zones_raw, self._convert_zone, **ATTRS_ZONE)

    @property
    async def _get_devices_raw(self) -> List[dict]:
        """Return a list of devices included in the system."""
        # getDeviceList = x.get("/v3/data_manager", {username: e, password: t})

        if self._api_v1:
            self._devices_raw = await self._request('GET', 'devices')
        else:
            json = await self._request('GET', 'data_manager')
            # _LOGGER.debug("Hub()._get_devices_raw(): json = %s", json['data'])
            self._devices_raw = _get_devices_from_data_manager(json['data'])

        _LOGGER.info("Hub: len(_devices_raw) = %s", len(self._devices_raw))
        return self._devices_raw

    @property
    def devices(self) -> list:
        """Return a list of Devices known to the Hub.

          v1/devices/summary: id, type
          v1/devices:         id, type, assignedZones, state
        """
        result = self._subset_list(
            self._devices_raw, self._convert_device, **ATTRS_DEVICE)

        if not self._api_v1 and self._client._verbose != 3:
            result = natural_sort(result, 'id')

        return result

    @property
    async def _get_issues_raw(self) -> List[dict]:
        """Return a list of issues known to the hub."""

        if self._api_v1:
            self._issues_raw = await self._request('GET', 'issues')
        else:  # NB: this must run after _get_zones_raw()
            self._issues_raw = _get_issues_from_zones_v3(self._zones_raw)

        _LOGGER.info("Hub: len(_issues_raw) = %s", len(self._issues_raw))
        return self._issues_raw

    @property
    def issues(self) -> list:
        """Return a list of Issues known to the Hub.

          v1/issues: description, level
        """
        return self._subset_list(
            self._issues_raw, self._convert_issue, **ATTRS_ISSUE)


class GeniusTestHub(GeniusHub):
    """The test class for a Genius Hub - uses a test file."""

    def __init__(self, client, hub_dict, zones_json, device_json) -> None:
        _LOGGER.warning("GeniusTestHub()")
        super().__init__(client, hub_dict)

        self._zones_test = zones_json
        self._devices_test = device_json

        self._api_v1 = False

    @property
    async def _get_zones_raw(self) -> List[dict]:
        """Return a list of zones included in the system."""
        self._zones_raw = self._zones_test

        _LOGGER.info("Hub: len(_zones_raw) = %s", len(self._zones_raw))
        return self._zones_raw

    @property
    async def _get_devices_raw(self) -> List[dict]:
        """Return a list of devices included in the system."""
        self._devices_raw = self._devices_test

        _LOGGER.info("Hub: len(_devices_raw) = %s", len(self._devices_raw))
        return self._devices_raw


class GeniusZone(GeniusObject):
    """The class for Genius Zone."""

    def __init__(self, client, zone_dict, hub) -> None:
        _LOGGER.info("GeniusZone(id=%s)", zone_dict['id'])
        super().__init__(client, zone_dict, hub=hub)

        self._info = {}
        self._devices = []
        self._issues = []

        self._info_raw = None
        self._issues_raw = self._devices_raw = None

    @property
    def info(self) -> dict:
        """Return all information for a zone."""
        return _without_keys(self.__dict__, ['device_by_id', 'device_objs'])

    @property
    def devices(self) -> list:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        self._devices = [self._convert_device(d) for d in self.hub._devices_raw
                         if d['childValues']['location']['val'] == self.name]

        _LOGGER.debug("Zone(%s).devices: len(self._devices) = %s",
                      self.id, len(self._devices))
        return self._devices

    @property
    def issues(self) -> list:
        """Return a list of Issues known to the Zone."""

        self._issues = [self._convert_issue(i) for i in self.hub._issues_raw
                        if i['_zone_name'] == self.name]

        _LOGGER.debug("Hub().devices: len(self._devices) = %s",
                      len(self._devices))
        return self._issues

    @property
    def schedule(self) -> list:
        """Return the list of scheduled setpoints for this Zone."""
        raise NotImplementedError()

    async def set_mode(self, mode):
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        # TODO: device-specific logic to prevent placing into an invalid mode
        # TODO: e.g. zones only support footprint if they have a PIR
        allowed_modes = [ZONE_MODES.Off, ZONE_MODES.Override, ZONE_MODES.Timer]

        if hasattr(self, 'occupied'):
            allowed_modes += [ZONE_MODES.Footprint]
        allowed_mode_strs = [IMODE_TO_MODE[i] for i in allowed_modes]

        if isinstance(mode, int) and mode in allowed_modes:
            mode_str = IMODE_TO_MODE[mode]
        elif isinstance(mode, str) and mode in allowed_mode_strs:
            mode_str = mode
            mode = MODE_TO_IMODE[mode_str]
        else:
            raise TypeError(
                "Zone.set_mode(): mode='{}' isn't valid.".format(mode))

        _LOGGER.debug("Zone(%s).set_mode(mode=%s, mode_str='%s')...",
                      self.id, mode, mode_str)

        if self._api_v1:
            # v1 API uses strings
            url = 'zones/{}/mode'
            resp = await self._request("PUT", url.format(self.id),
                                       data=mode_str)
        else:
            # v3 API uses dicts
            # TODO: check PUT(POST?) vs PATCH
            url = 'zone/{}'
            resp = await self._request("PATCH", url.format(self.id),
                                       data={'iMode': mode})

        if resp:  # for v1, resp = None?
            resp = resp['data'] if resp['error'] == 0 else resp
        _LOGGER.debug("set_mode(%s): done, response = %s", self.id, resp)

    async def set_override(self, setpoint=None, duration=3600):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        setpoint = self.setpoint if setpoint is None else setpoint

        _LOGGER.debug("Zone(%s).set_override(setpoint=%s, duration=%s)...",
                      self.id, setpoint, duration)

        if self._api_v1:
            url = 'zones/{}/override'
            data = {'setpoint': setpoint, 'duration': duration}
            resp = await self._request("POST", url.format(self.id), data=data)
        else:
            url = 'zone/{}'
            data = {'iMode': ZONE_MODES.Boost,
                    'fBoostSP': setpoint,
                    'iBoostTimeRemaining': duration}
            resp = await self._request("PATCH", url.format(self.id), data=data)

        if resp:  # for v1, resp = None?
            resp = resp['data'] if resp['error'] == 0 else resp
        _LOGGER.debug(
            "set_override_temp(%s): done, response = %s", self.id, resp)

    async def update(self):
        """Update the Zone with its latest state data."""
        _LOGGER.debug("Zone(%s).update(xx)", self.id)

        if self._api_v1:
            _LOGGER.debug("Zone(%s).update(v1): type = %s",
                          self.id, type(self))
            url = 'zones/{}'
            data = await self._request("GET", url.format(self.id))
            self.__dict__.update(data)
        else:  # a WORKAROUND...
            _LOGGER.debug("Zone(%s).update(v3): type = %s",
                          self.id, type(self))
            await self.hub.update()


class GeniusDevice(GeniusObject):
    """The class for Genius Device."""

    def __init__(self, client, device_dict, hub, zone=None) -> None:
        _LOGGER.info("GeniusDevice(id=%s, assignedZone=%s)",
                     device_dict['id'], zone.id if zone else None)
        super().__init__(client, device_dict, hub=hub, assignedZone=zone)

        self._info = {}
        self._issues = []

        self._info_raw = None
        self._issues_raw = None

    @property
    def info(self) -> dict:
        """Return all information for a device."""
        return _without_keys(self.__dict__, [])

    @property
    def location(self) -> dict:  # aka assignedZones
        """Return the parent Zone of this Device."""
        raise NotImplementedError()

    async def update(self):
        """Update the Device with its latest state data."""
        _LOGGER.debug("Device(%s).update(xx)", self.id)

        if self._api_v1:
            _LOGGER.debug("Device(%s).update(v1): type = %s",
                          self.id, type(self))
            url = 'devices/{}'
            data = await self._request("GET", url.format(self.id))
            self.__dict__.update(data)
        else:  # a WORKAROUND...
            await self.hub.update()
            _LOGGER.debug("Device(%s).update(v3): type = %s",
                          self.id, type(self))
