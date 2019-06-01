'''Python client library for the Genius Hub API.'''
from types import SimpleNamespace

DEFAULT_TIMEOUT_V1 = 300
DEFAULT_TIMEOUT_V3 = 20

API_STATUS_ERROR = {
    400: 'The request body or request parameters are invalid.',
    401: 'The authorization information is missing or invalid.',
    404: 'No zone/device with the specified ID was found '
         '(or the state property does not exist on the specified device).',
    502: 'The hub is offline.',
    503: 'The authorization information is invalid.',
}
ZONE_TYPES = SimpleNamespace(
    Manager=1,
    OnOffTimer=2,
    ControlSP=3,
    ControlOnOffPID=4,
    TPI=5,
    Surrogate=6
)
# 1 'Manager'
# 2 'On / Off'
# 3 'Radiator'
# 4
# 5 'Hot Water Temperature' OR 'Wet Underfloor'
# 6 'Group'

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
    'DA-WRT-C': 'Room Thermostat',
    'DA-WRV-B': 'Radiator Valve',
    'DA-WRV-C': 'Genius Valve',
    'HO-ESW-D': 'Electric Switch',
    'PH-PLG-C': 'Smart Plug',
    'PH-WRS-B': 'Room Sensor',
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
    'manager:no_boiler_controller':
        'The hub does not have a boiler controller assigned',
    'manager:no_boiler_comms':
        'The hub has lost communication with the boiler controller',
    'manager:no_temp':
        'The hub does not have a valid temperature',
    'manager:weather':                                                           # checked/confirmed
        'Unable to fetch the weather data',
    'manager:weather_data':
        'Weather data -',

    'zone:using_weather_temp':
        '{zone_name} is currently using the outside temperature',
    'zone:using_assumed_temp':
        '{zone_name} is currently using the assumed temperature',
    'zone:tpi_no_temp':                                                          # checked/confirmed
        '{zone_name} currently has no valid temperature',

    'node:no_comms':
        'The {device_type} has lost communication with the Hub',
    'node:not_seen':                                                             # checked/confirmed
        'The {device_type} in {zone_name} can not been found by the Hub',
    'node:low_battery':                                                          # checked/confirmed
        'The battery for the {device_type} in {zone_name} is dead and needs to be replaced',
    'node:warn_battery':
        'The battery for the {device_type} is low',
}

IDAY_TO_DAY = {
    0: 'sunday',
    1: 'monday',
    2: 'tuesday',
    3: 'wednesday',
    4: 'thursday',
    5: 'friday',
    6: 'saturday',
}

ATTRS_ZONE = {
    'summary_keys': ['id', 'name'],
    'detail_keys': ['type', 'mode', 'temperature', 'setpoint', 'occupied',
                    'override', 'schedule']
}
ATTRS_DEVICE = {
    'summary_keys': ['id', 'type'],
    'detail_keys': ['assignedZones', 'state']
}
ATTRS_ISSUE = {
    'summary_keys': ['description', 'level'],
    'detail_keys': []
}

# This is from Vendor's bower.js
DEVICES_MODEL = [
    {
        'hash': 'VIRTUAL',
        'sku': 'virtual node',
        'description': 'Virtual Node'
    }, {
        'hash': '0x0000000000000000',
        'sku': 'n/a',
        'description': 'Unrecognised Device'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Radiator Valve',
        'deviceString': 'wrv',
        'hash': '0x0000000200030005',
        'sku': 'da-wrv-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Radiator Valve',
        'deviceString': 'wrv',
        'hash': '0x0000000200040005',
        'sku': 'da-wrv-b'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Dual Underfloor Receiver',
        'deviceString': 'dur',
        'hash': '0x0000000220008004',
        'sku': 'da-dur-a'
    }, {
        'assignableZoneTypeIds': [1, 3, 5],
        'description': 'Room Thermostat',
        'deviceString': 'wrt',
        'hash': '0x0000000280100003',
        'sku': 'da-wrt-c'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Genius Valve',
        'deviceString': 'wrv',
        'hash': '0x00000002A0107FFF',
        'sku': 'da-wrv-c'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Single Channel Receiver',
        'deviceString': 'scr',
        'hash': '0x0000005900010003',
        'sku': 'ho-scr-c'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Electric Switch',
        'deviceString': 'esw',
        'hash': '0x0000005900010010',
        'sku': 'ho-esw-d'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Dual Channel Receiver',
        'deviceString': 'dcr',
        'hash': '0x0000005900020003',
        'sku': 'ho-dcr-c'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Temperature Sensor',
        'deviceString': 'wts',
        'hash': '0x000000590002000D',
        'sku': 'ho-wts-a'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Electric Switch',
        'deviceString': 'esw',
        'hash': '0x0000005900020010',
        'sku': 'ho-esw-d'
    }, {
        'assignableZoneTypeIds': [1, 3, 5],
        'description': 'Room Thermostat',
        'deviceString': 'wrt',
        'hash': '0x0000005900030001',
        'sku': 'ho-wrt-b'
    }, {
        'assignableZoneTypeIds': [1, 3, 5],
        'description': 'Room Thermostat',
        'deviceString': 'wrt',
        'hash': '0x0000005900050001',
        'sku': 'ho-wrt-d'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Single Channel Receiver',
        'deviceString': 'scr',
        'hash': '0x0000005900050003',
        'sku': 'ho-scr-d'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Dual Channel Receiver',
        'deviceString': 'dcr',
        'hash': '0x0000005900060003',
        'sku': 'ho-dcr-d'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Smart Plug',
        'deviceString': 'plg',
        'hash': '0x0000006000010003',
        'sku': 'ev-plg-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Temperature Humidity Sensor',
        'deviceString': 'ths',
        'hash': '0x0000006000010006',
        'sku': 'es-ths-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Motion Sensor',
        'deviceString': 'wms',
        'hash': '0x0000006000020001',
        'sku': 'es-wms-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Temperature Sensor',
        'deviceString': 'wts',
        'hash': '0x00000071035D0002',
        'sku': 'ls-wts-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'CO2 Sensor',
        'deviceString': 'cos',
        'hash': '0x00000081000100A0',
        'sku': 'sa-cos-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Room Sensor',
        'deviceString': 'wrs',
        'hash': '0x0000008600050002',
        'sku': 'al-wrs-c'
    }, {
        'assignableZoneTypeIds': [1],
        'description': 'Gas Meter Reader',
        'deviceString': 'umr',
        'hash': '0x0000009600010010',
        'sku': 'nq-umr-a'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Smart Plug',
        'deviceString': 'plg',
        'hash': '0x0000013C00010001',
        'sku': 'ph-plg-c'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Room Sensor',
        'deviceString': 'wrs',
        'hash': '0x0000013C00020002',
        'sku': 'ph-wrs-a'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Room Sensor',
        'deviceString': 'wrs',
        'hash': '0x0000013C000C0002',
        'sku': 'ph-wrs-b'
    }, {
        'assignableZoneTypeIds': [3, 5],
        'description': 'Room Sensor',
        'deviceString': 'wrs',
        'hash': '0x0000013C000D0002',
        'sku': 'ph-wrs-b'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Electric Switch',
        'deviceString': 'esw',
        'hash': '0x0000013C000F0001',
        'sku': 'ph-esw-b'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Electric Switch',
        'deviceString': 'esw',
        'hash': '0x0000013C00100001',
        'sku': 'ph-esw-a'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Smart Plug',
        'deviceString': 'plg',
        'hash': '0x0000013C00110001',
        'sku': 'ph-plg-c'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'In Wall Meter',
        'deviceString': 'iwm',
        'hash': '0x0000013C001A0006',
        'sku': 'ph-iwm-a'
    }, {
        'assignableZoneTypeIds': [1, 2, 3, 5, 6],
        'description': 'Smart Plug',
        'deviceString': 'plg',
        'hash': '0x0000015400011100',
        'sku': 'po-plg-b'
    }
]
