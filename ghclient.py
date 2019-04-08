"""
Usage: ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] [(zones | devices | issues)] [-v | -vv | --raw]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] reboot
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE [-v | -vv | --raw]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE --mode=MODE
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE [--secs=SECS] [--temp=TEMP]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --device=DEVICE [-v | -vv | --raw]

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
    -v -vv                         increasing verbosity
    -r --raw                       display the raw JSON

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

ZONES = 'zones'
DEVICES = 'devices'
REBOOT = 'reboot'

VERBOSE = '-v'
RAW_JSON = '--raw'

async def main(loop):
    """Return the JSON as requested."""
    _LOGGER.debug("main()")

    args = docopt(__doc__)
    print(args)

    session = aiohttp.ClientSession()

    client = GeniusHubClient(hub_id=args[HUB_ID],
                             username=args[USERNAME],
                             password=args[PASSWORD],
                             session=session)

    # client.verbose = False if args.verbose is None else args.verbose > 3

    hub = client.hub
    await hub.update()

    if args[ZONE_ID]:
        zone = hub.zone_by_id[args.zone]

    if args[DEVICES]:
        if args[RAW_JSON]:
            pass
        else:
            keys = ['id', 'name']  # same as /v1/zones/summary
            if args[VERBOSE] > 0:
                keys += ['type', 'temperature', 'setpoint', 'mode',
                        'occupied', 'override']
            if args[VERBOSE] > 1:
                keys += ['schedule']  # same as /v1/zones

        # display only the wanted keys
        devices = []
        print({k: v for k in keys for zone})

    elif args[ISSUES]:
        # print(await hub.issues)
        print("Sorry: not implemented yet.")

    elif args[REBOOT]:
        # await hub.reboot()
        print("Sorry: not implemented yet.")

    else:  # args[INFO]
        # print(await hub.info)
        print("Sorry: not implemented yet.")



        if not args.command or args.command == "info":
            print(await zone.info)

        elif args.command == "issues":
            print("Sorry: not implemented yet.")
            # print(await zone.issues)

        elif args.command == "devices":
           print(await zone.devices)

        elif args.command == "mode":
            await zone.set_mode(args.subcommand)

        elif args.command == "override":
            await zone.set_override()

    elif args[DEVICE_ID]:
        print("Sorry: not implemented yet.")
        return False

        device = hub.device(id=args.device)
        device.verbose = 0 if args.verbose is None else args.verbose

        if args.command == "detail":
            print(await device.detail)
        else:
            print("Error: unknown command: {}".format(args.command))

    else:
        if args[ZONES]:
            if args[RAW_JSON]:
                pass
            else:
                keys = ['id', 'name']  # same as /v1/zones/summary
                if args[VERBOSE] > 0:
                    keys += ['type', 'temperature', 'setpoint', 'mode',
                            'occupied', 'override']
                if args[VERBOSE] > 1:
                    keys += ['schedule']  # same as /v1/zones

            # display only the wanted keys
            zones = []
            for zone in await hub.zones:
                zones.append({k: zone[k] for k in keys if k in zone})
            print(zones)

        elif args[DEVICES]:
            if args[RAW_JSON]:
                pass
            else:
                keys = ['id', 'type']  # same as /v1/devices/summary
                if args[VERBOSE] > 0:
                    keys += ['assignedZones']
                if args[VERBOSE] > 1:
                    keys += ['state']  # same as /v1/devices

            # display only the wanted keys
            devices = []
            for device in await hub.devices:
                devices.append({k: device[k] for k in keys if k in device})
            print(devices)

        elif args[ISSUES]:
            # print(await hub.issues)
            print("Sorry: not implemented yet.")

        elif args[REBOOT]:
            # await hub.reboot()
            print("Sorry: not implemented yet.")

        else:  # args[INFO]
            # print(await hub.info)
            print("Sorry: not implemented yet.")

    await session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
