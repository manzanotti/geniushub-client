"""Python client library for the Genius Hub API."""
from types import SimpleNamespace

DEFAULT_TIMEOUT_V1 = 30
DEFAULT_TIMEOUT_V3 = 10

DEFAULT_INTERVAL_V1 = 300
DEFAULT_INTERVAL_V3 = 30

API_STATUS_ERROR = {
    400: "The request body or request parameters are invalid.",
    401: "The authorization information is missing or invalid.",
    404: "No zone/device with the specified ID was found "
         "(or the state property does not exist on the specified device).",
    502: "The hub is offline.",
    503: "The authorization information is invalid.",
}
ZONE_TYPES = SimpleNamespace(
    Manager=1,
    OnOffTimer=2,
    ControlSP=3,
    ControlOnOffPID=4,
    TPI=5,
    Surrogate=6
)
# 1 "Manager"
# 2 "On / Off"
# 3 "Radiator"
# 4
# 5 "Hot Water Temperature" OR "Wet Underfloor"
# 6 "Group"

ZONE_MODES = SimpleNamespace(
    Off=1,
    Timer=2,
    Footprint=4,
    Away=8,
    Boost=16,
    Override=16,
    Early=32,
    Test=64,
    Linked=128,
    Other=256
)
KIT_TYPES = SimpleNamespace(
    Temp=1,
    Valve=2,
    PIR=4,
    Power=8,
    Switch=16,
    Dimmer=32,
    Alarm=64,
    GlobalTemp=128,
    Humidity=256,
    Luminance=512
)
KIT_SKU_TO_TEXT = {
    "DA-WRT-C": "Room Thermostat",
    "DA-WRV-B": "Radiator Valve",
    "DA-WRV-C": "Genius Valve",
    "HO-ESW-D": "Electric Switch",
    "PH-PLG-C": "Smart Plug",
    "PH-WRS-B": "Room Sensor",
}
ZONE_FLAGS = SimpleNamespace(
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
    TPI=2048
)
ITYPE_TO_TYPE = {
    ZONE_TYPES.Manager: 'manager',
    ZONE_TYPES.OnOffTimer: 'on / off',
    ZONE_TYPES.ControlSP: 'radiator',
    ZONE_TYPES.ControlOnOffPID: 'type 4',
    ZONE_TYPES.TPI: 'hot water temperature',
    ZONE_TYPES.Surrogate: 'type 6',
}  # also: 'group', 'wet underfloor'
TYPE_TO_ITYPE = {v: k for k, v in ITYPE_TO_TYPE.items()}

IMODE_TO_MODE = {
    ZONE_MODES.Off: 'off',
    ZONE_MODES.Timer: 'timer',
    ZONE_MODES.Footprint: 'footprint',
    ZONE_MODES.Away: 'away',
    ZONE_MODES.Boost: 'override',
    ZONE_MODES.Early: 'early',
    ZONE_MODES.Test: 'test',
    ZONE_MODES.Linked: 'linked',
    ZONE_MODES.Other: 'other'
}
MODE_TO_IMODE = {v: k for k, v in IMODE_TO_MODE.items()}

LEVEL_TO_TEXT = {
    2: 'error',
    1: 'warning',
    0: 'information'
}
DESCRIPTION_TO_TEXT = {
    "manager:no_boiler_controller":
        "The hub does not have a boiler controller assigned",
    "manager:no_boiler_comms":
        "The hub has lost communication with the boiler controller",
    "manager:no_temp":
        "The hub does not have a valid temperature",
    "manager:weather":                                                           # checked/confirmed
        "Unable to fetch the weather data",
    "manager:weather_data":
        "Weather data -",

    "zone:using_weather_temp":
        "{} is currently using the outside temperature",
    "zone:using_assumed_temp":
        "{} is currently using the assumed temperature",
    "zone:tpi_no_temp":
        "{} has no valid temperature sensor",

    "node:no_comms":
        "The device has lost communication with the Hub",
    "node:not_seen":                                                             # checked/confirmed
        "The {device} in {zone} can not been found by the Hub",
    "node:low_battery":
        "The battery is dead and needs to be replaced",
    "node:warn_battery":
        "the battery is low",
}

### Examples:
# [{'iID': 0, 'strName': '32 Clift road', 'lstIssues': [{
#     'id': 'manager:weather', 'level': 1, 'zone_name': '32 Clift road',
#         'data': {'msg': ''} }] }]

# {'iID': 10, 'strName': 'Bathrooms', 'lstIssues': [{
#     'id': 'node:not_seen', 'level': 2, 'zone_name': 'Bathrooms',
#         'data': {'location': 'Bathrooms', 'nodeID': '19', 'nodeHash': ...} }] }]
