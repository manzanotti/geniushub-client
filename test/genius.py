''' This module connects to the Genius hub and shares the data'''
import json
from hashlib import sha256 as hash
import aiohttp
import asyncio
import threading
import logging

_LOGGER = logging.getLogger(__name__)


class GeniusUtility:

    def __init__(self, ip_address, username, password, update=5):
        sha = hash()
        sha.update((username + password).encode('utf-8'))
        GeniusUtility._auth = aiohttp.BasicAuth(
            login=username, password=sha.hexdigest())
        GeniusUtility._UPDATE_INTERVAL = update
        GeniusUtility._STATUS = 200
        GeniusUtility._ip_address = "http://" + ip_address + ":1223/v3"
        GeniusUtility._t = threading.Thread(
            target=self.StartPolling, name="GeniusInitLink")
        GeniusUtility._t.daemon = True
        GeniusUtility._t.start()

    async def fetch(self, session, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url,
                                   auth=GeniusUtility._auth) as response:
                text = await response.text()
                return text, response.status

    async def getjson(self, identifier):
        ''' gets the json from the supplied zone identifier '''
        url = GeniusUtility._ip_address + identifier
        try:
            async with aiohttp.ClientSession() as session:
                text, status = await self.fetch(session, url)
                GeniusUtility._STATUS = status

                if status == 200:
                    GeniusUtility._results = json.loads(text)

        except Exception as ex:
            _LOGGER.error("Failed requests in getjson")
            _LOGGER.error(ex)
            return None

    def StartPolling(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.Polling())

    async def Polling(self):
        while True:
            await self.getjson('/zones')

            if not GeniusUtility._STATUS == 200:
                _LOGGER.error(
                    self.LookupStatusError(GeniusUtility._STATUS))
                if GeniusUtility._STATUS == 501:
                    break

            await asyncio.sleep(GeniusUtility._UPDATE_INTERVAL)

    def getAllZones(self):
        return GeniusUtility._results['data']

    def getZone(self, zoneId):
        for zone in GeniusUtility.getAllZones(self):
            if zone['iID'] == zoneId:
                return zone

        return None

    def getDevice(self, zoneId, addr):
        for node in self.getZone(zoneId)['nodes']:
            if node['addr'] == addr:
                return node['childValues']

        return None

    def getClimateList(self):
        return self.filterList(3, self.GET_CLIMATE)

    def getSwitchList(self):
        return self.filterList(2, self.GET_SWITCH)

    def filterList(self, typeId, paramsFunction):
        this_list = []
        for zone in self.getAllZones():
            if zone['iType'] == typeId:
                result = paramsFunction(zone)
                result['iID'] = zone['iID']
                result['name'] = zone['strName'].strip()
                this_list.append(result)

        return this_list

    def filterDeviceList(self, typeId, paramsFunction):
        this_list = []
        for zone in self.getAllZones():
            for node in zone['nodes']:
                if not node['addr'] == 'WeatherData':
                    cv = node['childValues']
                    if typeId in cv:
                        result = paramsFunction(cv)
                        result['iID'] = zone['iID']
                        result['addr'] = node['addr']
                        result['name'] = zone['strName'].strip()
                        result['index'] = len(
                            [x for x in this_list if x['name'] == result['name']])
                        this_list.append(result)

        return this_list

    def getSensorList(self):
        return self.filterDeviceList('LUMINANCE', self.getSensor)

    def getTRVList(self):
        return self.filterDeviceList('HEATING_1', self.getTRV)

    async def place(self, session, url, data):
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                    url,
                    auth=GeniusUtility._auth,
                    data=json.dumps(data)) as response:
                assert response.status == 200
                return response.status

    async def putjson(self, device_id, data):
        ''' puts the json data to the supplied zone identifier '''
        url = GeniusUtility._ip_address + '/zone/' + str(device_id)
        try:
            async with aiohttp.ClientSession() as session:
                status = await self.place(session, url, data)

            ''' refresh the results '''
            await self.getjson('/zones')
            return status == 200

        except Exception as ex:
            _LOGGER.error(self.LookupStatusError(GeniusUtility._STATUS))
            _LOGGER.error("Failed requests in putjson")
            _LOGGER.error(ex)
            return False

    @staticmethod
    def GET_CLIMATE(zone):
        return {
            'current_temperature': zone['fPV'],
            'target_temperature': zone['fSP'],
            'mode': GeniusUtility.GET_MODE(zone),
            'is_active': zone['bIsActive']}

    @staticmethod
    def GET_SWITCH(zone):
        return {'mode': GeniusUtility.GET_MODE(zone)}

    @staticmethod
    def getSensor(cv):
        return {
            'Battery': cv['Battery']['val'],
            'LUMINANCE': cv['LUMINANCE']['val'],
            'Motion': cv['Motion']['val'],
            'TEMPERATURE': cv['TEMPERATURE']['val']}

    @staticmethod
    def getTRV(cv):
        return {
            'Battery': cv['Battery']['val'],
            'TEMPERATURE': cv['HEATING_1']['val']}

    @staticmethod
    def GET_MODE(zone):
        # Mode_Off: 1,
        # Mode_Timer: 2,
        # Mode_Footprint: 4,
        # Mode_Away: 8,
        # Mode_Boost: 16,
        # Mode_Early: 32,
        # Mode_Test: 64,
        # Mode_Linked: 128,
        # Mode_Other: 256
        mode_map = {1: "off", 2: "timer", 4: "footprint",
                    8: "away", 16: "boost", 32: "early", }
        return mode_map.get(zone['iMode'], "off")

    @staticmethod
    def LookupStatusError(status):
        return {
            400: "400 The request body or request parameters are invalid.",
            401: "401 The authorization information is missing or invalid.",
            404: "404 No zone with the specified ID was not found.",
            502: "502 The hub is offline.",
            503: "503 The authorization information invalid.",
        }.get(status, str(status) + " Unknown status")
