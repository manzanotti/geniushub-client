from typing import Dict

from geniushubclient.const import ITYPE_TO_TYPE, TYPE_TO_ITYPE, ZONE_KIT, ZONE_TYPE


class Properties:
    """The properties of the zone.

    Intended to be the properties that are relatively static for
    the lifecycle of the zone"""

    def __init__(self):
        self._name: str = None
        self._zone_type: int = None
        self._subtype: int = None
        self._type_name: str = None
        self._has_room_sensor: bool = None

    def _update(self, json_data: Dict, api_version: int) -> None:
        """Parse the json and use it to populate the properties data class."""

        if api_version == 1:
            self._update_from_v1_data(json_data)
        elif api_version == 3:
            self._update_from_v3_data(json_data)

    def _update_from_v1_data(self, json_data: Dict) -> None:
        self._name = json_data["name"]
        self._type_name = json_data["type"]
        self._zone_type = TYPE_TO_ITYPE[self.type_name]
        self._has_room_sensor = "occupied" in json_data

    def _update_from_v3_data(self, json_data: Dict) -> None:
        self._name = json_data["strName"]
        self._zone_type = iType = json_data["iType"]
        self._subtype = json_data["zoneSubType"]
        self._has_room_sensor = json_data["iFlagExpectedKit"] & ZONE_KIT.PIR
        self._type_name = ITYPE_TO_TYPE[iType]

        if iType == ZONE_TYPE.TPI and json_data["zoneSubType"] == 0:
            self._zone_type = ZONE_TYPE.ControlOnOffPID
            self._type_name = ITYPE_TO_TYPE[ZONE_TYPE.ControlOnOffPID]

    def _get_v1_data(self) -> Dict:
        result = {}
        result["name"] = self._name
        result["type"] = self._type_name

        return result

    @property
    def name(self) -> str:
        """Return the name of the zone."""
        return self._name

    @property
    def zone_type(self) -> int:
        """Return the zone type integer representation of the zone."""
        return self._zone_type

    @property
    def subtype(self) -> int:
        """Return the zone subtype integer representation of the zone."""
        return self._subtype

    @property
    def type_name(self) -> str:
        """Return the name of the type of zone."""
        return self._type_name

    @property
    def has_room_sensor(self) -> bool:
        """Return whether the zone has a PIR (movement sensor)."""
        return self._has_room_sensor
