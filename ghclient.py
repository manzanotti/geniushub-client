"""Python client library for Genius Hub public API."""

import asyncio
import logging

from geniushubclient2 import GeniusHub, GeniusZone, GeniusDevice
# import geniushubclient

_LOGGER = logging.getLogger(__name__)


async def main(loop):
    """Return the JSON as requested."""
    _LOGGER.debug("main()")

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "hub_id",
        help="the hostname/address or hub_token of the Hub"
    )
    parser.add_argument(
        "command",
        help="the command (version, detail, zones, devices)"
        )

    parser.add_argument(
        "--username", "-u", action='store', type=str,
        help="set the timeout in secs (default = 30 sec)"
    )
    parser.add_argument(
        "--password", "-p", action='store', type=str,
        help="set the timeout in secs (default = 30 sec)"
    )
    entity_group = parser.add_mutually_exclusive_group(required=False)

    # hub_group = entity_group.add_mutually_exclusive_group()
    # zone_group = entity_group.add_mutually_exclusive_group()
    # device_group = entity_group.add_mutually_exclusive_group()

    entity_group.add_argument(
        "--zone", "-z", action='store', type=int, default=0,
        help="the identifier of the zone"
    )
    # zone_group.add_argument(
    #     "--mode", "-m", action='store', type=int, default=0,
    #     help="the mode"
    # )
    # zone_group.add_argument(
    #     "--temp", "-t", action='store', type=int, default=0,
    #     help="the temperature of the override"
    # )
    # zone_group.add_argument(
    #     "--seconds", "-s", action='store', type=int, default=0,
    #     help="the duration of the override"
    # )
    entity_group.add_argument(
        "--device", "-d", action='store', type=int, default=0,
        help="the identifier of the device"
    )
    parser.add_argument(
        "--timeout", "-x", action='store', type=int, default=30,
        help="set the timeout in secs (default = 30 sec)"
    )
    parser.add_argument(
        "--verbose", "-v", action='count', required=False,
        help="-v add some detail, use -vv for more detail, -vvv raw data"
    )

    args = parser.parse_args()

    hub = GeniusHub(hub_id=args.hub_id,
                    username=args.username, password=args.password,
                    eventloop=loop, session=None)
    hub.verbose = 0 if args.verbose is None else args.verbose
    # hub.timeout = args.timeout
    # hub.interval = args.interval

    if args.zone:
        print("Sorry: not implemented yet.")
        return False

        zone = hub.zone(id=args.zone)
        zone.verbose = args.verbose if args.verbose else 0

        if args.command == "detail":
            print(await zone.detail)
        elif args.command == "devices":
           print(await zone.devices)
        elif args.command == "mode":
            print(await zone.mode)
        elif args.command == "override":
            print(await zone.override)
        else:
            print("Error: unknown command: {}".format(args.command))

    elif args.device:
        print("Sorry: not implemented yet.")
        return False

        device = hub.device(id=args.device)
        device.verbose = 0 if args.verbose is None else args.verbose

        if args.command == "detail":
            print(await device.detail)
        else:
            print("Error: unknown command: {}".format(args.command))

    else:
        if not args.command or args.command == "detail":
            print("Sorry: not implemented yet.")
            return False
            print(await hub.detail)

        elif args.command == "version":
            print("Sorry: not implemented yet.")
            return False
            print(await hub.version)

        elif args.command == "issues":
            print("Sorry: not implemented yet.")
            return False
            print(await hub.issues)

        elif args.command == "zones":
            keys = ['id', 'type', 'name']
            if args.verbose:
                keys += ['temperature', 'setpoint', 'mode', 'occupied', 'override']
                if args.verbose > 1:
                    keys += ['schedule']

            if not args.username:
                zones = []
                for zone in await hub.zones:
                    zones.append({k: zone[k] for k in keys if k in zone})
                print(zones)
            else:
                print(await hub.zones)

        elif args.command == "devices":
            keys = ['id', 'name', 'type', 'mode']
            if args.verbose:
                keys += ['assignedZones']
                if args.verbose > 1:
                    keys += ['state']

            if not args.username:
                devices = []
                for device in await hub.devices:
                    devices.append({k: device[k] for k in keys if k in device})
                print(devices)
            else:
                print(await hub.devices)

        else:
            print("Error: unknown command: {}".format(args.command))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
