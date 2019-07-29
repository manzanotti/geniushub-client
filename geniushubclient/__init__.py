"""Python client library for the Genius Hub API.

   see: https://my.geniushub.co.uk/docs
   """
from hashlib import sha256
from typing import Dict, List  # Any, Dict, List, Set, Tuple, Optional

import logging
import re

import aiohttp

from .const import (
    ATTRS_DEVICE, ATTRS_ZONE, STATE_ATTRS,
    DEFAULT_TIMEOUT_V1, DEFAULT_TIMEOUT_V3,
    ITYPE_TO_TYPE, IMODE_TO_MODE, MODE_TO_IMODE, IDAY_TO_DAY,
    LEVEL_TO_TEXT, DESCRIPTION_TO_TEXT,
    ZONE_TYPES, ZONE_MODES, KIT_TYPES)

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)

# pylint3 --max-line-length=100
# pylint: disable=fixme
# pylint: disable=too-many-branches, too-many-locals, too-many-statements


def natural_sort(dict_list, dict_key):
    """Return a list that is case-insensitively sorted, with '11' after '2'."""
    # noqa; pylint: disable=missing-docstring, multiple-statements
    def alphanum_key(k): return [int(c) if c.isdigit() else c.lower()
                                 for c in re.split('([0-9]+)', k[dict_key])]
    return sorted(dict_list, key=alphanum_key)


def _get_zones_from_zones_v3(raw_json) -> List:
    """Extract Zones from /v3/zones JSON."""
    return raw_json


def _get_devices_from_data_manager(raw_json) -> List:
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


def _get_devices_from_zones_v3(raw_json) -> List:
    """Extract Devices from /v3/zones JSON."""
    result = []
    for zone in raw_json:
        for device in [x for x in zone['nodes'].values()
                       if x['addr'] not in ['WeatherData']]:  # ['1', 'WeatherData']
            result.append(device)

    return result


def _get_issues_from_zones_v3(raw_json) -> List:
    """Extract Issues from /v3/zones JSON."""
    result = []
    for zone in raw_json:
        for issue in zone['lstIssues']:
            # TODO: might better be as an ID +/- convert to a comprehension
            issue['_zone_name'] = zone['strName']  # some issues wont have this data
            result.append(issue)

    return result


class GeniusHubClient():  # pylint: disable=too-many-instance-attributes
    """The class for a connection to a Genius Hub."""

    # pylint: disable=too-many-arguments
    def __init__(self, hub_id, username=None, password=None, session=None,
                 debug=False) -> None:
        if debug is True:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.debug("Debug mode is explicitly enabled.")
        else:
            _LOGGER.debug("Debug mode is not explicitly enabled "
                          "(but may be enabled elsewhere).")

        self._session = session if session else aiohttp.ClientSession()

        self.api_version = 3 if username or password else 1
        if self.api_version == 1:
            self._auth = None
            self._url_base = 'https://my.geniushub.co.uk/v1/'
            self._headers = {'authorization': "Bearer " + hub_id}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)
        else:  # self.api_version == 3
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
                raise_for_status=True
            ) as resp:
                response = await resp.json(content_type=None)

        # except concurrent.futures._base.TimeoutError as err:
        except aiohttp.client_exceptions.ServerDisconnectedError as err:
            _LOGGER.debug("_request(): ServerDisconnected, retrying (msg=%s)", err)
            _session = aiohttp.ClientSession()
            async with http_method(
                self._url_base + url,
                json=data,
                headers=self._headers,
                auth=self._auth,
                timeout=self._timeout,
                raise_for_status=True
            ) as resp:
                response = await resp.json(content_type=None)
            await _session.close()

        if method != 'GET':
            _LOGGER.debug("_request(): response=%s", response)
        return response

    @property
    def verbosity(self) -> int:
        """Get/Set the level of detail."""
        return self._verbose

    @verbosity.setter
    def verbosity(self, value):
        if 0 <= value <= 3:
            self._verbose = value
        else:
            raise ValueError("'{}' is not valid for verbosity. "
                             "The permissible range is (0-3).".format(value))


class GeniusObject():  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """The base class for any Genius object: Hub, Zone or Device."""

    def __init__(self, client, obj_dict, raw_json, assigned_zone=None) -> None:
        self.id = None  # prevents non-member lint errors                        # noqa; pylint: disable=invalid-name
        self.__dict__.update(obj_dict)  # create self.id, etc.

        self._client = client
        self._raw_json = raw_json

        if isinstance(self, GeniusHub):
            self.zone_objs = []
            self.zone_by_id = {}
            self.zone_by_name = {}
            self._issues = []

        if isinstance(self, GeniusDevice):
            self.assigned_zone = assigned_zone  # TODO: rename to _zone?

        else:  # GeniusHub, GeniusZone
            self.device_objs = []
            self.device_by_id = {}

    def _convert_zone(self, raw_dict) -> Dict:
        """Convert a v3 zone's dict/json to the v1 schema."""
        if self._client.api_version == 1:
            return raw_dict

        result = {}
        result['id'] = raw_dict['iID']
        result['name'] = raw_dict['strName']
        result['type'] = ITYPE_TO_TYPE[raw_dict['iType']]
        result['mode'] = IMODE_TO_MODE[raw_dict['iMode']]

        if raw_dict['iType'] in [ZONE_TYPES.ControlSP, ZONE_TYPES.TPI]:
            if not (raw_dict['iType'] == ZONE_TYPES.TPI and
                    not raw_dict['activeTemperatureDevices']):
                result['temperature'] = raw_dict['fPV']
            result['setpoint'] = raw_dict['fSP']

        elif raw_dict['iType'] == ZONE_TYPES.OnOffTimer:
            result['setpoint'] = bool(raw_dict['fSP'])

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
        if raw_dict['iFlagExpectedKit'] & KIT_TYPES.PIR:
            # pylint: disable=invalid-name
            u = raw_dict['iMode'] == ZONE_MODES.Footprint
            d = raw_dict['zoneReactive']['bTriggerOn']
            c = raw_dict['iActivity'] or 0                                       # noqa: ignore=F841; pylint: disable=unused-variable
            o = raw_dict['objFootprint']['bIsNight']
            # i suspect -1 should be True
            result['occupied'] = True if u and d and (not o) else -1 if c > 0 else False

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
             footprint={...} iff: ControlSP, _even_ if no PIR, otherwise ={}
        """
        result['schedule'] = {'timer': {}, 'footprint': {}}

        # Timer schedule...
        if raw_dict['iType'] != ZONE_TYPES.Manager:
            root = result['schedule']['timer'] = {'weekly': {}}
            day = -1

            try:  # TODO: confirm creation of zone despite exception
                setpoints = raw_dict['objTimer']
                for idx, setpoint in enumerate(setpoints):
                    tm_next = setpoint['iTm']
                    sp_next = setpoint['fSP']
                    if raw_dict['iType'] == ZONE_TYPES.OnOffTimer:
                        sp_next = bool(sp_next)

                    if setpoint['iDay'] > day:
                        day += 1
                        node = root['weekly'][IDAY_TO_DAY[day]] = {}
                        node['defaultSetpoint'] = sp_next
                        node['heatingPeriods'] = []

                    elif sp_next != node['defaultSetpoint']:
                        tm_last = setpoints[idx+1]['iTm']
                        node['heatingPeriods'].append({
                            'end': tm_last,
                            'start': tm_next,
                            'setpoint': sp_next
                        })

            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to convert Timer schedule for Zone %s, "
                                  "message: %s", result['id'], err)

        # Footprint schedule...
        if raw_dict['iType'] in [ZONE_TYPES.ControlSP]:
            root = result['schedule']['footprint'] = {'weekly': {}}
            day = -1

            try:  # TODO: confirm creation of zone despite exception
                setpoints = raw_dict['objFootprint']
                for idx, setpoint in enumerate(setpoints['lstSP']):
                    tm_next = setpoint['iTm']
                    sp_next = setpoint['fSP']

                    if setpoint['iDay'] > day:
                        day += 1
                        node = root['weekly'][IDAY_TO_DAY[day]] = {}
                        node['defaultSetpoint'] = setpoints['fFootprintAwaySP']
                        node['heatingPeriods'] = []

                    if sp_next != setpoints['fFootprintAwaySP']:
                        if tm_next == setpoints['iFootprintTmNightStart']:
                            tm_last = 86400  # 24 * 60 * 60
                        else:
                            tm_last = setpoints['lstSP'][idx+1]['iTm']

                        node['heatingPeriods'].append({
                            'end': tm_last,
                            'start': tm_next,
                            'setpoint': sp_next
                        })

            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Failed to convert Footprint schedule for Zone %s, "
                                  "message: %s", result['id'], err)

        return result

    def _convert_device(self, raw_dict) -> Dict:
        """Convert a v3 device's dict/json to the v1 schema.

        Sets id, type, assignedZones and state.
        """
        if self._client.api_version == 1:
            return raw_dict

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
                    _LOGGER.debug("Device %s, '%s': has no confirming fingerprint!",
                                  device['id'], device['type'])
                else:
                    _LOGGER.error("Device %s: has no type, and no fingerprint!",
                                  device['id'])
                return

            if not device['type']:
                device['type'] = fingerprint
                _LOGGER.warning("Device %s, '%s': typed only by its fingerprint!",
                                device['id'], device['type'])

            elif device['type'][:21] != fingerprint:  # "Dual Channel Receiver"
                _LOGGER.error("Device %s, '%s': doesn't match its fingerprint: '%s'!",
                              device['id'], device['type'], fingerprint)

            # else:
            #     _LOGGER.debug("Device %s, '%s': matches its fingerprint.",
            #                   device['id'], device['type'])

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
            _LOGGER.debug("Device %s, '%s': typed by its fingerprint (this is OK).",
                          result['id'], result['type'])
        else:
            _check_fingerprint(node, result)  # ... confirm type, set if needed

        result['assignedZones'] = [{'name': None}]  # 3. Set assignedZones...
        if node['location']['val']:
            result['assignedZones'] = [{'name': node['location']['val']}]

        result['state'] = state = {}  # 4. Set state...

        # the following order should be preserved
        state.update([(v, node[k]['val']) for k, v in STATE_ATTRS.items() if k in node])
        if 'outputOnOff' in state:  # this one should be a bool
            state['outputOnOff'] = bool(state['outputOnOff'])

        return result

    def _convert_issue(self, raw_dict) -> Dict:
        """Convert a v3 issues's dict/json to the v1 schema."""
        if self._client.api_version == 1:
            return raw_dict

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


class GeniusHub(GeniusObject):
    """The class for a Genius Hub."""

    def __init__(self, client, hub_dict) -> None:
        super().__init__(client, hub_dict, {})

        self._zones_raw = self._devices_raw = self._issues_raw = None
        self._zones_test = self._devices_test = None

    def __repr__(self):
        return self.info

    @property
    def info(self) -> Dict:
        """Return all information for the hub."""
        # x.get("/v3/auth/test", { username: e, password: t, timeout: n })
        keys = ['device_objs', 'device_by_id', 'device_by_zone_id',
                'zone_objs', 'zone_by_id', 'zone_by_name']
        return {k: v for k, v in self.__dict__.items() if k[:1] != '_' and k not in keys}

    @property
    def zones(self) -> List:
        """Return a list of Zones known to the Hub.

          v1/zones/summary: id, name
          v1/zones:         id, name, type, mode, temperature, setpoint,
          occupied, override, schedule
        """
        # return self._subset_list(self.zone_objs, self._zones_raw, **ATTRS_ZONE)
        return [z.info for z in self.zone_objs]

    @property
    def devices(self) -> List:
        """Return a list of Devices known to the Hub.

          v1/devices/summary: id, type
          v1/devices:         id, type, assignedZones, state
        """
        return natural_sort([d.info for d in self.device_objs], 'id')

    @property
    def issues(self) -> List:
        """Return a list of Issues known to the Hub.

          v1/issues: description, level
        """
        return self._issues

    async def update(self):
        """Update the Hub with its latest state data."""

        def _populate_zone(zone_raw):
            zone_dict = self._convert_zone(zone_raw)

            try:  # does the hub already know about this zone?
                zone = self.zone_by_id[zone_dict['id']]
            except KeyError:
                zone = GeniusZone(self._client, zone_dict, zone_raw)
                self.zone_objs.append(zone)

                self.zone_by_id[zone_dict['id']] = zone
                self.zone_by_name[zone_dict['name']] = zone

            return zone_dict['id'], zone

        def _populate_device(device_raw):
            device_dict = self._convert_device(device_raw)

            zone_name = device_dict['assignedZones'][0]['name']
            zone = self.zone_by_name[zone_name] if zone_name else None

            try:  # does the Hub already know about this device?
                device = self.device_by_id[device_dict['id']]
            except KeyError:
                device = GeniusDevice(self._client, device_dict, device_raw, zone)
                self.device_objs.append(device)

                self.device_by_id[device_dict['id']] = device

            if zone:
                try:  # does the parent Zone already know about this device?
                    device = zone.device_by_id[device_dict['id']]  # TODO: what happends if None???
                except KeyError:
                    zone.device_by_id[device_dict['id']] = device
                    zone.device_objs.append(device)

            return device_dict['id'], device

        def _populate_issue(issue_raw):
            issue_dict = self._convert_issue(issue_raw)

            _LOGGER.info("Found an Issue: %s)", issue_dict)

            return issue_dict

        if isinstance(self, GeniusTestHub):  # a hack for testing
            self._client.api_version = 3
            self._zones_raw = _get_zones_from_zones_v3(self._zones_test)
            self._issues_raw = _get_issues_from_zones_v3(self._zones_test)
            self._devices_raw = _get_devices_from_data_manager(self._devices_test)

        elif self._client.api_version == 1:  # TODO: this needs checking!
            self._zones_raw = await self._client.request('GET', 'zones')
            self._issues_raw = await self._client.request('GET', 'issues')
            self._devices_raw = await self._client.request('GET', 'devices')

        else:   # self._client.api_version == 3:
            response = await self._client.request('GET', 'zones')
            self._zones_raw = _get_zones_from_zones_v3(response['data'])
            self._issues_raw = _get_issues_from_zones_v3(response['data'])

            response = await self._client.request('GET', 'data_manager')
            self._devices_raw = _get_devices_from_data_manager(response['data'])

        # pylint: disable=expression-not-assigned
        [_populate_zone(z) for z in self._zones_raw]
        [_populate_device(d) for d in self._devices_raw]
        self._issues = [_populate_issue(i) for i in self._issues_raw]

    async def reboot(self):
        """Reboot the hub."""
        # x.post("/v3/system/reboot", { username: e, password: t, json:{} })
        raise NotImplementedError


class GeniusTestHub(GeniusHub):
    """The test class for a Genius Hub - uses a test file."""

    def __init__(self, client, hub_dict, zones_json, device_json) -> None:
        super().__init__(client, hub_dict)

        _LOGGER.info("Using GeniusTestHub()")

        self._zones_test = zones_json
        self._devices_test = device_json


class GeniusZone(GeniusObject):
    """The class for a Genius Zone."""

    def __init__(self, client, zone_dict, raw_json) -> None:
        super().__init__(client, zone_dict, raw_json)

    def __repr__(self):
        return {k: v for k, v in self.__dict__.items()
                if k in ATTRS_ZONE['summary_keys']}

    @property
    def info(self) -> Dict:
        """Return all information for the zone."""
        if self._client.verbosity == 3:
            return self._raw_json

        if self._client.verbosity == 2:
            return {k: v for k, v in self.__dict__.items()
                    if k[:1] != '_' and k not in ['device_objs', 'device_by_id']}

        keys = ATTRS_ZONE['summary_keys']
        if self._client.verbosity == 1:
            keys += ATTRS_ZONE['detail_keys']

        return {k: v for k, v in self.__dict__.items() if k in keys}

    @property
    def devices(self) -> List:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        return natural_sort([d.info for d in self.device_objs], 'id')

    @property
    def issues(self) -> List:
        """Return a list of Issues known to the Zone."""
        raise NotImplementedError

    async def set_mode(self, mode):
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        allowed_modes = [ZONE_MODES.Off, ZONE_MODES.Override, ZONE_MODES.Timer]

        if hasattr(self, 'occupied'):  # has a PIR (movement sensor)
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

        if self._client.api_version == 1:
            url = 'zones/{}/mode'  # v1 API uses strings
            resp = await self._client.request('PUT', url.format(self.id), data=mode_str)
        else:  # self._client.api_version == 1
            url = 'zone/{}'  # v3 API uses dicts  # TODO: check: is it PUT(POST?) vs PATCH
            resp = await self._client.request('PATCH', url.format(self.id), data={'iMode': mode})

        if resp:  # for v1, resp = None?
            resp = resp['data'] if resp['error'] == 0 else resp
        _LOGGER.debug("Zone(%s).set_mode(): response = %s", self.id, resp)

    async def set_override(self, setpoint=None, duration=3600):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        setpoint = setpoint if setpoint is not None else self.setpoint  # pylint: disable=no-member

        _LOGGER.debug("Zone(%s).set_override(setpoint=%s, duration=%s)...",
                      self.id, setpoint, duration)

        if self._client.api_version == 1:
            url = 'zones/{}/override'
            data = {'setpoint': setpoint, 'duration': duration}
            resp = await self._client.request('POST', url.format(self.id), data=data)
        else:
            url = 'zone/{}'
            data = {'iMode': ZONE_MODES.Boost,
                    'fBoostSP': setpoint,
                    'iBoostTimeRemaining': duration}
            resp = await self._client.request('PATCH', url.format(self.id), data=data)

        if resp:  # for v1, resp = None?
            resp = resp['data'] if resp['error'] == 0 else resp
        _LOGGER.debug("Zone(%s).set_override_temp(): response = %s", self.id, resp)


class GeniusDevice(GeniusObject):  # pylint: disable=too-few-public-methods
    """The class for a Genius Device."""

    def __init__(self, client, device_dict, raw_json, zone=None) -> None:
        super().__init__(client, device_dict, raw_json, assigned_zone=zone)

    def __repr__(self):
        return {k: v for k, v in self.__dict__.items()
                if k in ATTRS_DEVICE['summary_keys']}

    @property
    def info(self) -> Dict:
        """Return all information for the device."""
        if self._client.verbosity == 3:
            return self._raw_json

        if self._client.verbosity == 2:
            return {k: v for k, v in self.__dict__.items()
                    if k[:1] != '_' and k not in ['assigned_zone']}

        keys = ATTRS_DEVICE['summary_keys']
        if self._client.verbosity == 1:
            keys += ATTRS_DEVICE['detail_keys']

        return {k: v for k, v in self.__dict__.items() if k in keys}
