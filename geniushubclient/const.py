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

zone_types = SimpleNamespace(
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

zone_modes = SimpleNamespace(
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
kit_types = SimpleNamespace(
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
zone_flags = SimpleNamespace(
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
    zone_types.Manager: 'manager',
    zone_types.OnOffTimer: 'on / off',
    zone_types.ControlSP: 'radiator',
    zone_types.ControlOnOffPID: 'type 4',
    zone_types.TPI: 'hot water temperature',
    zone_types.Surrogate: 'type 6',
}  # also: 'group', 'wet underfloor'
IMODE_TO_MODE = {
    zone_modes.Off: 'off',
    zone_modes.Timer: 'timer',
    zone_modes.Footprint: 'footprint',
    zone_modes.Away: 'away',
    zone_modes.Boost: 'override',
    zone_modes.Early: 'early',
    zone_modes.Test: 'test',
    zone_modes.Linked: 'linked',
    zone_modes.Other: 'other'
}
LEVEL_TO_TEXT = {
    0: 'error',
    1: 'warning',
    2: 'information'
}
DESCRIPTION_TO_TEXT = {
    "node:no_comms":
        "The device has lost communication with the Hub",
    "node:not_seen":
        "The device has not been found by the Hub",
    "node:low_battery":
        "The battery is dead and needs to be replaced",
    "node:warn_battery":
        "the battery is low",
    "manager:no_boiler_controller":
        "The hub does not have a boiler controller assigned",
    "manager:no_boiler_comms":
        "The hub has lost communication with the boiler controller",
    "manager:no_temp":
        "The hub does not have a valid temperature",
    "manager:weather_data":
        "Weather data -",
    "zone:using_weather_temp":
        "The {} zone is currently using the outside temperature",
    "zone:using_assumed_temp":
        "The {} zone is currently using the assumed temperature",
    "zone:tpi_no_temp":
        "The {} zone has no valid temperature sensor",
}
