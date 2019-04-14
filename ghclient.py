"""
Usage: ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] [(zones | devices)] [-v | -vv | -vvv ]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] [(issues | reboot)]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE [devices] [-v | -vv | -vvv ]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE --mode=MODE
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE --temp=TEMP [--secs=SECS]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --device=DEVICE [-v | -vv | -vvv ]

Connect to a Genius Hub and interact with it, a Zone, or a Device.

Arguments:
  HUB-ID  either a Hub token, or a Hub hostname/address (needs user credentials)
    If a token is provided, then v1 API calls are made, otherwise v3 API calls

  COMMAND  the operation to perform: zones, devices, issues...
    If no COMMAND is provided, the entity's properties will be displayed.

Options:
  If a USERNAME is provided, the HUB-ID must be hostname/IP address:
    -u USERNAME --user=USERNAME    the username
    -p PASSWORD --pass=PASSWORD    the password

  Operations on a Zone:
    -z ZONE --zone=ZONE            the identifer of a Zone
    -m MODE --mode=MODE            one of: off, timer, footprint, override
    -s SECS --secs=SECS            the override duration in seconds
    -t TEMP --temp=TEMP            the override temperature in Celsius

  Operations on a Device:
    -d DEVICE --device=DEVICE      the identifer of a Device

  If no COMMAND is used, the entity's properties will be displayed:
    -v -vv -vvv                    increasing verbosity, -vvv gives raw JSON

Examples:
  ghclient.py HUB_ID
    Display information about the Hub.

  ghclient.py HUB_ID zones -v
    Display detailed information about all Zones.

  ghclient.py HUB_ID -z 3 off
    Turn Zone 3 off.

  ghclient.py HUB_ID -z 12 -d 3600 -t 19.5
    Set the override temperature for Zone 12 to 19.5C for 1 hour..

"""

import asyncio
import json
import logging

import aiohttp
from docopt import docopt

from geniushubclient import GeniusHubClient, GeniusHub

_LOGGER = logging.getLogger(__name__)


HUB_ID = 'HUB-ID'
ZONE_ID = '--zone'
DEVICE_ID = '--device'
USERNAME = '--user'
PASSWORD = '--pass'
MODE = '--mode'
SECS = '--secs'
TEMP = '--temp'

DEVICES = 'devices'
ISSUES = 'issues'
REBOOT = 'reboot'
ZONES = 'zones'

VERBOSE = '-v'

async def main(loop):
    """Return the JSON as requested."""
    _LOGGER.debug("main()")

    args = docopt(__doc__)
    # print(args)

    session = aiohttp.ClientSession()

    client = GeniusHubClient(hub_id=args[HUB_ID],
                             username=args[USERNAME],
                             password=args[PASSWORD],
                             session=session)

    hub = client.hub
    await hub.update()  # enumerate all zones and devices
    # print(await hub.zones)
    # print(await hub.devices)
    # return

    if args[ZONE_ID]:
        try:  # is zone_is a Int or a Str?
            key = int(args[ZONE_ID])
        except ValueError:  # it's a Str
            key = args[ZONE_ID]
            find_zone_by_key = hub.zone_by_name
        else: # it's an Int
            find_zone_by_key = hub.zone_by_id

        try:  # does this zone exist?
            zone = find_zone_by_key[key]
        except KeyError:  #  no, Zone ID not found
            raise  # TODO:

        if args[ISSUES]:
            print(await zone.issues)

        elif args[DEVICES]:
            if args[VERBOSE] > 2:
                print(zone._devices_raw)
            else:
                keys = ['id', 'type']  # as per /v1/devices/summary
                if args[VERBOSE] > 0:
                    keys += ['assignedZones']
                if args[VERBOSE] > 1:  # as per /v1/devices
                    keys += ['state']

                for device in sorted(zone.devices, key=lambda k: k['id']):
                    # display only the wanted keys
                    print({k: device[k] for k in keys if k in device})

        elif args[MODE]:
            # await zone.set_mode()
            print("Sorry: not implemented yet.")

        elif args[TEMP]:
            # await zone.set_override()
            print("Sorry: not implemented yet.")

        else:  # as per args[INFO]
            if args[VERBOSE] > 2:
                print(dir(zone))
                print(zone._dict_raw)
            else:
                print(zone.info)

    elif args[DEVICE_ID]:
        key = args[DEVICE_ID]  # Zone IDs are Strs, not Ints

        try:  # does this Device exist?
            device = hub.device_by_id[key]
        except KeyError:  # no, Device ID not found
            raise  # TODO:

        if args[ISSUES]:
            print(await zone.issues)

        else:  # as per args[INFO]
            print(device.info)

    else:  # as per args[HUB_ID]
        if args[ISSUES]:
            print(await hub.issues)

        elif args[ZONES]:
            if args[VERBOSE] > 2:
                print(hub._zones_raw)
            else:
                keys = ['id', 'name']  # same as /v1/zones/summary
                if args[VERBOSE] > 0:
                    keys += ['type', 'temperature', 'setpoint', 'mode',
                            'occupied', 'override']
                if args[VERBOSE] > 1:  # same as /v1/zones
                    keys += ['schedule']

                # for zone in sorted(hub.zones, key=lambda k: k['id']):
                #     # display only the wanted keys
                #     print({k: zone[k] for k in keys if k in zone})

                result = [{k: zone[k] for k in keys if k in zone}
                             for zone in hub.zones]
                print(json.dumps(result))

        elif args[DEVICES]:
            if args[VERBOSE] > 2:
                print(hub._devices_raw)
            else:
                keys = ['id', 'type']  # same as /v1/devices/summary
                if args[VERBOSE] > 0:
                    keys += ['assignedZones']
                if args[VERBOSE] > 1:  # same as /v1/devices
                    keys += ['state']

                # for device in sorted(hub.devices, key=lambda k: k['id']):
                #     # display only the wanted keys
                #     print({k: device[k] for k in keys if k in device})

                result = [{k: device[k] for k in keys if k in device}
                             for device in hub.devices]
                print(json.dumps(result))

        elif args[REBOOT]:
            # await hub.reboot()
            print("Sorry: not implemented yet.")

        else:  # as per args[INFO]
            print(await hub.info)

    await session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
