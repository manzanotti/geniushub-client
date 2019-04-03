"""Python client library for the Genius Hub API.

see: https://my.geniushub.co.uk/docs
"""
import asyncio
from hashlib import sha256
import logging
from types import SimpleNamespace

import aiohttp

HTTP_OK = 200  # cheaper than: from http import HTTPStatus.OK

from .const import (
    API_STATUS_ERROR,
    DEFAULT_INTERVAL_V1, DEFAULT_INTERVAL_V3,
    DEFAULT_TIMEOUT_V1, DEFAULT_TIMEOUT_V3,
    ITYPE_TO_TYPE, IMODE_TO_MODE,
    LEVEL_TO_TEXT, DESCRIPTION_TO_TEXT,
    zone_types, zone_modes, kit_types, zone_flags)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)

class GeniusObject(object):
    def __init__(self, id):
        self._verbose = False

    @property
    def verbose(self) -> int:
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = 0 if value is None else value

    async def _handle_assetion(self, error):
        _LOGGER.debug("_handle_assetion(type=%s, url=%s)", type, url)

    async def _request(self, type, url):
        _LOGGER.debug("_request(type=%s, url=%s)", type, url)

        async with self._session as session:
            if type == "GET":
                async with session.get(
                    url, headers=self._headers,
                    auth=self._auth, timeout=self._timeout
                ) as response:
                    assert response.status == HTTP_OK, response.text
                    return await response.json(content_type=None)
            elif type == "PATCH":
                async with session.patch(url) as response:
                    assert response.status == HTTP_OK, response.text
                    return await response.json(content_type=None)
            elif type == "POST":
                async with session.post(url) as response:
                    assert response.status == HTTP_OK, response.text
                    return await response.json(content_type=None)
            elif type == "PUT":
                async with session.put(url) as response:
                    assert response.status == HTTP_OK, response.text
                    return await response.json(content_type=None)

    @staticmethod
    def LookupStatusError(status):
        return API_STATUS_ERROR.get(status, str(status) + " Unknown status")


class GeniusHub(GeniusObject):
    def __init__(self, hub_id, username=None, password=None,
                 session=None, eventloop=None):
        _LOGGER.debug("GeniusHub(hub_id=%s)", hub_id)
        super().__init__(hub_id)

        # use existing session/loop if provided
        self._session = eventloop if session else aiohttp.ClientSession()
        self._loop = eventloop if eventloop else asyncio.new_event_loop()

        # if no credentials, then hub_id is a token for v1 API
        self._api_v1 = not (username or password)

        if self._api_v1:
            self._auth = None
            self._url_base = 'https://my.geniushub.co.uk/v1'
            self._headers = {'authorization': "Bearer " + hub_id}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)
            self._poll_interval = DEFAULT_INTERVAL_V1

        else:  # using API ver3
            hash = sha256()
            hash.update((username + password).encode('utf-8'))
            self._auth = aiohttp.BasicAuth(
                login=username, password=hash.hexdigest())
            self._url_base = 'http://{}:1223/v3'.format(hub_id)
            self._headers = None
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
            self._poll_interval = DEFAULT_INTERVAL_V3

        self._zones = self._devices = None

    @property
    async def detail(self) -> dict:
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
            url = '{}/version'.format(self._url_base)
            self._version = await self._request("GET", url)
        else:
            self._version = {
                'hubSoftwareVersion': 'unable to determine via v3 API'
            }

        _LOGGER.debug("self._version = %s", self._version)
        return self._version

    @property
    async def zones(self) -> list:
        """Return a list of zones included in the system.

          This is a v1 API: GET /zones
        """
        def _convert_to_v1(input) -> list:
            """Convert v3 output to v1 schema."""
            output = []
            for zone in input['data']:
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
                    c = zone['iActivity'] | 0
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

        url = '{}/zones'
        raw_json = await self._request("GET", url.format(self._url_base))

        self._zones = raw_json if self._api_v1 else _convert_to_v1(raw_json)

        _LOGGER.debug("GeniusHub.zones = %s", self._zones)
        return self._zones

    @property
    async def devices(self) -> list:
        """Return a list of devices included in the system.

          This is a v1 API: GET /devices
        """
        def _convert_to_v1(input) -> list:
            """Convert v3 output to v1 schema."""

            this_list = []
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
                        this_list.append(result)

            this_list.sort(key=lambda s: int(s['id']))
            return this_list

        url = '{}/devices' if self._api_v1 else '{}/zones'
        raw_json = await self._request("GET", url.format(self._url_base))

        self._devices = raw_json if self._api_v1 else _convert_to_v1(raw_json)

        _LOGGER.debug("GeniusHub.devices = %s", self._devices)
        return self._devices

    @property
    async def issues(self) -> list:
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

        url = '{}/issues' if self._api_v1 else '{}/zones'
        raw_json = await self._request("GET", url.format(self._url_base))

        self._issues = raw_json if self._api_v1 else _convert_to_v1(raw_json)

        _LOGGER.debug("GeniusHub.issues = %s", self._issues)
        return self._issues


class GeniusZone(GeniusObject):
    def __init__(self, id):
        _LOGGER.debug("__init__(id=%s)", id)
        super().__init__()

        self._id = id

    @property
    async def detail(self) -> dict:
        """Return information for a zone.

          This is a v1 API: GET /zones/{zoneId}
        """
        url = '{}/zones/{}' if self._verbose else '{}/zones/{}/summary'
        self._detail = await self._request("GET", url.format(self._url_base, self._id))

        _LOGGER.debug("self.detail = %s", self._detail)
        return self._detail

    @property
    async def devices(self) -> list:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        url = '{}/zones/{}/devices' if self._verbose else '{}/zones/{}/devices/summary'
        self._devices = await self._request("GET", url.format(self._url_base, self._id))

        _LOGGER.debug("self.devices = %s", self._devices)
        return self._devices

    async def set_mode(self, mode):
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        _LOGGER.debug("set_mode(Zone): mode=%s")
        url = '{}zones/{}/mode'
        self._detail = await self._request("PUT", url.format(self._url_base, self._id))

        _LOGGER.debug("set_mode(Zone): done")

    async def set_override(self, duration, setpoint):
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        _LOGGER.debug("set_override_temp(Zone): duration=%s, setpoint=%s", duration, setpoint)
        url = '{}zones/{}/override'
        self._detail = await self._request("POST", url.format(self._url_base, self._id))

        _LOGGER.debug("set_override_temp(Zone): done.")

    @property
    async def id(self) -> int:
        raise NotImplementedError()

    @property
    async def name(self) -> str:
        raise NotImplementedError()

    @property
    async def type(self) -> str:
        raise NotImplementedError()

    @property
    async def mode(self) -> str:
        raise NotImplementedError()

    @property
    async def temperature(self) -> float:
        raise NotImplementedError()

    @property
    async def setpoint(self):
        raise NotImplementedError()

    @property
    async def occupied(self) -> bool:
        raise NotImplementedError()

    @property
    async def override(self) -> dict:
        raise NotImplementedError()

    @property
    async def schedule(self) -> dict:
        raise NotImplementedError()


class GeniusDevice(GeniusObject):
    def __init__(self, id):
        _LOGGER.debug("__init__(id=%s)", id)
        super().__init__(id)

        self._id = id

    @property
    async def detail(self) -> dict:
        """Return all information for a device."""
        url = '{}/devices/{}'
        self._detail = await self._request("GET", url.format(self._url_base, self._id))

        temp = dict(self._detail)
        if not self._verbose:
            del temp['assignedZones']

        _LOGGER.debug("self.detail = %s", temp)
        return temp

    @property
    async def id(self) -> str:
        raise NotImplementedError()

    @property
    async def type(self) -> str:
        raise NotImplementedError()

    @property
    async def location(self) -> dict:  ## aka assignedZones
        raise NotImplementedError()

    @property
    async def state(self) -> dict:
        raise NotImplementedError()
