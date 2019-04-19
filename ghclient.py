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

    If no COMMAND is provided,  info is used and the entity's properties will be displayed.

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

ATTRS_ZONE = {
    'summary_keys': ['id', 'name'],
    'detail_keys': ['type', 'mode', 'temperature', 'setpoint', 'occupied', 'override', 'schedule']  # also: 'schedule'
}
ATTRS_DEVICE = {
    'summary_keys': ['id', 'type'],
    'detail_keys': ['assignedZones', 'state']
}
ATTRS_ISSUE = {
    'summary_keys': ['description', 'level'],
    'detail_keys': []
}

async def main(loop):
    """Return the JSON as requested."""
    def subset_dict(item_dict, item_dict_raw, summary_keys=[], detail_keys=[]):
        if args[VERBOSE] >= 3:
            return item_dict_raw
        elif args[VERBOSE] >= 2:
            return json.dumps(item_dict)
        elif args[VERBOSE] >= 1:
            keys = summary_keys + detail_keys
        else:
            keys = summary_keys

        return json.dumps({k: item[k] for k in keys if k in item})

    def subset_list(item_list, item_list_raw, summary_keys=[], detail_keys=[]):
        if args[VERBOSE] >= 3:
            return item_list_raw
        elif args[VERBOSE] >= 2:
            result = item_list
            if 'id' in result:
                result = sorted(result, key=lambda k: k['id'])
            return json.dumps(result)
        elif args[VERBOSE] >= 1:
            keys = summary_keys + detail_keys
        else:
            keys = summary_keys

        result = [{k: item[k] for k in keys if k in item}
            for item in item_list]
        if 'id' in result:
            result = sorted(result, key=lambda k: k['id'])

        return json.dumps(result)

    args = docopt(__doc__)
    # print(args)

    session = aiohttp.ClientSession()

    client = GeniusHubClient(hub_id=args[HUB_ID],
                             username=args[USERNAME],
                             password=args[PASSWORD],
                             session=session)

    hub = client.hub
    await hub.update()  # enumerate all zones, devices and issues

    if args[DEVICE_ID]:
        key = args[DEVICE_ID]  # a device_id is always a str, never an int

        try:  # does a Device with this ID exist?
            device = hub.device_by_id[key]
        except KeyError:
            raise KeyError("Device '%s' does not exist.", args[ZONE_ID])

        else:  # as per args[INFO]
            kwargs = ATTRS_DEVICE
            print(subset_dict(device.info, device._info_raw, **kwargs))

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
            # await zone.set_mode(args[MODE])
            raise NotImplementedError()

        elif args[TEMP]:
            # await zone.set_override(args[TEMP], args[SECS])
            raise NotImplementedError()

        elif args[DEVICES]:
            kwargs = ATTRS_DEVICE
            print(subset_list(zone.devices, zone._devices_raw, **kwargs))

        elif args[ISSUES]:
            kwargs = ATTRS_ISSUE
            print(subset_list(zone.issues, zone._issues_raw, **kwargs))

        else:  # as per args[INFO]
            kwargs = ATTRS_ZONE
            print(subset_dict(zone.info, zone._info_raw, **kwargs))

    else:  # as per: args[HUB_ID]
        if args[REBOOT]:
            # await hub.reboot()
            raise NotImplementedError()

        elif args[ZONES]:
            kwargs = ATTRS_ZONE
            print(subset_list(hub.zones, hub._zones_raw, **kwargs))

        elif args[DEVICES]:
            kwargs = ATTRS_DEVICE
            print(subset_list(hub.devices, hub._devices_raw, **kwargs))

        elif args[ISSUES]:
            kwargs = ATTRS_ISSUE
            print(subset_list(hub.issues, hub._issues_raw, **kwargs))

        else:  # as per args[INFO]
            raise NotImplementedError()

    await session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
