"""Python client library for the Genius Hub API.

see: https://my.geniushub.co.uk/docs
"""
import asyncio
from hashlib import sha256
import logging
from types import SimpleNamespace

import aiohttp

HTTP_OK = 200  # cheaper than: from http import HTTPStatus.OK

DEFAULT_TIMEOUT_V1 = 30
DEFAULT_TIMEOUT_V3 = 10

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
zone_types = SimpleNamespace(
    Manager = 1,
    OnOffTimer = 2,
    ControlSP = 3,
    ControlOnOffPID = 4,
    TPI = 5,
    Surrogate = 6
)
zone_modes = SimpleNamespace(
    Off = 1,
    Timer = 2,
    Footprint = 4,
    Away = 8,
    Boost = 16,
    Early = 32,
    Test = 64,
    Linked = 128,
    Other = 256
)
kit_types = SimpleNamespace(
    Temp = 1,
    Valve = 2,
    PIR = 4,
    Power = 8,
    Switch = 16,
    Dimmer = 32,
    Alarm = 64,
    GlobalTemp = 128,
    Humidity = 256,
    Luminance = 512
)
zone_flags = SimpleNamespace(
    Frost = 1,
    Timer = 2,
    Footprint = 4,
    Boost = 8,
    Away = 16,
    WarmupAuto = 32,
    WarmupManual = 64,
    Reactive = 128,
    Linked = 256,
    WeatherComp = 512,
    Temps = 1024,
    TPI = 2048
)

ITYPE_TO_TYPE = {
    zone_types.Manager: 'manager',
    zone_types.OnOffTimer: 'on / off',
    zone_types.ControlSP: 'radiator',
    zone_types.ControlOnOffPID: 'type 4',
    zone_types.TPI: 'hot water temperature',
    zone_types.Surrogate: 'type 6',
}  # also: 'group', 'wet underfloor'
IMODE_TO_MODE = {
    zone_modes.Off: 'off',
    zone_modes.Timer: 'timer',
    zone_modes.Footprint: 'footprint',
    zone_modes.Away: 'away',
    zone_modes.Boost: 'override',
    zone_modes.Early: 'early',
    zone_modes.Test: 'test',
    zone_modes.Linked: 'linked',
    zone_modes.Other: 'other'
}  # or: 16: 'boost'?

LEVEL_TO_TEXT = {
    0: 'error',
    1: 'warning',
    2: 'information'
}
DESCRIPTION_TO_TEXT = {
    "node:no_comms":
        "The device has lost communication with the Hub",
    "node:not_seen":
        "The device has not been found by the Hub",
    "node:low_battery":
        "The battery is dead and needs to be replaced",
    "node:warn_battery":
        "the battery is low",
    "manager:no_boiler_controller":
        "The hub does not have a boiler controller assigned",
    "manager:no_boiler_comms":
        "The hub has lost communication with the boiler controller",
    "manager:no_temp":
        "The hub does not have a valid temperature",
    "manager:weather_data":
        "Weather data -",
    "zone:using_weather_temp":
        "The {} zone is currently using the outside temperature",
    "zone:using_assumed_temp":
        "The {} zone is currently using the assumed temperature",
    "zone:tpi_no_temp":
        "The {} zone has no valid temperature sensor",
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
                tmp['name'] = zone['strName']
                tmp['type'] = ITYPE_TO_TYPE[zone['iType']]
                tmp['mode'] = IMODE_TO_MODE[zone['iMode']]

                if zone['iType'] in [zone_types.ControlSP,
                                     zone_types.TPI]:
                    tmp['temperature'] = zone['fPV']
                    tmp['setpoint'] = zone['fSP']

                if zone['iType'] == zone_types.OnOffTimer:
                    tmp['setpoint'] = zone['fSP'] != 0

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
        # self._zones = raw_json if self._api_v1 else raw_json

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
