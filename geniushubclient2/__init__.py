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

ZONE_MODE_MAP = {
    1: 'off',
    2: 'timer',
    4: 'footprint',
    8: 'away',
    16: 'boost',
    32: 'early',
    64: 'test',
    128: 'linked',
    256: 'other'
}

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

    async def _test1(self, type, url):
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
                 interval=None, session=None, eventloop=None):
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
            self._poll_interval = interval if interval else DEFAULT_INTERVAL_V1

        # if credentials, then hub_id is name/address for v3 API
        else:
            hash = sha256()
            hash.update((username + password).encode('utf-8'))
            self._auth = aiohttp.BasicAuth(
                login=username, password=hash.hexdigest())
            self._url_base = 'http://{}:1223/v3'.format(hub_id)
            self._headers = None
            self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_V3)
            self._poll_interval = interval if interval else DEFAULT_INTERVAL_V3

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
    async def version(self) -> str:
        """Return the current software version(s) of the system.

        This is a v1 API: GET /version
          200 OK.
          401 The authorization information is missing or invalid.
          502 The hub is offline.
        """
        url = '{}/version'.format(self._url_base)
        self._version = await self._test1("GET", url)

        _LOGGER.debug("self._version = %s", self._version)
        return self._version if self._verbose else self._version['hubSoftwareVersion']

    @property
    async def zones(self) -> list:
        """Return a list of zones inluded in the system.

          This is a v1 API:
            GET /zones (all information),
            GET /zones/summary (ID, name, type)

          Verbose for Zones:
            v0 = id, name (a.k.a. v1/zones/summary)
            v1 + type, mode, temperature, setpoint, occupied, override
            v2 + schedule (v1/zones)
            v3 = RAW JSON
        """

        def _convert(input) -> list:
            """Convert v3 output to v1 schema."""
            XXXX = {
                'id': 'iID',
                'name': 'strName',
                'type': 'iType',
                'mode': 'iMode',  # 1 - off, 2 - timer, 16 - Override 4 - footprint,
                'temperature': 'fPV',
                'setpoint': 'fSP',
                # 'occupied': true/false,
                # 'override': { "duration": 0, "setpoint": 16 },
                # 'schedule': {
                #     'timer': {'weekly': {}},
                #     'footprint': {'weekly': {}}
                # },
            }

            itype_to_type = {
                '1': 'manager',
                '2': 'on /off',
                '3': 'radiator',
                '4': 'type 4',
                '5': 'hot water temperature',
            }  # also: group, wet underfloor

            imode_to_mode = {
                '1': 'off',
                '2': 'timer',
                '4': 'footprint',
                '8': 'mode 8',
                '16': 'override',
            }

            output = []
            for zone in input['data']:
                temp = {}
                temp['id'] = zone['iID']
                temp['name'] = zone['strName']
                temp['type'] = itype_to_type[str(zone['iType'])]
                temp['mode'] = imode_to_mode[str(zone['iMode'])]

                if temp['type'] in ['radiator', 'hot water temperature']:
                    temp['temperature'] = zone['fPV']
                    temp['setpoint'] = zone['fSP']

                if temp['type'] in ['radiator']:
                    temp['occupied'] = 'Unknown'  # but not all types, ?zoneReactive

                if temp['type'] in ['on /off']:
                    temp['setpoint'] = 'False?'

                if temp['type'] in ['radiator', 'hot water temperature']:
                    temp['override'] = {}
                    temp['override']['duration'] = zone['iBoostTimeRemaining']
                    temp['override']['setpoint'] = zone['fBoostSP']
                    # temp['override']['iOverrideDuration'] = zone['iOverrideDuration']
                    # temp['override']['fOverrideTemp'] = zone['fOverrideTemp']
                    # temp['override']['iOverrideMode'] = zone['iOverrideMode']

                if temp['type'] in ['on /off']:
                    temp['override'] = {}
                    temp['override']['duration'] = zone['iBoostTimeRemaining']
                    temp['override']['setpoint'] = zone['fBoostSP'] != 0  # 1=True=On/0=False=Off?

                output.append(temp)
            return output

        url = '{}/zones'
        # url = '{}/zones' if self._verbose > 0 else '{}/zones/summary'
        self._zones = await self._test1("GET", url.format(self._url_base))

        if self._verbose > 3:  # no format, leave as raw json
            temp = self._zones
        else:  #  format as per v1 api
            if 'v3' in self._url_base:
                temp = _convert(self._zones)
            else:
                temp = self._zones

            if self._verbose > 2:  # -v3
                keys = ['schedule']
                for zone in temp:
                    for key in keys:
                        zone.pop(key, None)

            else:
                keys = ['id', 'name']

                if self._verbose > 0:  # -v1, -v2
                    keys = keys + ['type', 'mode', 'temperature', 'setpoint']

                if self._verbose > 1:  # -v3
                    keys = keys + ['occupied', 'override']

                xxxx = []
                for zone in temp:
                    xxxx.append({key: zone[key] for key in zone if key in keys})
                temp = xxxx

        _LOGGER.debug("self.zones = %s", temp)
        return temp

    @property
    async def devices(self) -> list:
        """Return a list of devices inlcuded in the system.

          This is a v1 API:
            GET /devices (all information),
            GET /devices/summary (ID, name, type)

          Verbose for Devices:
            v0 = id, name (a.k.a. v1/zones/summary)
            v1 + type, mode, temperature, setpoint, occupied, override
            v2 + schedule (v1/zones)
            v3 = RAW JSON
        """
        url = '{}/devices' if self._verbose else '{}/devices/summary'
        self._devices = await self._test1("GET", url.format(self._url_base))

        _LOGGER.debug("self.devices = %s", self._devices)
        return self._devices

    @property
    async def issues(self) -> list:
        """Return a list of currently identified issues.

          This is a v1 API:
            GET /issues
        """
        url = '{}/issues'.format(self._url_base)
        self._issues = await self._test1("GET", url)

        _LOGGER.debug("self.issues = %s", self._issues)
        return self._issues


class GeniusZone(GeniusObject):
    def __init__(self, id):
        _LOGGER.debug("__init__(id=%s)", id)
        super().__init__()

        self._id = id

    @property
    async def detail(self) -> dict:
        """Return information for a zone.

        This is a v1 API: GET /zones/{zoneId}/summary (ID, name, type)
        This is a v1 API: GET /zones/{zoneId} (all information),
          200 OK.
          401 The authorization information is missing or invalid.
          404 No zone with the specified ID was not found.
          502 The hub is offline.
        """
        url = '{}/zones/{}' if self._verbose else '{}/zones/{}/summary'
        self._detail = await self._test1("GET", url.format(self._url_base, self._id))

        _LOGGER.debug("self.detail = %s", self._detail)
        return self._detail

    @property
    async def devices(self) -> list:
        """Return information for devices assigned to a zone.

        This is a v1 API: GET /zones/{zoneId}/devices/summary (ID, type)
        This is a v1 API: GET /zones/{zoneId}devices (all information),
          200 OK.
          401 The authorization information is missing or invalid.
          404 No zone with the specified ID was not found.
          502 The hub is offline.
        """
        url = '{}/zones/{}/devices' if self._verbose else '{}/zones/{}/devices/summary'
        self._devices = await self._test1("GET", url.format(self._url_base, self._id))

        _LOGGER.debug("self.devices = %s", self._devices)
        return self._devices

    async def set_mode(self, mode):
        """Set the mode of the zone.

        mode is in {'off', 'timer', footprint', 'override'}
        """
        _LOGGER.debug("set_mode(Zone): mode=%s")
        url = '{}zones/{}/mode'
        self._detail = await self._test1("PUT", url.format(self._url_base, self._id))

        _LOGGER.debug("set_mode(Zone): done")

    async def set_override(self, duration, setpoint):
        """Set the zone to override to a certain temperature.

        duration is in seconds
        setpoint is in degrees Celsius
        """
        _LOGGER.debug("set_override_temp(Zone): duration=%s, setpoint=%s", duration, setpoint)
        url = '{}zones/{}/override'
        self._detail = await self._test1("POST", url.format(self._url_base, self._id))

        _LOGGER.debug("set_override_temp(Zone): done.")

    @property
    async def name(self):
        raise NotImplementedError()

    @property
    async def type(self):
        raise NotImplementedError()

    @property
    async def temperature(self):
        raise NotImplementedError()

    @property
    async def occupied(self) -> bool:
        raise NotImplementedError()

    @property
    async def schedule(self) -> bool:
        raise NotImplementedError()

    @property
    async def mode(self) -> bool:
        raise NotImplementedError()

    @property
    async def mode(self) -> bool:
        raise NotImplementedError()

    @staticmethod
    def GET_ZONE_MODE(zone):
        return ZONE_MODE_MAP.get(zone['iMode'], "off")


class GeniusDevice(GeniusObject):
    def __init__(self, id):
        _LOGGER.debug("__init__(id=%s)", id)
        super().__init__(id)

        self._id = id

    @property
    async def detail(self) -> dict:
        """Return all information for a device."""
        url = '{}/devices/{}'
        self._detail = await self._test1("GET", url.format(self._url_base, self._id))

        temp = dict(self._detail)
        if not self._verbose:
            del temp['assignedZones']

        _LOGGER.debug("self.detail = %s", temp)
        return temp

    @property
    async def type(self):
        raise NotImplementedError()

    @property
    async def location(self):
        raise NotImplementedError()

    @property
    async def state(self):
        raise NotImplementedError()
