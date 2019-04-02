"""Python client library for the Genius Hub API.

see: https://my.geniushub.co.uk/docs
"""
import asyncio
from hashlib import sha256
import logging

import aiohttp

HTTP_OK = 200  # cheaper than: from http import HTTPStatus.OK

DEFAULT_TIMEOUT_V1 = 10
DEFAULT_TIMEOUT_V3 = 60

DEFAULT_INTERVAL_V1 = 300
DEFAULT_INTERVAL_V3 = 30

API_STATUS_ERROR = {
    400: "The request body or request parameters are invalid.",
    401: "The authorization information is missing or invalid.",
    404: "No zone/device with the specified ID was found "
         "(or the state property does not exist on the specified device).",
    502: "The hub is offline.",
    503: "The authorization information is invalid.",
}
ITYPE_TO_TYPE = {
    1: 'manager',
    2: 'on / off',
    3: 'radiator',
    4: 'type 4',
    5: 'hot water temperature',
}  # also: 'group', 'wet underfloor'
IMODE_TO_MODE = {
    1: 'off',
    2: 'timer',
    4: 'footprint',
    8: 'away',
    16: 'override',
    32: 'early',
    64: 'test',
    128: 'linked',
    256: 'other'
}  # or: 16: 'boost'?

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
        _LOGGER.debug("_test2(type=%s, url=%s)", type, url)

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
        if username is None and password is None:
            self._auth = None
            self._url_base = 'https://my.geniushub.co.uk/v1'
            self._headers = {'authorization': "Bearer " + hub_id}
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V1)
            self._poll_interval = DEFAULT_INTERVAL_V1

        # if credentials, then hub_id is name/address for v3 API
        else:
            hash = sha256()
            hash.update((username + password).encode('utf-8'))
            self._auth = aiohttp.BasicAuth(
                login=username, password=hash.hexdigest())
            self._url_base = 'http://{}:1223/v3'.format(hub_id)
            self._headers = None
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
            self._poll_interval = DEFAULT_INTERVAL_V3

    @property
    async def detail(self) -> dict:
        """Return information for the hub.

          This is not a v1 API."""
        self._detail = {}

        async with self._session as session:

            url = '{}/zones' if self._verbose else '{}/zones/summary'
            async with session.get(url.format(self._url_base)) as response:
                assert response.status == HTTP_OK, response.status
                self._zones =  await response.json(content_type=None)

            self._detail = self._zones[0]
            if self._verbose:
                del self._detail['mode']
                del self._detail['schedule']

            url = '{}/version'.format(self._url_base)
            async with session.get(url) as response:
                assert response.status == HTTP_OK, response.status
                self._version =  await response.json(content_type=None)

        if self._verbose:
            self._detail.update(self._version)
        else:
            self._detail['version'] = self._version['hubSoftwareVersion']

        _LOGGER.debug("self._detail = %s", self._detail)
        return self._detail

    @property
    async def version(self) -> dict:
        """Return the current software version(s) of the system.

          This is a v1 API only.
        """
        if 'v3' in self._url_base:
            self._version = {
                'hubSoftwareVersion': 'unable to determine via v3 API'
            }
        else:
            url = '{}/version'.format(self._url_base)
            self._version = await self._request("GET", url)

        _LOGGER.debug("self._version = %s", self._version)
        return self._version

    @property
    async def zones(self) -> list:
        """Return a list of zones included in the system.

          This is a v1 API: GET /zones
        """
        def _convert_to_v1_response(input) -> list:
            """Convert v3 output to v1 schema."""
            output = []
            for zone in input['data']:
                tmp = {}
                tmp['id'] = zone['iID']
                tmp['name'] = zone['strName']
                tmp['type'] = ITYPE_TO_TYPE[zone['iType']]
                tmp['mode'] = IMODE_TO_MODE[zone['iMode']]

                if zone['iType'] in [3, 5]:
                    tmp['temperature'] = zone['fPV']
                    tmp['setpoint'] = zone['fSP']

                if zone['iType'] == 2:  # ITYPE_ON_OFF
                    tmp['setpoint'] = zone['fSP'] != 0

                if zone['iMode'] == 4:  # IMODE_FOOTPRINT
                    # tmp['occupied'] = zone['bIsActive'] - No!
                    # bTriggerOn, bTriggerOff -> Occupied
                    # False,      False       -> False
                    # False,      True        -> False
                    # True,       False       -> False
                    #
                    tmp['occupied'] = \
                        zone['objFootprint']['objReactive']['bTriggerOn']

                if zone['iType'] in [2, 3, 5]:
                    tmp['override'] = {}
                    tmp['override']['duration'] = zone['iBoostTimeRemaining']
                    tmp['override']['setpoint'] = zone['fBoostSP'] \
                        if zone['iType'] != 2 else (zone['fBoostSP'] != 0)

                if 'objFootprint' in zone:
                    tmp['objFootprint'] = zone['objFootprint']
                    del tmp['objFootprint']['lstSP']

                    tmp['schedule'] = {}

                output.append(tmp)

            return output

        url = '{}/zones'
        raw_json = await self._request("GET", url.format(self._url_base))

        if 'v3' in self._url_base:
            self._zones = _convert_to_v1_response(raw_json)
        else:
            self._zones = raw_json

        _LOGGER.debug("GeniusHub.zones = %s", self._zones)
        return self._zones

    @property
    async def devices(self) -> list:
        """Return a list of devices included in the system.

          This is a v1 API: GET /devices
        """
        def _convert_to_v1_response(input) -> list:
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

        url = '{}/zones' if 'v3' in self._url_base else '{}/devices'
        raw_json = await self._request("GET", url.format(self._url_base))

        if 'v3' in self._url_base:
            self._devices = _convert_to_v1_response(raw_json)
        else:
            self._devices = raw_json

        _LOGGER.debug("GeniusHub.devices = %s", self._devices)
        return self._devices

    @property
    async def issues(self) -> list:
        """Return a list of currently identified issues.

          This is a v1 API: GET /issues
        """
        url = '{}/issues'.format(self._url_base)
        self._issues = await self._request("GET", url)

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
    async def id(self):
        raise NotImplementedError()

    @property
    async def name(self):
        raise NotImplementedError()

    @property
    async def type(self):
        raise NotImplementedError()

    @property
    async def mode(self) -> bool:
        raise NotImplementedError()

    @property
    async def temperature(self):
        raise NotImplementedError()

    @property
    async def setpoint(self):
        raise NotImplementedError()

    @property
    async def occupied(self) -> bool:
        raise NotImplementedError()

    @property
    async def override(self) -> bool:
        raise NotImplementedError()

    @property
    async def schedule(self) -> bool:
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
    async def id(self):
        raise NotImplementedError()

    @property
    async def type(self):
        raise NotImplementedError()

    @property
    async def location(self):  ## aka assignedZones?
        raise NotImplementedError()

    @property
    async def state(self):
        raise NotImplementedError()
