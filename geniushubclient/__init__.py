"""Python client library for the Genius Hub API.

   see: https://my.geniushub.co.uk/docs
   """
# import asyncio
from hashlib import sha256
import logging

import aiohttp

from .const import (
    API_STATUS_ERROR,
    DEFAULT_INTERVAL_V1, DEFAULT_INTERVAL_V3,
    DEFAULT_TIMEOUT_V1, DEFAULT_TIMEOUT_V3,
    ITYPE_TO_TYPE, IMODE_TO_MODE,
    LEVEL_TO_TEXT, DESCRIPTION_TO_TEXT,
    zone_types, zone_modes, kit_types)

HTTP_OK = 200  # cheaper than: from http import HTTPStatus.OK

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)


def _convert_zone(input) -> dict:
    """Convert a v3 zone's dict/json to the v1 schema."""
    result = {}
    result['id'] = input['iID']
    result['type'] = ITYPE_TO_TYPE[input['iType']]
    result['name'] = input['strName']

    if input['iType'] in [zone_types.ControlSP, zone_types.TPI]:
        result['temperature'] = input['fPV']
        result['setpoint'] = input['fSP']

    if input['iType'] == zone_types.OnOffTimer:
        result['setpoint'] = input['fSP'] != 0

    result['mode'] = IMODE_TO_MODE[input['iMode']]

    # l = parseInt(i.iFlagExpectedKit) & e.equipmentTypes.Kit_PIR
    if input['iFlagExpectedKit'] & kit_types.PIR:
        # = parseInt(i.iMode) === e.zoneModes.Mode_Footprint
        u = input['iMode'] == zone_modes.Footprint
        # = null != (s = i.zoneReactive) ? s.bTriggerOn : void 0,
        d = input['objFootprint']['objReactive']['bTriggerOn']
        # = parseInt(i.iActivity) || 0,
        # c = input['iActivity'] | 0
        # o = t.isInFootprintNightMode(i)
        o = input['objFootprint']['bIsNight']
        # u && l && d && !o ? True : False
        result['occupied'] = u and d and not o

    if input['iType'] in [zone_types.OnOffTimer,
                          zone_types.ControlSP,
                          zone_types.TPI]:
        result['override'] = {}
        result['override']['duration'] = input['iBoostTimeRemaining']
        if input['iType'] == zone_types.OnOffTimer:
            result['override']['setpoint'] = (input['fBoostSP'] != 0)
        else:
            result['override']['setpoint'] = input['fBoostSP']

        result['schedule'] = {}

    # for device in input['nodes']:
    #     if device['addr'] not in ['1', 'WeatherData']:
    #         node = device['childNodes']['_cfg']['childValues']
    #         device_name = node['name']['val']
    #         device_sku = node['sku']['val']

    return result


def _convert_device(input) -> dict:
    """Convert a v3 device's dict/json to the v1 schema."""

    # if device['addr'] not in ['1', 'WeatherData']:
    result = {}
    result['id'] = input['addr']
    node = input['childNodes']['_cfg']['childValues']
    if node:
        result['type'] = node['name']['val']
        result['sku'] = node['sku']['val']
    else:
        result['type'] = None

    tmp = input['childValues']['location']['val']
    if tmp:
        result['assignedZones'] = [{'name': tmp}]
    else:
        result['assignedZones'] = [{'name': None}]

    result['state'] = {}

    return result


def _convert_issue(input) -> dict:                                               # TODO: not complete
    """Convert a v3 issues's dict/json to the v1 schema."""

    output = []
    for zone in input['data']:
        for issue in zone['lstIssues']:
            message = DESCRIPTION_TO_TEXT[issue['id']]

            tmp = {}
            tmp['description'] = message.format(zone['strName'])
            tmp['level'] = LEVEL_TO_TEXT[issue['level']]

            output.append(tmp)

    return output


def _extract_zones_from_zones(input) -> list:
    """Extract zones from /v3/zones JSON."""
    _LOGGER.debug("_zones_from_zones(): input = %s", input)

    return input


def _extract_devices_from_data_manager(input) -> list:
    """Extract devices from /v3/data_manager JSON."""
    _LOGGER.debug("_devices_from_data_manager(): input = %s", input)

    result = []
    for k1, v1 in input['childNodes'].items():
        if k1 != 'WeatherData':
            for device_id, device in v1['childNodes'].items():
                if device_id != '1':  # also: device['addr'] != '1':
                    result.append(device)

    return result


def _extract_devices_from_zones(input) -> list:
    """Extract devices from /v3/zones JSON."""
    _LOGGER.debug("_devices_from_zones(): input = %s", input)

    result = []
    for zone in input:
        if 'nodes' in zone:
            for device in zone['nodes']:
                if device['addr'] not in ['1', 'WeatherData']:
                    result.append(device)

    return result


class GeniusHubClient(object):
    def __init__(self, hub_id, username=None, password=None, session=None,
                 debug=False):
        if True:  # debug is True:
            _LOGGER.setLevel(logging.DEBUG)
            _LOGGER.error("Debug mode is explicitly enabled.")
        else:
            _LOGGER.error("Debug mode is not explicitly enabled "
                          "(but may be enabled elsewhere).")

        _LOGGER.info("GeniusHubClient(hub_id=%s)", hub_id)

        # use existing session if provided
        self._session = session if session else aiohttp.ClientSession()

        # if no credentials, then hub_id is a token for v1 API
        self._api_v1 = not (username or password)
        if self._api_v1:
            self._auth = None
            self._url_base = 'https://my.geniushub.co.uk/v1/'
            self._headers = {'authorization': "Bearer " + hub_id}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)
            self._poll_interval = DEFAULT_INTERVAL_V1
        else:  # using API ver3
            hash = sha256()
            hash.update((username + password).encode('utf-8'))
            self._auth = aiohttp.BasicAuth(
                login=username, password=hash.hexdigest())
            self._url_base = 'http://{}:1223/v3/'.format(hub_id)
            self._headers = {"Connection": "close"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
            self._poll_interval = DEFAULT_INTERVAL_V3

        self._verbose = False
        hub_id = hub_id[:8] + "..." if len(hub_id) > 20 else hub_id

        self.hub = GeniusHub(self, {'id': hub_id})

    @property
    def verbose(self) -> int:
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = 0 if value is None else value


class GeniusObject(object):
    def __init__(self, client, obj_dict, hub=None, assignedZone=None):

        self.__dict__.update(obj_dict)

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
            self.assignedZone = assignedZone

    def _without_keys(self, dict_obj, keys) -> dict:
        _info = dict(dict_obj)
        _info = {k: v for k, v in _info.items() if k[:1] != '_'}
        _info = {k: v for k, v in _info.items() if k not in keys}
        return _info

    async def _handle_assetion(self, error):
        _LOGGER.debug("_handle_assetion(error=%s)", error)

    async def _request(self, type, url, data=None):
        _LOGGER.debug("_request(type=%s, url='%s')", type, url)

        http_method = {
            "GET": self._client._session.get,
            "PATCH": self._client._session.patch,
            "POST": self._client._session.post,
            "PUT": self._client._session.put,
        }.get(type)

        try:
            async with http_method(
                self._client._url_base + url,
                json=data,
                headers=self._client._headers,
                auth=self._client._auth,
                timeout=self._client._timeout
            ) as response:
                assert response.status == HTTP_OK, response.text
                return await response.json(content_type=None)

        except aiohttp.client_exceptions.ServerDisconnectedError as err:
            _LOGGER.warning("_request(): Exception: ServerDisconnected, message: %s", err)
            _session = aiohttp.ClientSession()
            async with http_method(
                self._client._url_base + url,
                json=data,
                headers=self._client._headers,
                auth=self._client._auth,
                timeout=self._client._timeout
            ) as response:
                assert response.status == HTTP_OK, response.text
                return await response.json(content_type=None)
            _session.close()

        # except concurrent.futures._base.TimeoutError as err:

    @staticmethod
    def LookupStatusError(status):
        return API_STATUS_ERROR.get(status, str(status) + " Unknown status")


class GeniusHub(GeniusObject):
    # connection.post("/v3/system/reboot", { username: e, password: t,json: {}} )
    # connection.get("/v3/auth/test", { username: e, password: t, timeout: n })

    def __init__(self, client, hub_dict):
        _LOGGER.info("GeniusHub(client, hub=%s)", hub_dict['id'])
        super().__init__(client, hub_dict)

        self._info = {}  # a dict of attrs
        self._zones = []  # a list of dicts
        self._devices = []  # a list of dicts
        self._issues = []  # a list of dicts

        self._issues_raw = self._devices_raw = self._zones_raw = None

    async def update(self, force_refresh=False):
        """Update the Hub with its latest state data."""
        _LOGGER.debug("Hub(%s).update()", self.id)

        def _populate_zone(zone_dict):
            hub = self  # for now, only Hubs invoke this method

            zone_id = zone_dict['id']
            try:  # does the hub already know about this device?
                zone = hub.zone_by_id[zone_id]
            except KeyError:
                _LOGGER.debug("Creating a Zone (hub=%s, zone=%s)",
                              hub.id, zone_dict['id'])
                zone = GeniusZone(self._client, zone_dict, hub)
                hub.zone_objs.append(zone)
                hub.zone_by_id[zone.id] = zone
                hub.zone_by_name[zone.name] = zone
            else:
                _LOGGER.debug("Found a Zone (hub=%s, zone=%s)",
                              hub.id, zone_dict['id'])

        def _populate_device(device_dict, parent=None):
            if isinstance(self, GeniusHub):
                hub = self
                # or parent if None?
                name = device_dict['assignedZones'][0]['name']
                zone = hub.zone_by_name[name] if name else None
            else:
                hub = self.hub
                zone = self

            device_id = device_dict['id']
            try:  # does the Hub already know about this device?
                device = hub.device_by_id[device_id]
            except KeyError:
                _LOGGER.debug("Creating a Device (device=%s, hub=%s, zone=??)",
                              device_dict['id'], hub.id)
                device = GeniusDevice(self._client, device_dict, hub, zone)
                hub.device_objs.append(device)
                hub.device_by_id[device.id] = device
            else:
                _LOGGER.debug("Found a Device (hub=%s, device=%s)",
                              hub.id, device_dict['id'])

            if zone:
                try:  # does the (parent) Zone already know about this device?
                    device = zone.device_by_id[device_id]
                except KeyError:
                    _LOGGER.debug(
                        "Adding a Device (zone=%s, device=%s)", zone.id, device_dict['id'])
                    zone.device_objs.append(device)
                    zone.device_by_id[device.id] = device
                else:
                    _LOGGER.debug(
                        "Found a Device (zone=%s, device=%s)", zone.id, device_dict['id'])

            if isinstance(self, GeniusZone):                                     # TODO: this code may be redundant
                print("LOOK FOR THIS IN THE LIBRARY")                            # TODO: remove this
                try:  # does the zone already know about this device?
                    device = self.device_by_id[device_id]
                except KeyError:
                    self.device_objs.append(device)
                    self.device_by_id[device.id] = device

        for z in await self._get_zones:
            _populate_zone(z if self._api_v1 else _convert_zone(z))
        for d in await self._get_devices:
            _populate_device(d if self._api_v1 else _convert_device(d))

        _LOGGER.debug("Hub(%s).update(): len(hub.zone_objs) = %s",
                      self.id, len(self.zone_objs))
        _LOGGER.debug("Hub(%s).update(): len(hub.device_objs) = %s",
                      self.id, len(self.device_objs))

    @property
    def info(self) -> dict:
        """Return all information for the hub."""
        _LOGGER.debug("Hub(%s).info", self.id)

        keys = ['device_objs', 'device_by_id',
                'zone_objs', 'zone_by_id', 'zone_by_name']
        info = self._without_keys(self.__dict__, keys)

        _LOGGER.debug("Hub(%s).info = %s", self.id, info)
        return info

    @property
    async def version(self) -> dict:
        """Return the current software version(s) of the system.

          This is a v1 API only.
        """
        if self._api_v1:
            url = 'version'
            self._version = await self._request("GET", url)
        else:
            self._version = {
                'hubSoftwareVersion': 'unable to determine via v3 API'
            }

        _LOGGER.debug("self._version = %s", self._version)
        return self._version

    @property
    async def _get_zones(self) -> list:
        """Return a list (of dicts) of zones included in the system."""
        # getAllZonesData = x.get("/v3/zones", {username: e, password: t})

        raw_json = await self._request("GET", 'zones')

        if self._api_v1:
            self._zones_raw = raw_json
        else:
            self._zones_raw = _extract_zones_from_zones(raw_json['data'])

        # self._zones_raw.sort(key=lambda s: int(s['id']))

        _LOGGER.info("Hub()._get_zones(): len(self._zones_raw) = %s", len(self._zones_raw))
        _LOGGER.info("Hub()._get_zones(): self._zones_raw[0]) = %s", self._zones_raw[0])
        return self._zones_raw

    @property
    def zones(self) -> list:
        """Return a list of Zones known to the Hub.

          v1/zones/summary: id, name
          v1/zones: id, name, type, mode, temperature, setpoint, occupied,
          override, schedule
        """
        _LOGGER.debug("Hub().zones: len(self.zone_objs) = %s",
                      len(self.zone_objs))

        if not self._zones:
            self._zones = []
            for zone in self.zone_objs:
                self._zones.append(zone.info)

        _LOGGER.debug("Hub().zones: self._devices = %s", self._zones)
        return self._zones

    @property
    async def _get_devices(self) -> list:
        """Return a list (of dicts) of devices included in the system."""
        # getDeviceList = x.get("/v3/data_manager", {username: e, password: t})

        if not self._api_v1:
            # WORKAROUND: There's a aiohttp.ServerDisconnectedError on 2nd HTTP
            # method (2nd GET v3/zones or GET v3/zones & get /data_manager) if
            # it is done the v1 way (above) for v3
            self._devices_raw = _extract_devices_from_zones(self._zones_raw)

        else:  # son = await self._request('GET', 'devices' if self._api_v1 else 'zones')
            raw_json = await self._request('GET', 'devices' if self._api_v1 else 'data_manager')

            if self._api_v1:
                self._devices_raw = raw_json
            else:  #._devices_raw = _extract_devices_from_zones(raw_json['data'])
                self._devices_raw = _extract_devices_from_data_manager(raw_json['data'])

        # self._get_devices.sort(key=lambda s: int(s['id']))

        _LOGGER.info("Hub()._get_devices(): len(self._devices_raw) = %s", len(self._devices_raw))
        _LOGGER.info("Hub()._get_devices(): self._devices_raw[0]) = %s", self._devices_raw[0])
        return self._devices_raw

    @property
    def devices(self) -> list:
        """Return a list of Devices known to the Hub.

          v1/devices/summary: id, type
          v1/devices: id, type, assignedZones, state
        """
        _LOGGER.debug("Hub().devices: len(self.device_objs) = %s",
                      len(self.device_objs))

        if not self._devices:
            self._devices = []
            for device in self.device_objs:
                self._devices.append(device.info)

        _LOGGER.debug("Hub().devices: self._devices = %s", self._devices)
        return self._devices

    @property
    async def _get_issues(self) -> list:
        """Return a list of currently identified issues with the system.

          This is a v1 API: GET /issues
        """
        # url = 'issues' if self._api_v1 else 'zones'
        raw_json = await self._request("GET", 'issues')

        self._issues = raw_json if self._api_v1 else _convert_issue(raw_json)

        _LOGGER.info("GeniusHub.issues = %s", self._issues)
        return raw_json if self._client._verbose else self._issues

    @property
    async def issues(self) -> list:
        """Return a list of Issues known to the Hub."""

        if not self._issues:
            await self._get_issues
        return self._issues


class GeniusZone(GeniusObject):
    def __init__(self, client, zone_dict, hub):
        _LOGGER.info("GeniusZone(hub=%s, zone['id]=%s)",
                      hub.id, zone_dict['id'])
        super().__init__(client, zone_dict, hub=hub)

        self._info = {}
        self._devices = []
        self._issues = []

        self._issues_raw = self._devices_raw = None

    @property
    def info(self) -> dict:
        """Return all information for a zone."""
        _LOGGER.debug("Zone(%s).info", self.id)

        keys = ['device_objs', 'device_by_id']
        info = self._without_keys(self.__dict__, keys)

        _LOGGER.debug("Zone(%s).info = %s", self.id, info)
        return info

    @property
    def devices(self) -> list:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        _LOGGER.debug("Zone(%s).devices: len(self.device_objs) = %s",
                      self.id, len(self.device_objs))

        if not self._devices:                                                    # TODO: some zones dont have devices?
            self._devices = []
            for device in self.device_objs:
                self._devices.append(device.info)

        _LOGGER.debug("Zone(%s).devices: self._devices = %s",
                      self.id, self._devices)
        return self._devices

    async def set_mode(self, mode):
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        _LOGGER.debug("set_mode(%s): mode=%s", self.id, mode)

        if self._api_v1:
            url = 'zones/{}/mode'
            await self._request("PUT", url.format(self.id), data=mode)
        else:
            # 'off'       'data': {'iMode': 1}}
            # 'footprint' 'data': {'iMode': 4}}
            # 'timer'     'data': {'iMode': 2}}
            url = 'zone/{}'
            data = {'iMode': mode}
            await self._request("PATCH", url.format(self.id), data=data)

        _LOGGER.debug("set_mode(%s): done.", self.id)                            # TODO: remove this line

    async def set_override(self, duration, setpoint):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        _LOGGER.debug(
            "set_override_temp(%s): duration=%s, setpoint=%s", self.id, duration, setpoint)

        if self._api_v1:
            url = 'zones/{}/override'
            data = {'duration': duration, 'setpoint': setpoint}
            await self._request("POST", url.format(self.id), data=data)
        else:
            # 'override'  'data': {'iMode': 16, 'iBoostTimeRemaining': 3600, 'fBoostSP': temp}}
            url = 'zone/{}'
            data = {'iMode': 16,
                    'iBoostTimeRemaining': duration,
                    'fBoostSP': setpoint}
            await self._request("PATCH", url.format(self.id), data=data)

        _LOGGER.debug("set_override_temp(%s): done.", self.id)                   # TODO: remove this line

    async def update(self):
        """Update the Zone with its latest state data."""
        _LOGGER.error("Zone(%s).update(xx)", self.id)

        if self._api_v1:                                                         # TODO: this doesn't work for v3
            _LOGGER.warn("Zone(%s).update(v1): type = %s", self.id, type(self))
            url = 'zones/{}'
            data = await self._request("GET", url.format(self.id))
            self.__dict__.update(data)
        else:  # a WORKAROUND...
            _LOGGER.warn("Zone(%s).update(v3): type = %s", self.id, type(self))
            await self.hub.update()


class GeniusDevice(GeniusObject):
    def __init__(self, client, device_dict, hub, zone=None):
        _LOGGER.info("GeniusZone(hub=%s, zone=%s,device['id']=%s)",
                      hub.id, zone, device_dict['id'])
        super().__init__(client, device_dict, hub=hub, assignedZone=zone)

        self._info = {}
        self._issues = []

        self._issues_raw = None

    @property
    def info(self) -> dict:
        """Return all information for a device."""
        _LOGGER.debug("Device(%s).info: type = %s", self.id, type(self))

        keys = []
        info = self._without_keys(self.__dict__, keys)
        _LOGGER.debug("Device(%s).info = %s", self.id, info)
        return info

    @property
    async def location(self) -> dict:  # aka assignedZones
        raise NotImplementedError()

    async def update(self):
        """Update the Device with its latest state data."""
        _LOGGER.error("Device(%s).update(xx)", self.id)

        if self._api_v1:                                                         # TODO: this block doesn't work for v3
            _LOGGER.warn("Device(%s).update(v1): type = %s",
                         self.id, type(self))
            url = 'devices/{}'
            data = await self._request("GET", url.format(self.id))
            self.__dict__.update(data)
        else:  # a WORKAROUND...
            await self.hub.update()
            _LOGGER.warn("Device(%s).update(v3): type = %s",
                         self.id, type(self))
