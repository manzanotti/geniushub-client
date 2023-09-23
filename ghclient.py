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

    If a token is provided, then v1 API calls are made, otherwise its v3 API calls.

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
    Set the override temperature for Zone 12 to 19.5C for 1 hour.

"""  # noqa

# import ast
import argparse
import asyncio
import json
import logging

import aiohttp

from geniushubclient import GeniusHub, GeniusTestHub

DEBUG_ADDR = "172.27.0.138"
DEBUG_PORT = 5678

logging.basicConfig(datefmt="%H:%M:%S", format="%(asctime)s %(levelname)s: %(message)s")
_LOGGER = logging.getLogger(__name__)

# Debugging flags - all False for production releases
FILE_MODE = False  # use test files instead of a real Hub
DEBUG_NO_SCHEDULES = False  # don't print schedule data


def _parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("hub_id", help="either a Hub token, or a Hub hostname/address")

    group = parser.add_argument_group("user credentials (iff using v3 API)")
    group.add_argument("-u", "--username", type=str)
    group.add_argument("-p", "--password", type=str)

    group = parser.add_argument_group("various options")
    group.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="increasing verbosity, -vvv gives raw JSON",
    )
    group.add_argument(
        "-x",
        "--debug_mode",
        action="count",
        default=0,
        help="0=none, 1=enable_attach, 2=wait_for_attach",
    )

    args = parser.parse_known_args()

    if bool(args[0].username) ^ bool(args[0].password):
        parser.error("--username and --password must be given together, or not at all")
        return None

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", nargs="?")

    group = parser.add_mutually_exclusive_group()
    parser.add_argument("-z", "--zone_id", help="a Zone (id or name)")
    parser.add_argument("-d", "--device_id", help="a Device (a string)")

    group = parser.add_argument_group("used with a zone")
    group.add_argument("-m", "--mode", help="set to: off, timer, footprint, override")
    group.add_argument("-s", "--secs", help="set override duration, in seconds")
    group.add_argument("-t", "--temp", help="set override temperature, in Celsius")

    try:
        args_cmd = parser.parse_args(args[1])
    except IndexError:
        print(f"Invalid parameters, namespace is: {args[1]}")
        return

    if args_cmd.command not in [None, "zones", "devices", "issues", "info", "reboot"]:
        print(f"Unknown command, namespace is: {args_cmd}")
        return None

    if args_cmd.zone_id and args_cmd.command not in [None, "devices", "issues", "info"]:
        print(f"Invalid arguments, namespace is: {args_cmd}")
        return None

    if any([args_cmd.mode, args_cmd.secs, args_cmd.temp]) and not args_cmd.zone_id:
        print(f"Invalid arguments, namespace is: {args_cmd}")
        return None

    if args_cmd.device_id and args_cmd.command not in [None, "issues", "info"]:
        print(f"Invalid arguments, namespace is: {args_cmd}")
        return None

    return argparse.Namespace(**vars(args[0]), **vars(args_cmd))


async def main(loop):
    """Return the JSON as requested."""

    # Option of providing test data (as list of Dicts), or leave both as None
    if FILE_MODE:
        with open("raw_zones.json", mode="r") as fh:
            z = json.loads(fh.read())  # file from: ghclient zones -vvv
            # z = ast.literal_eval(fh.read())  # file from HA logs
        with open("raw_devices.json", mode="r") as fh:
            d = json.loads(fh.read())  # file from: ghclient zones -vvv
            # d = ast.literal_eval(fh.read())  # file from HA logs

        session = None
        hub = GeniusTestHub(zones_json=z, device_json=d, debug=True)
    else:
        args = _parse_args()
        # print(args)
        if args is None:
            return

        if args.debug_mode > 0:
            import ptvsd

            print(f"Debugging is enabled, listening on: {DEBUG_ADDR}:{DEBUG_PORT}.")
            ptvsd.enable_attach(address=(DEBUG_ADDR, DEBUG_PORT))

        if args.debug_mode > 1:
            print("Waiting for debugger to attach...")
            ptvsd.wait_for_attach()
            print("Debugger is attached!")

        if args.debug_mode > 2:
            breakpoint()

        session = aiohttp.ClientSession()
        hub = GeniusHub(
            hub_id=args.hub_id,
            username=args.username,
            password=args.password,
            session=session,
            debug=args.debug_mode,
        )

        hub.verbosity = args.verbosity

    await hub.update()  # initialise: enumerate all zones, devices & issues
    # ait hub.update()  # for testing, do twice in a row to check for no duplicates

    # these can be used for debugging, above - save as files, above
    # z = await hub._zones  # raw_zones.json
    # d = await hub._devices  # raw_devices.json

    if args.device_id:
        try:  # does a Device with this ID exist?
            device = hub.device_by_id[args.device_id]  # device_id is a str, not an int
        except KeyError:
            raise KeyError(f"Device '{args.device_id}' does not exist (by addr).")

        print(device.data)  # v0 = device, v1 = device.data, v3 = device._raw

    elif args.zone_id:
        try:  # was the zone_id given as a str, or an int?
            zone_id = int(args.zone_id)
        except ValueError:
            zone_id = args.zone_id
            find_zone_by_key = hub.zone_by_name
        else:
            find_zone_by_key = hub.zone_by_id

        try:  # does a Zone with this ID exist?
            zone = find_zone_by_key[zone_id]
        except KeyError:
            raise KeyError(f"Zone '{args.zone_id}' does not exist (by name or ID).")

        if args.mode:
            await zone.set_mode(args.mode)
        elif args.temp:
            await zone.set_override(args.temp, args.secs)
        elif args.command == "devices":
            print(json.dumps(zone.devices))
        elif args.command == "issues":
            print(json.dumps(zone.issues))
        else:  # args.command == "info"
            if DEBUG_NO_SCHEDULES:
                _info = {k: v for k, v in zone.data.items() if k != "schedule"}
                print(json.dumps(_info))
            else:
                print(json.dumps(zone.data))

    else:  # as per: args.hub_id
        if args.command == "reboot":
            raise NotImplementedError()  # await hub.reboot()
        elif args.command == "zones":
            if DEBUG_NO_SCHEDULES:
                _zones = [
                    {k: v for k, v in z.items() if k != "schedule"} for z in hub.zones
                ]
                print(json.dumps(_zones))
            else:
                print(json.dumps(hub.zones))
        elif args.command == "devices":
            print(json.dumps(hub.devices))
        elif args.command == "issues":
            print(json.dumps(hub.issues))
        else:  # args.command == "info"
            print(f"VER = {json.dumps(hub.version)}")
            print(f"UID = {hub.uid}")
            if hub.api_version == 3:
                print(f"XXX =", {"weatherData": hub.zone_by_id[0]._raw["weatherData"]})

    if session:
        await session.close()


if __name__ == "__main__":  # called from CLI?
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(main(LOOP))
    LOOP.close()
