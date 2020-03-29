"""Constants based upon module.exports from the vendor's source file."""

# From bower.js

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
]

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

ZONE_TYPES_MODEL = [
    {"string": "Manager", "typeId": 1, "defaultSettings": {}},
    {"string": "On / Off", "typeId": 2, "defaultSettings": {}},
    {"string": "Radiator", "typeId": 3, "defaultSettings": {}},
    {"string": "Wet Underfloor", "typeId": 5, "defaultSettings": {"zoneSubType": 0}},
    {
        "string": "Hot Water Temperature",
        "typeId": 5,
        "defaultSettings": {"zoneSubType": 2},
    },
    {"string": "Group", "typeId": 6, "defaultSettings": {}},
]

MODES_MODEL = [
    {"modeId": 0x0001, "string": "off"},
    {"modeId": 0x0002, "string": "timer"},
    {"modeId": 0x0004, "string": "footprint"},
    {"modeId": 0x0008, "string": "off"},
    {"modeId": 0x0010, "string": "override"},
    {"modeId": 0x0020, "string": "early"},
    {"modeId": 0x0040, "string": "test"},
    {"modeId": 0x0080, "string": "linked"},
    {"modeId": 0x0100, "string": "other"},
]

ZONE_KIT_MODEL = [
    {"type": "Temp", "flag": 0x0001},
    {"type": "Valve", "flag": 0x0002},
    {"type": "PIR", "flag": 0x0004},
    {"type": "Power", "flag": 0x0008},
    {"type": "Switch", "flag": 0x0010},
    {"type": "Dimmer", "flag": 0x0020},
    {"type": "Alarm", "flag": 0x0040},
    {"type": "GlobalTemp", "flag": 0x0080},
    {"type": "Humidity", "flag": 0x0100},
    {"type": "Luminance", "flag": 0x0200},
    {"type": "GasMeter", "flag": 0x0400},
    {"type": "CO2", "flag": 0x0800},
]

# from csv-data.js

# x = constant(
#     "hubinfo",
#     [
#         [48, "node:no_comms"],
#         [49, "node:not_seen"],
#         [50, "node:low_battery"],
#         [51, "node:warn_battery"],
#         [52, "node:assignment_limit_exceeded"],
#         [53, "manager:no_boiler_controller"],
#         [54, "manager:no_boiler_comms"],
#         [55, "manager:no_temp"],
#         [56, "include_new_device"],
#         [57, "zone:tpi_no_temp"],
#         [58, "zone:using_assumed_temp"],
#         [59, "zone:using_weather_temp"],
#         [60, "manager:weather"],
#         [61, "no_meta_data"],
#         [62, "login:hub_connection_broken"],
#         [63, "login:device_has_no_internet"],
#         [64, "login:hg_server_offline"],
#         [65, "login:internal_error"],
#         [66, "create_new_zone"],
#         [67, "device:configure"],
#         [68, "device:ping"],
#         [69, "device:remove_dead_node"],
#         [70, "node:bad_temp"],
#         [71, "hub_type"],
#     ],
# )

# from app.js, search fro 'Zone.Type.', 'hgNodeTools.equipmentTypes.'

# scope.renameChannels = function(channelName) {
# switch (channelName) {
# case 'Battery':
# return 'Battery Level';
# case 'HEATING_1':
# return 'Set Temperature';
# case 'SwitchBinary' || 'Switch Binary':
# return 'Output On/Off';
# case 'TEMPERATURE':
# return 'Measured Temperature';
# case 'LUMINANCE':
# return 'Luminance';
# case 'Motion':
# return 'Occupancy Trigger';
# }
# return channelName;

# scope.weekArray = [
#       {
#         'id': 0,
#         'name': "Sunday"
#       }, {
#         'id': 1,
#         'name': "Monday"
#       }, {
#         'id': 2,
#         'name': "Tuesday"
#       }, {
#         'id': 3,
#         'name': "Wednesday"
#       }, {
#         'id': 4,
#         'name': "Thursday"
#       }, {
#         'id': 5,
#         'name': "Friday"
#       }, {
#         'id': 6,
#         'name': "Saturday"
#       }


#     Zone = {};
#     Zone.Type = {
#       Manager: 1,
#       OnOffTimer: 2,
#       ControlSP: 3,
#       ControlOnOffPID: 4,
#       TPI: 5,
#       Surrogate: 6
#     };
#     Zone.ZoneModes = {
#       Mode_Off: 1,
#       Mode_Timer: 2,
#       Mode_Footprint: 4,
#       Mode_Away: 8,
#       Mode_Boost: 16,
#       Mode_Early: 32,
#       Mode_Test: 64,
#       Mode_Linked: 128,
#       Mode_Other: 256
#     };
#     Zone.EquipmentTypes = {
#       Kit_Temp: 0x0001,
#       Kit_Valve: 0x0002,
#       Kit_PIR: 0x0004,
#       Kit_Power: 0x0008,
#       Kit_Switch: 0x0010,
#       Kit_Dimmer: 0x0020,
#       Kit_Alarm: 0x0040,
#       Kit_GlobalTemp: 0x0080,
#       Kit_Humidity: 0x0100,
#       Kit_Luminance: 0x0200
#     };
#     Zone.ZoneFlags = {
#       Flag_Frost: 0x0001,
#       Flag_Timer: 0x0002,
#       Flag_Footprint: 0x0004,
#       Flag_Boost: 0x0008,
#       Flag_Away: 0x0010,
#       Flag_WarmupAuto: 0x0020,
#       Flag_WarmupManual: 0x0040,
#       Flag_Reactive: 0x0080,
#       Flag_Linked: 0x0100,
#       Flag_WeatherComp: 0x0200,
#       Flag_Temps: 0x0400,
#       Flag_TPI: 0x0800
#     };
#     canLink = function(masterZoneType) {
#       switch (masterZoneType) {
#         case Zone.Type.Manager:
#           return 0;
#         case Zone.Type.OnOffTimer:
#           return 1;
#         case Zone.Type.ControlSP:
#           return 1;
#         case Zone.Type.TPI:
#           return 1;
#         case Zone.Type.Surrogate:
#           return 0;
#         default:
#           return 0;
#       }
#     };


#     NodeDescription = {
#       '0x0000000000000000': 'Unrecognised Device',
#       '0x0000006000010003': 'Smart Plug',
#       '0x0000005900010003': 'Single Channel Receiver',
#       '0x0000005900020003': 'Dual Channel Receiver',
#       '0x0000005900050003': 'Single Channel Receiver',
#       '0x0000005900060003': 'Dual Channel Receiver',
#       '0x0000005900030001': 'Room Thermostat',
#       '0x0000005900050001': 'Room Thermostat',
#       '0x0000000200030005': 'Radiator Valve',
#       '0x0000000200040005': 'Radiator Valve',
#       '0x00000071035D0002': 'Temperature Sensor',
#       '0x0000008600050002': 'Room Sensor',
#       '0x0000009600010010': 'Gas Meter Reader',
#       '0x0000013C00100001': 'Electric Switch',
#       '0x0000013C000F0001': 'Electric Switch',
#       '0x0000013C00010001': 'Smart Plug',
#       '0x0000013C00290001': 'Smart Plug',
#       '0x0000013C00110001': 'Smart Plug',
#       '0x0000015400011100': 'Smart Plug',
#       '0x0000013C00020002': 'Room Sensor',
#       '0x0000013C000C0002': 'Room Sensor',
#       '0x0000013C000D0002': 'Room Sensor',
#       '0x0000013C00500002': 'Motion Sensor',
#       '0x0000000220008004': 'Underfloor Receiver',
#       '0x00000081000100A0': 'CO2 Sensor',
#       '0x000000590002000D': 'Temperature Sensor',
#       '0x0000005900020010': 'Electric Switch',
#       '0x0000005900010010': 'Electric Switch',
#       '0x0000006000020001': 'Motion Sensor',
#       '0x0000006000010006': 'Temperature Humidity Sensor',
#       '0x0000013C001A0006': 'In Wall Meter',
#       '0x00000002A0107FFF': 'Radiator Valve',
#       '0x0000000280100003': 'Room Thermostat',
#       'VIRTUAL': 'Virtual Node'
#     };
#     NodeSKU = {
#       '0x0000000000000000': 'N/A',
#       '0x0000006000010003': 'EV-PLG-A',
#       '0x0000005900010003': 'HO-SCR-C',
#       '0x0000005900050003': 'HO-SCR-D',
#       '0x0000005900020003': 'HO-DCR-C',
#       '0x0000005900060003': 'HO-DCR-D',
#       '0x0000005900030001': 'HO-WRT-B',
#       '0x0000005900050001': 'HO-WRT-D',
#       '0x0000000200030005': 'DA-WRV-A',
#       '0x0000000200040005': 'DA-WRV-B',
#       '0x00000071035D0002': 'LS-WTS-A',
#       '0x0000008600050002': 'AL-WRS-C',
#       '0x0000009600010010': 'NQ-UMR-A',
#       '0x0000013C00100001': 'PH-ESW-A',
#       '0x0000013C000F0001': 'PH-ESW-B',
#       '0x0000013C00010001': 'PH-PLG-C',
#       '0x0000013C00290001': 'PH-PLG-D',
#       '0x0000013C00110001': 'PH-PLG-C',
#       '0x0000015400011100': 'PO-PLG-B',
#       '0x0000013C00020002': 'PH-WRS-A',
#       '0x0000013C000C0002': 'PH-WRS-B',
#       '0x0000013C000D0002': 'PH-WRS-B',
#       '0x0000013C00500002': 'PH-WMS-B',
#       '0x0000000220008004': 'DA-SUR-B',
#       '0x00000081000100A0': 'SA-COS-A',
#       '0x000000590002000D': 'HO-WRT-A',
#       '0x0000005900020010': 'HO-ESW-D',
#       '0x0000005900010010': 'HO-ESW-D',
#       '0x0000006000020001': 'ES-WMS-A',
#       '0x0000006000010006': 'ES-THS-A',
#       '0x0000013C001A0006': 'PH-IWM-A',
#       '0x00000002A0107FFF': 'DA-WRV-C',
#       '0x0000000280100003': 'DA-WRT-C',
#       'VIRTUAL': 'Virtual Node'
#     };
#     zoneModes = {
#       Mode_Off: 1,
#       Mode_Timer: 2,
#       Mode_Footprint: 4,
#       Mode_Away: 8,
#       Mode_Boost: 16,
#       Mode_Early: 32,
#       Mode_Test: 64,
#       Mode_Linked: 128,
#       Mode_Other: 256
#     };
#     equipmentTypes = {
#       Kit_Temp: 0x0001,
#       Kit_Valve: 0x0002,
#       Kit_PIR: 0x0004,
#       Kit_Power: 0x0008,
#       Kit_Switch: 0x0010,
#       Kit_Dimmer: 0x0020,
#       Kit_Alarm: 0x0040,
#       Kit_GlobalTemp: 0x0080,
#       Kit_Humidity: 0x0100,
#       Kit_Luminance: 0x0200
#     };
#     zoneFlags = {
#       Flag_Frost: 0x0001,
#       Flag_Timer: 0x0002,
#       Flag_Footprint: 0x0004,
#       Flag_Boost: 0x0008,
#       Flag_Away: 0x0010,
#       Flag_WarmupAuto: 0x0020,
#       Flag_WarmupManual: 0x0040,
#       Flag_Reactive: 0x0080,
#       Flag_Linked: 0x0100,
#       Flag_WeatherComp: 0x0200,
#       Flag_Temps: 0x0400,
#       Flag_TPI: 0x0800
#     };


#     getNodeIssueAsString = function(id, data) {
#       var desc, obj;
#       if (data != null) {
#         desc = hgNodeTools.convertHashToNodeDescription(data.nodeHash);
#       }
#       switch (id) {
#         case 'node:no_comms':
#           obj = {
#             id: checkIssuesID(data.nodeID),
#             location: data.location,
#             description: desc,
#             details: '',
#             message: 'has lost communication with the Hub'
#           };
#           return obj;
#         case 'node:not_seen':
#           obj = {
#             id: checkIssuesID(data.nodeID),
#             location: data.location,
#             description: desc,
#             details: '',
#             message: 'has not been found by the Hub'
#           };
#           return obj;
#         case 'node:low_battery':
#           obj = {
#             id: checkIssuesID(data.nodeID),
#             location: data.location,
#             description: desc,
#             details: '',
#             message: 'battery is dead and needs to be replaced'
#           };
#           return obj;
#         case 'node:warn_battery':
#           obj = {
#             id: checkIssuesID(data.nodeID),
#             location: data.location,
#             description: desc,
#             details: data.batteryLevel,
#             message: 'battery is low'
#           };
#           return obj;
#         case 'manager:no_boiler_controller':
#           obj = {
#             id: '',
#             location: '',
#             description: '',
#             details: '',
#             message: 'My House does not have a boiler controller assigned'
#           };
#           return obj;
#         case 'manager:no_boiler_comms':
#           obj = {
#             id: '',
#             location: '',
#             description: '',
#             details: '',
#             message: 'Hub has lost communication with the boiler controller'
#           };
#           return obj;
#         case 'manager:no_temp':
#           obj = {
#             id: '',
#             location: '',
#             description: '',
#             details: '',
#             message: 'My House does not have a valid temperature'
#           };
#           return obj;
#         case 'manager:weather_data':
#           obj = {
#             id: '',
#             location: data.location,
#             description: desc,
#             details: data.detail,
#             message: 'Weather data -'
#           };
#           return obj;
#         case 'zone:using_weather_temp':
#           obj = {
#             id: '',
#             location: '',
#             description: '',
#             details: '',
#             message: "The " + data.zone.strName + " zone is currently using the outside temperature"
#           };
#           return obj;
#         case 'zone:using_assumed_temp':
#           obj = {
#             id: '',
#             location: '',
#             description: '',
#             details: '',
#             message: "The " + data.zone.strName + " zone is currently using the assumed temperature (as specified on the settings page)"
#           };
#           return obj;
#         case 'zone:tpi_no_temp':
#           obj = {
#             id: '',
#             location: '',
#             description: '',
#             details: '',
#             message: "The " + data.zone.strName + " zone has no valid temperature sensor"
#           };
#           return obj;
#       }
#     };

#     $scope.orderDeviceListBy = function(order) {
#       switch (order) {
#         case 'ID':
#           return $scope.deviceOrder = 'node.addr';
#         case 'Location':
#           return $scope.deviceOrder = 'node.childValues.location.val';
#         case 'Type':
#           return $scope.deviceOrder = 'description';
#         case 'Battery':
#           return $scope.deviceOrder = 'node.childValues.Battery.val';
#         case 'lastComm':
#           return $scope.deviceOrder = 'node.childValues.lastComms.val';
#         case 'airTemp':
#           return $scope.deviceOrder = 'node.childValues.TEMPERATURE.val';
#       }
#     };


# # angular.module('occupancyIcon', []).directive('hgOccupancyIcon', [
# #   'hgNodeTools', 'hgTimerTools', 'hgModals', '$rootScope', function(hgNodeTools, hgTimerTools, hgModals, $rootScope) {
# #     var generateTemplate, isZoneReactive, linkFunction;
# #     generateTemplate = function(zone) {

# def _is_occupied(node) -> bool:
#       # var _fullMan, currentSP, fullMan, greyMan, hollowMan, isNight, isTimerPlusEnabled, zoneHasRoomSensor, zoneModeFootprint, zoneOccupancyLevel, zoneReactiveHeatingTriggered, zoneSenseActive;

#       isTimerPlusEnabled = ($rootScope.settings.experimentalFeatures != null) && $rootScope.settings.experimentalFeatures.timerPlus;
#       zoneModeFootprint = node["iMode"] == ZONE_MODE.Footprint  # parseInt(zone.iMode) === hgNodeTools.zoneModes.Mode_Footprint;
#       zoneHasRoomSensor = node["iFlagExpectedKit"] & ZONE_KIT.PIR  # parseInt(zone.iFlagExpectedKit) & hgNodeTools.equipmentTypes.Kit_PIR;
#       zoneReactiveHeatingTriggered = zone.zoneReactive.bTriggerOn;
#       zoneOccupancyLevel = node["zoneReactive"]["fActivityLevel"]  # parseInt(zone.zoneReactive.fActivityLevel) || 0;
#       isNight = node["objFootprint"]["bIsNight"]  # hgTimerTools.isInFootprintNightMode(zone);
#       currentSP = hgTimerTools.getZoneTimerSetpointForCurrentTime(zone.objTimer);
#       zoneSenseActive = isTimerPlusEnabled && currentSP.reactiveEnabled;
#       fullMan = "<i class='icon hg-icon-full-man occupancy active' data-clickable='true'></i>";
#       hollowMan = "<i class='icon hg-icon-hollow-man occupancy active' data-clickable='true'></i>";
#       greyMan = "<i class='icon hg-icon-full-man occupancy' data-clickable='false'></i>";
#       _fullMan = zoneModeFootprint && zoneHasRoomSensor && zoneReactiveHeatingTriggered && !isNight;
#       console.debug("hgOccupancyIcon (zoneID=" + zone.iID + "): isTimerPlusEnabled=" + isTimerPlusEnabled + ", zoneHasRoomSensor=" + zoneHasRoomSensor + ", zoneReactiveHeatingTriggered=" + zoneReactiveHeatingTriggered + ", zoneOccupancyLevel=" + zoneOccupancyLevel + ", isNight=" + isNight + ", _fullMan=" + _fullMan + ", zoneOccupancyLevel=" + zoneOccupancyLevel + ", currentSP=" + (JSON.stringify(currentSP)) + ",");

#       if (zoneModeFootprint && zoneHasRoomSensor && zoneReactiveHeatingTriggered && !isNight) {
#         return fullMan;
#       } else if (zoneSenseActive && zoneHasRoomSensor && zoneReactiveHeatingTriggered) {
#         return fullMan;
#       } else if (zoneOccupancyLevel > 0) {
#         return hollowMan;
#       } else {
#         return greyMan;
#       }
#     };
#     isZoneReactive = function(zone) {
#       return zone.iMode === 4 && !hgTimerTools.isInFootprintNightMode(zone);
#     };
#     linkFunction = function(scope, el, attr) {
#       var removeWatcher, template;
#       template = generateTemplate(scope.zone);
#       el.html(template).show();
#       scope.formatRemainingOccupancyDuration = function(minutes) {
#         if (minutes === 0) {
#           return 1;
#         } else {
#           return minutes;
#         }
#       };
#       scope.$watchCollection('zone', function(newVal, oldVal) {
#         if (newVal !== oldVal) {
#           scope.isReactive = isZoneReactive(scope.zone);
#           template = generateTemplate(newVal);
#           return el.html(template).show();
#         }
#       });
#       scope.isReactive = isZoneReactive(scope.zone);
#       removeWatcher = scope.$watchCollection('zone', function(newVal, oldVal) {});
#       angular.element(el).on('click', function() {
#         var clickableElement;
#         if (scope.click != null) {

#         } else {
#           clickableElement = angular.element(el)[0].children[0].attributes[1].value;
#           if (clickableElement === "true") {
#             return hgModals.showOccupancyDetails(scope);
#           }
#         }
#       });
#       return scope.$on('destroy', function() {
#         el.remove();
#         return removeWatcher;
#       });
#     };
#     return {
#       restrict: 'E',
#       replace: true,
#       scope: {
#         zone: '=',
#         click: '='
#       },
#       link: linkFunction
#     };
#   }
# ]);
