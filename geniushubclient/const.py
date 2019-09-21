"""Python client library for the Genius Hub API."""
from types import SimpleNamespace

DEFAULT_TIMEOUT_V1 = 120
DEFAULT_TIMEOUT_V3 = 20

# see: https://docs.geniushub.co.uk/pages/viewpage.action?pageId=14221432
HUB_SW_VERSIONS = {
    "Dec 31 9999": "5.3.2+",
    "Jul 23 2019": "5.3.2",  # #          confirmed in testing
    "Jun 25 2019": "5.3.0",
    "Dec 20 2018": "5.2.10 (beta)",
    "Dec 19 2018": "5.2.10",  # #         confirmed in testing
    "Jul 11 2018": "5.2.4",
    "Jan 05 2018": "5.2.2",
    "Jan 01 1000": "<5.2.2",
}

API_STATUS_ERROR = {
    400: "The request body or request parameters are invalid.",
    401: "The authorization information is missing or invalid.",
    404: "No zone/device with the specified ID was found "
    "(or the state property does not exist on the specified device).",
    502: "The hub is offline.",
    503: "The authorization information is invalid.",
}

FOOTPRINT_MODES = {1: "super-eco", 2: "eco", 3: "comfort"}

# the following is from the vendor's javascript

ZONE_TYPE = SimpleNamespace(
    Manager=1, OnOffTimer=2, ControlSP=3, ControlOnOffPID=4, TPI=5, Surrogate=6
)  # from app.js, search for '.Type = {'

ITYPE_TO_TYPE = {  # ZONE_TYPE_MODEL
    ZONE_TYPE.Manager: "manager",  # "my house"
    ZONE_TYPE.OnOffTimer: "on / off",  # "on / off timer"
    ZONE_TYPE.ControlSP: "radiator",  # "radiator room"
    ZONE_TYPE.ControlOnOffPID: "wet underfloor",  # "control on / off PID"
    ZONE_TYPE.TPI: "hot water temperature",  # "TPI"
    ZONE_TYPE.Surrogate: "group",  # "group"
}
TYPE_TO_ITYPE = {v: k for k, v in ITYPE_TO_TYPE.items()}

ZONE_MODE = SimpleNamespace(
    Off=1,
    Timer=2,
    Footprint=4,
    Away=8,
    Boost=16,
    Override=16,
    Early=32,
    Test=64,
    Linked=128,
    Other=256,
)  # from app.js, search for '.ZoneModes = {'

IMODE_TO_MODE = {  # MODE_MODEL
    ZONE_MODE.Off: "off",
    ZONE_MODE.Timer: "timer",  # could also be 'sense' mode
    ZONE_MODE.Footprint: "footprint",
    ZONE_MODE.Away: "off",  # v1 API says 'off', not 'away'
    ZONE_MODE.Boost: "override",
    ZONE_MODE.Early: "early",
    ZONE_MODE.Test: "test",
    ZONE_MODE.Linked: "linked",
    ZONE_MODE.Other: "other",
}
MODE_TO_IMODE = {v: k for k, v in IMODE_TO_MODE.items()}

ZONE_FLAG = SimpleNamespace(
    Frost=1,
    Timer=2,
    Footprint=4,
    Boost=8,
    Away=16,
    WarmupAuto=32,
    WarmupManual=64,
    Reactive=128,
    Linked=256,
    WeatherComp=512,
    Temps=1024,
    TPI=2048,
)  # from app.js, search for '.ZoneFlags = {'

ISSUE_TEXT = {0: "information", 1: "warning", 2: "error"}
ISSUE_DESCRIPTION = {
    "manager:no_boiler_controller": "The hub does not have a boiler controller assigned",
    "manager:no_boiler_comms": "The hub has lost communication with the boiler controller",
    "manager:no_temp": "The hub does not have a valid temperature",
    "manager:weather": "Unable to fetch the weather data",  # correct
    "manager:weather_data": "Weather data -",
    "zone:using_weather_temp": "{zone_name} is currently using the outside temperature",  # correct
    "zone:using_assumed_temp": "{zone_name} is currently using the assumed temperature",
    "zone:tpi_no_temp": "{zone_name} currently has no valid temperature",  # correct
    "node:no_comms": "The {device_type} has lost communication with the Hub",
    "node:not_seen": "The {device_type} in {zone_name} can not been found by the Hub",  # correct
    "node:low_battery": "The battery for the {device_type} in {zone_name} is dead and needs to be replaced",  # correct
    "node:warn_battery": "The battery for the {device_type} is low",
    "node:assignment_limit_exceeded": "{device_type} has been assigned to too many zones",  # for DCR channels
}  # from app.js, search for: "node:, "zone:, "manager:

# Example errors
# {'id': 'node:low_battery',        'level': 2, 'data': {'location': 'Room 2.2',
#        'nodeHash': '0x00000002A0107FFF', 'nodeID': '27', 'batteryLevel': 255}}
# {'id': 'node:not_seen',           'level': 2, 'data': {'location': 'Kitchen',
#         'nodeHash': '0x0000000000000000', 'nodeID':  '4'}}
# {'id': 'zone:tpi_no_temp',        'level': 2, 'data': {'location': 'Temp'}}
# {'id': 'zone:using_weather_temp', 'level': 1, 'data': {'location': 'Test Rad'}}

IDAY_TO_DAY = {
    0: "sunday",
    1: "monday",
    2: "tuesday",
    3: "wednesday",
    4: "thursday",
    5: "friday",
    6: "saturday",
}

ATTRS_ZONE = {
    "summary_keys": ["id", "name"],
    "detail_keys": [
        "type",
        "mode",
        "temperature",
        "setpoint",
        "occupied",
        "override",
        "schedule",
    ],
}
ATTRS_DEVICE = {
    "summary_keys": ["id", "type"],
    "detail_keys": ["assignedZones", "state"],
}
ATTRS_ISSUE = {"summary_keys": ["description", "level"], "detail_keys": []}

# The following MODELs are from Vendor's bower.js, search for: 'Model: [{'
DEVICES_MODEL = [
    {"hash": "VIRTUAL", "sku": "virtual node", "description": "Virtual Node"},
    {"hash": "0x0000000000000000", "sku": "n/a", "description": "Unrecognised Device"},
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Radiator Valve",
        "deviceString": "wrv",
        "hash": "0x0000000200030005",
        "sku": "da-wrv-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Radiator Valve",
        "deviceString": "wrv",
        "hash": "0x0000000200040005",
        "sku": "da-wrv-b",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Dual Underfloor Receiver",
        "deviceString": "dur",
        "hash": "0x0000000220008004",
        "sku": "da-dur-a",
    },
    {
        "assignableZoneTypeIds": [1, 3, 5],
        "description": "Room Thermostat",
        "deviceString": "wrt",
        "hash": "0x0000000280100003",
        "sku": "da-wrt-c",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Genius Valve",
        "deviceString": "wrv",
        "hash": "0x00000002A0107FFF",
        "sku": "da-wrv-c",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Single Channel Receiver",
        "deviceString": "scr",
        "hash": "0x0000005900010003",
        "sku": "ho-scr-c",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Electric Switch",
        "deviceString": "esw",
        "hash": "0x0000005900010010",
        "sku": "ho-esw-d",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Dual Channel Receiver",
        "deviceString": "dcr",
        "hash": "0x0000005900020003",
        "sku": "ho-dcr-c",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Temperature Sensor",
        "deviceString": "wts",
        "hash": "0x000000590002000D",
        "sku": "ho-wts-a",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Electric Switch",
        "deviceString": "esw",
        "hash": "0x0000005900020010",
        "sku": "ho-esw-d",
    },
    {
        "assignableZoneTypeIds": [1, 3, 5],
        "description": "Room Thermostat",
        "deviceString": "wrt",
        "hash": "0x0000005900030001",
        "sku": "ho-wrt-b",
    },
    {
        "assignableZoneTypeIds": [1, 3, 5],
        "description": "Room Thermostat",
        "deviceString": "wrt",
        "hash": "0x0000005900050001",
        "sku": "ho-wrt-d",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Single Channel Receiver",
        "deviceString": "scr",
        "hash": "0x0000005900050003",
        "sku": "ho-scr-d",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Dual Channel Receiver",
        "deviceString": "dcr",
        "hash": "0x0000005900060003",
        "sku": "ho-dcr-d",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Smart Plug",
        "deviceString": "plg",
        "hash": "0x0000006000010003",
        "sku": "ev-plg-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Temperature Humidity Sensor",
        "deviceString": "ths",
        "hash": "0x0000006000010006",
        "sku": "es-ths-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Motion Sensor",
        "deviceString": "wms",
        "hash": "0x0000006000020001",
        "sku": "es-wms-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Temperature Sensor",
        "deviceString": "wts",
        "hash": "0x00000071035D0002",
        "sku": "ls-wts-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "CO2 Sensor",
        "deviceString": "cos",
        "hash": "0x00000081000100A0",
        "sku": "sa-cos-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Room Sensor",
        "deviceString": "wrs",
        "hash": "0x0000008600050002",
        "sku": "al-wrs-c",
    },
    {
        "assignableZoneTypeIds": [1],
        "description": "Gas Meter Reader",
        "deviceString": "umr",
        "hash": "0x0000009600010010",
        "sku": "nq-umr-a",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Smart Plug",
        "deviceString": "plg",
        "hash": "0x0000013C00010001",
        "sku": "ph-plg-c",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Room Sensor",
        "deviceString": "wrs",
        "hash": "0x0000013C00020002",
        "sku": "ph-wrs-a",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Room Sensor",
        "deviceString": "wrs",
        "hash": "0x0000013C000C0002",
        "sku": "ph-wrs-b",
    },
    {
        "assignableZoneTypeIds": [3, 5],
        "description": "Room Sensor",
        "deviceString": "wrs",
        "hash": "0x0000013C000D0002",
        "sku": "ph-wrs-b",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Electric Switch",
        "deviceString": "esw",
        "hash": "0x0000013C000F0001",
        "sku": "ph-esw-b",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Electric Switch",
        "deviceString": "esw",
        "hash": "0x0000013C00100001",
        "sku": "ph-esw-a",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Smart Plug",
        "deviceString": "plg",
        "hash": "0x0000013C00110001",
        "sku": "ph-plg-c",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "In Wall Meter",
        "deviceString": "iwm",
        "hash": "0x0000013C001A0006",
        "sku": "ph-iwm-a",
    },
    {
        "assignableZoneTypeIds": [1, 2, 3, 5, 6],
        "description": "Smart Plug",
        "deviceString": "plg",
        "hash": "0x0000015400011100",
        "sku": "po-plg-b",
    },
]  # from bower.js, search for: 'Model: [{'

DEVICE_HASH_TO_TYPE = {d["hash"]: d["description"] for d in DEVICES_MODEL}

SKU_BY_HASH = {d["hash"]: d["sku"] for d in DEVICES_MODEL}

CHANNELS_MODEL = [
    {
        "id": "Switch Binary",
        "description": "Output On/Off",
        "slug": "outputOnOff",
        "type": "Boolean",
    },
    {
        "id": "SwitchBinary",
        "description": "Output On/Off",
        "slug": "outputOnOff",
        "type": "Boolean",
    },
    {
        "id": "Battery",
        "description": "Battery Level",
        "slug": "batteryLevel",
        "type": "Number",
    },
    {
        "id": "HEATING_1",
        "description": "Set Temperature",
        "slug": "setTemperature",
        "type": "Number",
    },
    {
        "id": "TEMPERATURE",
        "description": "Measured Temperature",
        "slug": "measuredTemperature",
        "type": "Number",
    },
    {
        "id": "LUMINANCE",
        "description": "Luminance",
        "slug": "luminance",
        "type": "Number",
    },
    {
        "id": "Motion",
        "description": "Occupancy Trigger",
        "slug": "occupancyTrigger",
        "type": "Number",
    },
]

STATE_ATTRS = {c["id"]: c["slug"] for c in CHANNELS_MODEL}

ZONE_KIT = SimpleNamespace(  # ZONE_KIT_MODEL
    Temp=1,
    Valve=2,
    PIR=4,
    Power=8,
    Switch=16,
    Dimmer=32,
    Alarm=64,
    GlobalTemp=128,
    Humidity=256,
    Luminance=512,
    GasMeter=1024,
    CO2=2014,
)  # from app.js, search for '.EquipmentTypes = {'
