"""
Usage: ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] [(zones | devices | info | issues)] [-v | -vv | -vvv ]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] reboot
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE [(devices | info | issues)] [-v | -vv | -vvv ]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE --mode=MODE
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --zone=ZONE --temp=TEMP [--secs=SECS]
       ghclient.py HUB-ID [(--user=USERNAME --pass=PASSWORD)] --device=DEVICE  [(info)] [-v | -vv | -vvv ]

Connect to a Genius Hub and interact with it, a Zone, or a Device:
       ghclient.py <HUB ID> [COMMAND] [ENTITY] [PARAMETERS]

Arguments:
  HUB-ID  either a Hub token, or a Hub hostname/address (which needs user credentials)
    If a token is provided, then v1 API calls are made, otherwise its v3 API calls

  COMMAND  the method or property to use:
    zones     display all zones attached to the hub, as a list of dicts
    devices   display all devices attached to the hub/zone, as a list of dicts
    issues    display all issues of the hub/zone/device, as a list of dicts
    info      display the properties of the hub/zone/device, as a dict
    reboot    reboot the hub

    If no COMMAND is provided, info is used and the entity's properties will be displayed.

Options:
  If a USERNAME is provided, the HUB-ID must be hostname/IP address:
    -u USERNAME --user=USERNAME    the username
    -p PASSWORD --pass=PASSWORD    the password

  Operations on a Zone:
    -z ZONE --zone=ZONE            the identifer of a Zone (id or name)
    -m MODE --mode=MODE            set mode to: off, timer, footprint, override
    -s SECS --secs=SECS            set the override duration, in seconds
    -t TEMP --temp=TEMP            set the override temperature, in Celsius

  Operations on a Device:
    -d DEVICE --device=DEVICE      the identifer of a Device (a string)

  Level of detail displayed:
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
import re

import aiohttp
from docopt import docopt

from geniushubclient import GeniusHubClient, GeniusHub, GeniusTestHub

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

    args = docopt(__doc__)
    # print(args)

    session = aiohttp.ClientSession()

    client = GeniusHubClient(hub_id=args[HUB_ID],
                             username=args[USERNAME],
                             password=args[PASSWORD],
                             session=session,
                             debug=False)

    client.verbosity = args[VERBOSE]

    hub = client.hub  # client.hub = GeniusHub(client, {'id': hub_id})
    await hub.update()  # initialise: enumerate all zones, devices & issues

    if args[DEVICE_ID]:
        key = args[DEVICE_ID]  # a device_id is always a str, never an int

        try:  # does a Device with this ID exist?
            device = hub.device_by_id[key]
        except KeyError:
            raise KeyError("Device '%s' does not exist.", args[ZONE_ID])

        print(json.dumps(device.info))

    elif args[ZONE_ID]:
        try:  # is the zone_id is a str, or an int?
            key = int(args[ZONE_ID])
        except ValueError:
            key = args[ZONE_ID]
            find_zone_by_key = hub.zone_by_name
        else:
            find_zone_by_key = hub.zone_by_id

        try:  # does a Zone with this ID exist?
            zone = find_zone_by_key[key]
        except KeyError:
            raise KeyError("Zone '%s' does not exist.", args[ZONE_ID])

        if args[MODE]:
            await zone.set_mode(args[MODE])
        elif args[TEMP]:
            await zone.set_override(args[TEMP], args[SECS])
        elif args[DEVICES]:
            print(json.dumps(zone.devices))
        elif args[ISSUES]:
            print(json.dumps(zone.issues))
        else:  # as per args[INFO]
            print(json.dumps(zone.info))

    else:  # as per: args[HUB_ID]
        if args[REBOOT]:
            raise NotImplementedError()  # await hub.reboot()
        elif args[ZONES]:
            print(json.dumps(hub.zones))
        elif args[DEVICES]:
            print(json.dumps(hub.devices))
        elif args[ISSUES]:
            print(json.dumps(hub.issues))
        else:  # as per args[INFO]
            print(json.dumps(hub.info))

    await session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
