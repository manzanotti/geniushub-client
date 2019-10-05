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
import ast
import json
import logging

import aiohttp
from docopt import docopt

from geniushubclient import GeniusHub, GeniusTestHub

logging.basicConfig(datefmt="%H:%M:%S", format="%(asctime)s %(levelname)s: %(message)s")
_LOGGER = logging.getLogger(__name__)

FILE_MODE = False  # use test files, or not

HUB_ID = "HUB-ID"
ZONE_ID = "--zone"
DEVICE_ID = "--device"
USERNAME = "--user"
PASSWORD = "--pass"
MODE = "--mode"
SECS = "--secs"
TEMP = "--temp"

DEVICES = "devices"
ISSUES = "issues"
REBOOT = "reboot"
ZONES = "zones"

VERBOSE = "-v"


async def main(loop):
    """Return the JSON as requested."""

    args = docopt(__doc__)
    # print(args)

    session = aiohttp.ClientSession()  # test with/without

    # Option of providing test data (as list of Dicts), or leave both as None
    if FILE_MODE:
        with open("raw_zones.json", "r") as fh:
            z = ast.literal_eval(fh.read())
        with open("raw_devices.json", "r") as fh:
            d = ast.literal_eval(fh.read())

        hub = GeniusTestHub(zones_json=z, device_json=d, session=session, debug=True)
    else:
        hub = GeniusHub(
            hub_id=args[HUB_ID],
            username=args[USERNAME],
            password=args[PASSWORD],
            session=session,
            debug=False,
        )

    hub.verbosity = args[VERBOSE]

    await hub.update()  # initialise: enumerate all zones, devices & issues
    # ait hub.update()  # for testing, do twice in a row to check for no duplicates

    # these can be used for debugging, above - save as files, above
    # z = await hub._zones  # raw_zones.json
    # d = await hub._devices  # raw_devices.json

    if args[DEVICE_ID]:
        key = args[DEVICE_ID]  # a device_id is always a str, never an int

        try:  # does a Device with this ID exist?
            device = hub.device_by_id[key]
        except KeyError:
            raise KeyError(f"Device '{args[DEVICE_ID]}' does not exist (by addr).")

        print(device.info)  # detail depends upon verbosity (v=0..3)
        # is: device (v=0), device.data (v=1), device._raw (v=3), and device.assigned_zone

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
            raise KeyError(f"Zone '{args[ZONE_ID]}' does not exist (by name or ID).")

        if args[MODE]:
            await zone.set_mode(args[MODE])
        elif args[TEMP]:
            await zone.set_override(args[TEMP], args[SECS])
        elif args[DEVICES]:
            print(json.dumps(zone.devices))
        elif args[ISSUES]:
            print(json.dumps(zone.issues))
        else:  # as per args[INFO]
            print(json.dumps({k: v for k, v in zone.info.items() if k != "schedule"}))
            # is: zone (v=0) zone.data (v=1) and zone._raw (v=3)

    else:  # as per: args[HUB_ID]
        if args[REBOOT]:
            raise NotImplementedError()  # await hub.reboot()
        elif args[ZONES]:
            print(json.dumps([{k: v for k, v in i.items() if k != "schedule"} for i in hub.zones]))
            # print(json.dumps(hub.zones))
        elif args[DEVICES]:
            print(json.dumps(hub.devices))
        elif args[ISSUES]:
            print(json.dumps(hub.issues))
        else:  # as per args[INFO]
            print(json.dumps(hub.version))
            print(hub.uid)
            if hub.api_version == 3:
                print({"weatherData": hub.zone_by_id[0]._raw["weatherData"]})

    if session:
        await session.close()


if __name__ == "__main__":  # called from CLI?
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(main(LOOP))
    LOOP.close()
