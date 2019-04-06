"""Python client library for the Genius Hub API.

see: https://my.geniushub.co.uk/docs
"""
import asyncio
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


class GeniusObject(object):
    def __init__(self, client, hub=None, zone=None, device=None, data={}):
        self._client = client
        self._api_v1 = client._api_v1
        self.__dict__.update(data)

        if isinstance(self, GeniusHub):
            self.zone_objs = []
            self.zone_by_id = {}
            self.zone_by_name = {}

        if isinstance(self, GeniusHub) or isinstance(self, GeniusZone):
            self.device_objs = []
            self.device_by_id = {}

    async def _handle_assetion(self, error):
        _LOGGER.debug("_handle_assetion(error=%s)", error)

    async def _request(self, type, url, payload=None):
        _LOGGER.debug("_request(type=%s, url=%s)", type, url)

        method = {
            "GET": self._client._session.get,
            "PATCH": self._client._session.patch,
            "POST": self._client._session.post,
            "PUT": self._client._session.put,
        }.get(type)

        async with method(
                self._client._url_base + url,
                headers=self._client._headers,
                auth=self._client._auth,
                timeout=self._client._timeout
            ) as response:
                assert response.status == HTTP_OK, response.text
                return await response.json(content_type=None)
                # data=payload,

    @staticmethod
    def LookupStatusError(status):
        return API_STATUS_ERROR.get(status, str(status) + " Unknown status")


class GeniusHubClient(object):
    def __init__(self, hub_id, username=None, password=None, session=None):
        _LOGGER.debug("GeniusHubClient(hub_id=%s)", hub_id)

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
            self._headers = None  # {"Connection": "close"}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
            self._poll_interval = DEFAULT_INTERVAL_V3

        self._verbose = False
        self._hub_id = hub_id[:20] + "..." if len(hub_id) > 20 else hub_id

        self.hub = None

    async def populate(self, force_refresh=False):

        def _populate_zone(hub, zone_dict):
            _LOGGER.debug("Adding a Zone=%s", zone_dict['id'])
            try:  # does the hub already know about this device?
                zone = hub.zone_by_id[zone_dict['id']]
            except KeyError:
                zone = GeniusZone(self, hub, zone_dict)
                hub.zone_objs.append(zone)
                hub.zone_by_id[zone.id] = zone
                hub.zone_by_name[zone.name] = zone

        def _populate_device(hub, device_dict):
            _LOGGER.debug("Adding a Device=%s", device_dict['id'])
            zone_name = device_dict['assignedZones'][0]['name']
            if zone_name and zone_name in hub.zone_by_name:
                zone = hub.zone_by_name[zone_name]
            else:
                zone = None
            try:  # does the hub already know about this device?
                device = hub.device_by_id[device_dict['id']]
            except KeyError:
                device = GeniusDevice(self, hub, zone, device_dict)
                hub.device_objs.append(device)
                hub.device_by_id[device.id] = device

            if isinstance(self, GeniusHub):
                try:  # does the zone already know about this device?
                    device = self.device_by_id[device_dict['id']]
                except KeyError:
                    self.device_objs.append(device)
                    self.device_by_id[device.id] = device

        hub = self.hub = GeniusHub(self, self._hub_id)
        for zone in await hub.zones:
            _populate_zone(hub, zone)
        for device in await hub.devices:
            _populate_device(hub, device)

    @property
    def verbose(self) -> int:
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = 0 if value is None else value


class GeniusHub(GeniusObject):
    # connection.post("/v3/system/reboot", { username: e, password: t,json: {}} )
    # connection.get("/v3/auth/test", { username: e, password: t, timeout: n })

    def __init__(self, client, hub_id):
        _LOGGER.debug("GeniusHub(hub=%s)", hub_id[:20])
        super().__init__(client, data={'id': hub_id[:20]})

        self._zones = []
        self._devices = []
        self._issues = []

    @property
    async def info(self) -> dict:
        """Return information for the hub.

          This is not a v1 API.
        """
        def _convert_to_v1(input) -> dict:
            """Convert v3 output to v1 schema."""
            output = dict(input)
            output['schedule'] = {}
            output['schedule']['timer'] = {}
            output['schedule']['footprint'] = {}
            return output

        self._detail = {}

        tmp = await self.zones if not self._zones else self._zones
        self._detail = tmp[0] if self._api_v1 else _convert_to_v1(tmp[0])

        _LOGGER.debug("self._detail = %s", self._detail)
        return self._detail

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
        """Return a list of zones included in the system.

          This is a v1 API: GET /zones
        """
        def _convert_to_v1(input) -> list:
            """Convert v3 output to v1 schema."""
            output = []
            for zone in input:
                tmp = {}
                tmp['id'] = zone['iID']
                tmp['type'] = ITYPE_TO_TYPE[zone['iType']]
                tmp['name'] = zone['strName']

                if zone['iType'] in [zone_types.ControlSP,
                                     zone_types.TPI]:
                    tmp['temperature'] = zone['fPV']
                    tmp['setpoint'] = zone['fSP']

                if zone['iType'] == zone_types.OnOffTimer:
                    tmp['setpoint'] = zone['fSP'] != 0

                tmp['mode'] = IMODE_TO_MODE[zone['iMode']]

                # l = parseInt(i.iFlagExpectedKit) & e.equipmentTypes.Kit_PIR
                if zone['iFlagExpectedKit'] & kit_types.PIR:
                    # = parseInt(i.iMode) === e.zoneModes.Mode_Footprint
                    u = zone['iMode'] == zone_modes.Footprint
                    # = null != (s = i.zoneReactive) ? s.bTriggerOn : void 0,
                    d = zone['objFootprint']['objReactive']['bTriggerOn']
                    # = parseInt(i.iActivity) || 0,
                    # c = zone['iActivity'] | 0
                    # o = t.isInFootprintNightMode(i)
                    o = zone['objFootprint']['bIsNight']
                    # u && l && d && !o ? True : False
                    tmp['occupied'] = u and d and not o

                if zone['iType'] in [zone_types.OnOffTimer,
                                     zone_types.ControlSP,
                                     zone_types.TPI]:
                    tmp['override'] = {}
                    tmp['override']['duration'] = zone['iBoostTimeRemaining']
                    if zone['iType'] == zone_types.OnOffTimer:
                        tmp['override']['setpoint'] = (zone['fBoostSP'] != 0)
                    else:
                        tmp['override']['setpoint'] = zone['fBoostSP']

                    tmp['schedule'] = {}

                output.append(tmp)

            return output

        # getAllZonesData = x.get("/v3/zones", {username: e, password: t})
        raw_json = await self._request("GET", 'zones')
        raw_json = raw_json if self._api_v1 else raw_json['data']

        self._zones = raw_json if self._api_v1 else _convert_to_v1(raw_json)
        self._zones.sort(key=lambda s: int(s['id']))

        _LOGGER.debug("GeniusHub.zones = %s", self._zones)
        return raw_json if self._client._verbose else self._zones

    @property
    async def zones(self) -> list:
        """Return a list of Zones known to the Hub."""

        if not self._zones:
            await self._get_zones
        return self._zones

    @property
    async def _get_devices(self) -> list:
        """Return a list of devices included in the system.

          This is a v1 API: GET /devices
        """
        def _convert_to_v1_via_zones(input) -> list:
            """Convert v3 output to v1 schema."""

            output = []
            for zone in input['data']:
                for node in zone['nodes']:
                    if not node['addr'] == 'WeatherData':
                        # cv = node['childValues']
                        # if typeId in cv:
                        # result = paramsFunction(cv)
                        result = {}
                        result['id'] = node['addr']  # not zone['iID']
                        # sult['type'] = node['type']
                        # sult['name'] = zone['strName'].strip()
                        xx = node['childNodes']['_cfg']['childValues']
                        result['type'] = xx['name']['val'] if 'name' in xx else None
                        output.append(result)

            return output

        def _convert_to_v1(input) -> list:
            """Convert v3 output to v1 schema."""

            output = []
            for k1, v1 in input['childNodes'].items():
                if k1 != 'WeatherData':
                    for k2, device in v1['childNodes'].items():
                        if device['addr'] != '1':
                            result = {}
                            result['id'] = device['addr']
                            node = device['childNodes']['_cfg']['childValues']
                            if node:
                                result['type'] = node['name']['val']
                                result['sku'] = node['sku']['val']
                            else:
                                result['type'] = None

                            tmp = device['childValues']['location']['val']
                            if tmp:
                                result['assignedZones'] = [{'name': tmp}]
                            else:
                                result['assignedZones'] = [{'name': None}]

                            result['status'] = {}

                            output.append(result)

            return output

        # getDeviceList = x.get("/v3/data_manager", {username: e, password: t})
        url = 'devices' if self._api_v1 else 'data_manager'
        raw_json = await self._request("GET", url)
        raw_json = raw_json if self._api_v1 else raw_json['data']

        self._devices = raw_json if self._api_v1 else _convert_to_v1(raw_json)
        self._devices.sort(key=lambda s: s['id'])

        _LOGGER.debug("GeniusHub.devices = %s", self._devices)
        return raw_json if self._client._verbose else self._devices

    @property
    async def devices(self) -> list:
        """Return a list of Devices known to the Hub."""

        if not self._devices:
            await self._get_devices
        return self._devices

    @property
    async def _get_issues(self) -> list:
        """Return a list of currently identified issues with the system.

          This is a v1 API: GET /issues
        """
        def _convert_to_v1(input) -> list:
            """Convert v3 output to v1 schema."""
            output = []
            for zone in input['data']:
                for issue in zone['lstIssues']:
                    message = DESCRIPTION_TO_TEXT[issue['id']]

                    tmp = {}
                    tmp['description'] = message.format(zone['strName'])
                    tmp['level'] = LEVEL_TO_TEXT[issue['level']]

                    output.append(tmp)

            return output

        # url = 'issues' if self._api_v1 else 'zones'
        raw_json = await self._request("GET", 'issues')

        self._issues = raw_json if self._api_v1 else _convert_to_v1(raw_json)

        _LOGGER.debug("GeniusHub.issues = %s", self._issues)
        return raw_json if self._client._verbose else self._issues

    @property
    async def issues(self) -> list:
        """Return a list of Issues known to the Hub."""

        if not self._issues:
            await self._get_issues
        return self._issues


class GeniusZone(GeniusObject):
    def __init__(self, client, hub, zone_dict):
        _LOGGER.debug("GeniusZone(hub=%s, zone=%s)", hub.id, zone_dict['id'])
        super().__init__(client, data=zone_dict)

        self._hub = hub

    @property
    async def info(self) -> dict:
        """Return information for a zone.

          This is a v1 API: GET /zones/{zoneId}
        """
        url = 'zones/{}'
        self._detail = await self._request("GET", url.format(self.id))

        _LOGGER.debug("self.detail = %s", self._detail)
        return self._detail

    @property
    async def devices(self) -> list:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        url = 'zones/{}/devices'
        self._devices = await self._request("GET", url.format(self.id))

        await self._populate_devices(self._devices)

        _LOGGER.debug("self.devices = %s", self._devices)
        return self._devices

    async def set_mode(self, mode):
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        _LOGGER.debug("set_mode(Zone): mode=%s")
        url = 'zones/{}/mode'
        self._detail = await self._request("PUT", url.format(self.id))

        _LOGGER.debug("set_mode(Zone): done")

    async def set_override(self, duration, setpoint):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        _LOGGER.debug("set_override_temp(%s): duration=%s, setpoint=%s", self.id, duration, setpoint)

        url = 'zones/{}/override'
        payload = {'duration': duration, 'setpoint': setpoint}
        self._detail = await self._request("POST", url.format(self.id), payload=payload)

        _LOGGER.debug("set_override_temp(%s): done.", self.id)

    async def update(self):
        """Update the zone with the latest state data."""
        _LOGGER.debug("Zone(%s).update()", self.id)
        print("Zone(%s).update()", self.id)


class GeniusDevice(GeniusObject):
    def __init__(self, client, hub, zone, device_dict):
        _LOGGER.debug("GeniusDevice(hub=%s, device=%s)", hub.id, device_dict['id'])
        super().__init__(client, data=device_dict)

        self._hub = hub
        self._zone = zone

    @property
    async def info(self) -> dict:
        """Return all information for a device."""
        url = 'devices/{}'
        self._detail = await self._request("GET", url.format(self.id))

        temp = dict(self._detail)
        if not self._verbose:
            del temp['assignedZones']

        _LOGGER.debug("self.detail = %s", temp)
        return temp

    @property
    async def location(self) -> dict:  # aka assignedZones
        raise NotImplementedError()
