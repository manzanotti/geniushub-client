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

    # args = vars(parser.parse_args())
    args = parser.parse_args()

    # hub.verbose = args.verbose
    # hub.timeout = args.timeout

    if args.zone:
        if args.username or args.password:
            zone = GeniusZone(hub_id=args.hub_id,
                              username=args.username,
                              password=args.password,
                              id=args.zone)
        else:
            zone = GeniusZone(hub_id=args.hub_id, id=args.zone)

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
            print("Unknown command")

    elif args.device:
        if args.username or args.password:
            device = GeniusDevice(hub_id=args.hub_id,
                                  username=args.username,
                                  password=args.password,
                                  id=args.device)
        else:
            device = GeniusDevice(hub_id=args.hub_id, id=args.device)

        device.verbose = 0 if args.verbose is None else args.verbose

        if args.command == "detail":
            print(await device.detail)
        else:
            print("Unknown command")

    else:
        hub = GeniusHub(hub_id=args.hub_id, username=args.username,
                        password=args.password, eventloop=loop)

        hub.verbose = 0 if args.verbose is None else args.verbose

        if args.command == "detail":
            print(await hub.detail)
        elif args.command == "version":
            print(await hub.version)
        elif args.command == "issues":
            print(await hub.issues)
        elif args.command == "zones":
            print(await hub.zones)
        elif args.command == "devices":
            print(await hub.devices)
        else:
            print(await hub.detail)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
