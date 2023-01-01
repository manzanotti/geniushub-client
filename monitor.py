import asyncio
import json
import sqlite3

import aiohttp

from config import geniushub
from geniushubclient import GeniusHub

username = geniushub["USERNAME"]
password = geniushub["PASSWORD"]
hub_id = geniushub["HUB_ADDRESS"]
token = geniushub["HUB_TOKEN"]

local = True

debug = False

zone_map = dict()


async def run():

    global zone_map
    my_session = aiohttp.ClientSession()
    if local:
        hub = GeniusHub(
            hub_id=hub_id, username=username, password=password, session=my_session
        )
    else:
        hub = GeniusHub(hub_id=token, session=my_session)

    try:
        await hub.update()  # enumerate all zones, devices and issues
    except BaseException as e:
        print(f"Problem updating hub info: {e}")
        return

    hub.verbosity = 0  # same as v1/zones/summary, v1/devices/summary

    hub.verbosity = 1  # default, same as v1/zones, v1/devices, v1/issues
    hub_zones = hub.zones
    hub_devices = hub.devices
    if debug:
        print(json.dumps({"zones": hub_zones}, indent=4, sort_keys=True))
        print(json.dumps({"devices": hub_devices}, indent=4, sort_keys=True))

    await my_session.close()

    for zone in hub_zones:
        if "name" in zone:
            zone_map["z" + str(zone["id"])] = zone["name"]
        add_zone_output(zone)
    for device in hub_devices:
        name = device["assignedZones"][0]["name"] or device["type"]
        if name is not None:
            zone_map[device["id"]] = name
        else:
            print(f"Null device name: {device}")
        if "setTemperature" in device["state"]:
            add_temp(
                hub,
                device["id"],
                "setTemperature",
                f"{device['assignedZones'][0]['name']} set temperature",
            )
        if "measuredTemperature" in device["state"]:
            if device["type"] == "Powered Room Thermostat - Channel 2":
                add_temp(
                    hub,
                    device["id"],
                    "measuredTemperature",
                    f"{zone_map[device['id'].split('-')[0]]} air temperature",
                )
            elif device["type"] == "Powered Room Thermostat - Channel 3":
                pass
            elif device["type"] == "Powered Room Thermostat - Channel 4":
                add_temp(
                    hub,
                    device["id"],
                    "measuredTemperature",
                    f"{zone_map[device['id'].split('-')[0]]} floor temperature",
                )
            elif device["type"] == "Genius Valve":
                add_temp(
                    hub,
                    device["id"],
                    "measuredTemperature",
                    f"{zone_map[device['id']]} valve temperature",
                )
            else:
                print(json.dumps(device, indent=4, sort_keys=True))
        if "outputOnOff" in device["state"]:
            write_output(device["id"], device["state"]["outputOnOff"])


def write_output(name, output):
    output = float(output)
    lookup = zone_map.get(name)
    print(name + (f" ({lookup})" if lookup is not None else "") + f": status={output}")

    db = sqlite3.connect("genius.db")
    qry = "insert into temp (device_id, temperature, timestamp) values (?,?,CURRENT_TIMESTAMP);"
    try:
        cur = db.cursor()
        cur.execute(qry, (name, output))
        db.commit()
    except BaseException as e:
        print(f"error in database insert: {qry}")
        print(str(e))
        db.rollback()
    db.close()


def add_zone_output(zone):
    try:
        output = zone["output"]
        write_output("z" + str(zone["id"]), output)
    except KeyError:
        print(f'{zone.get("name", zone["id"])} output status not available')


def add_output(hub, room):
    try:
        output = hub.zone_by_name[room].info["output"]
        print(f"{room}: status={output}")
        write_output(room, output)
    except KeyError:
        print(f"{room} output y status not available")


def add_temp(hub, device, field, description):
    try:
        temperature = hub.device_by_id[device].data["state"][field]
        print(f"{description}: {temperature}")
        db = sqlite3.connect("genius.db")
        qry = "insert into temp (device_id, temperature, timestamp) values (?,?,CURRENT_TIMESTAMP);"
        try:
            cur = db.cursor()
            cur.execute(qry, (device, temperature))
            db.commit()
        except BaseException:
            print(f"error in database insert: {qry}")
            db.rollback()
        db.close()
    except KeyError:
        print(f"{description} not available")


def setup():
    db = sqlite3.connect("genius.db")
    cur = db.cursor()
    cur.execute(
        """
    CREATE TABLE temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT (7) NOT NULL,
    temperature REAL,
    timestamp TEXT (25) NOT NULL
    );
    """
    )
    db.close()


if __name__ == "__main__":
    # db = sqlite3.connect('genius.db')
    import sys
    import time

    if "-d" in sys.argv or "--debug" in sys.argv:
        debug = True
    while True:
        asyncio.run(run())
        time.sleep(300)
