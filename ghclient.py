"""Python client library for Genius Hub public API."""

import asyncio
import logging

import aiohttp

from geniushubclient import GeniusHubClient, GeniusHub

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
    #parser.add_argument(
    #    "--timeout", "-x", action='store', type=int, default=30,
    #    help="set the timeout in secs (default = 30 sec)"
    #)
    parser.add_argument(
        "--verbose", "-v", action='count', required=False,
        help="-v add some detail, -vv raw data"
    )

    args = parser.parse_args()

    session = aiohttp.ClientSession()

    client = GeniusHubClient(hub_id=args.hub_id,
                             username=args.username, password=args.password,
                             session=session)
    client.verbose = False if args.verbose is None else args.verbose > 3
    # client.timeout = args.timeout
    # client.interval = args.interval

#   await client.populate()
#   hub = client.hub

    hub = GeniusHub(client, hub_id=args.hub_id[:20])

    # print(len(hub.zone_objs))
    # print(dir(hub.zone_objs[1]))
    # print(hub.zone_objs[1].name)
    # print(hub.zone_by_id[1].name)

    # for z in hub.zone_objs:
    #     print(z.id, z.name)
    # for d in hub.device_objs:
    #     print(d.id, d.type)
    # return

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
            print(await hub.issues)

        elif args.command == "zones":
            """Verbosity:
              v0 = id, name (/zones/summary)
              v1 = v0 + type, mode, temperature, setpoint, occupied, override
              v2 = v1 + schedule (/zones)
              v3 = v2 + ???
              v4 = raw JSON
            """

            # which keys to keep?
            keys = ['id', 'name']
            if args.verbose:
                if args.verbose > 3:
                    print(await hub.zones)
                    await session.close()
                    return
                if args.verbose > 0:
                    keys += ['type', 'temperature', 'setpoint', 'mode',
                            'occupied', 'override']
                if args.verbose > 1:
                    keys += ['schedule']

            # keep only the wanted keys
            zones = []
            for zone in await hub.zones:
                zones.append({k: zone[k] for k in keys if k in zone})
            print(zones)

            # print(len(hub.zone_objs))
            # print(hub.zone_objs[1].name)
            # print(hub.zone_by_id[1].name)

        elif args.command == "devices":
            """Verbosity:
              v0 = id, type (/devices/summary)
              v1 = v0 + ???
              v2 = v1 + "assignedZones", state (/devices)
              v3 = v2 + ???
              v4 = raw JSON
            """

            # which keys to keep?
            keys = ['id', 'type']
            if args.verbose:
                if args.verbose > 3:
                    print(await hub.devices)
                    await session.close()
                    return
                if args.verbose > 0:
                    keys += ['assignedZones']
                if args.verbose > 1:  # v2 - as /devices
                    keys += ['state']

            # keep only the wanted keys
            devices = []
            for device in await hub.devices:
                devices.append({k: device[k] for k in keys if k in device})
            print(devices)

        else:
            print("Error: unknown command: {}".format(args.command))

    await session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
