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
