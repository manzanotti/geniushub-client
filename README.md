# Genius
Python library to provide connect to Genius Hub on a local network.

# Installation
Either clone this resposition and run `python setup.py install`, or install from pip using `pip install genius`.

# API
This library makes use of the undocumented API for communicating to the Genius Hub. This API may change with future updates to the Genius Hub Firmware.

The library supports the following functions:
```
getClimateList()
getSwitchList()
getTRVList()
getSensorList()
getSwitchList()
getZone(zoneId)
getDevice(zoneId, addr)
GET_CLIMATE(zone)
GET_SWITCH(zone)
getSensor(cv)
getTRV(cv)
GET_MODE(zone)
putjson(device_id, data)

```

# Usage
Initialise a link to the hub by passing in the local IP address, username and password. The username and password are the same that you use to log into your Genius application. Once logged in successfully the module will poll the hub at regular intervals so that getting values from the hub will be cached locally.

What is read from the getters is self explanatory. The putjson POST the data to the Genius Hub. The format of the json can be discovered by exploring the Genius application and view the requests posted to the hub.
```
import asyncio
from genius import GeniusUtility

IP_ADDRESS = 'Your local ip address'
USERNAME = 'Your user name'
PASSWORD = 'Your password'
INTERVAL = 60


async def main():
    genius_utility = GeniusUtility(IP_ADDRESS, USERNAME, PASSWORD, INTERVAL)
    await genius_utility.getjson('/zones')

    # Get the zones with a temperature
    climate_list = genius_utility.getClimateList()

    print("Climate -------------------------------------------------------------")
    for zone in climate_list:
        print(zone)

    trvs = genius_utility.getTRVList()

    print("TRV -----------------------------------------------------------------")
    for trv in trvs:
        print(trv)

    switches = genius_utility.getSwitchList()

    print("Switches ------------------------------------------------------------")
    for switch in switches:
        print(switch)

    sensors = genius_utility.getSensorList()

    print("Sensors -------------------------------------------------------------")
    for sensor in sensors:
        print(sensor)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```