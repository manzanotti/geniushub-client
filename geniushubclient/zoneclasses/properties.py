from geniushubclient.const import (
    ITYPE_TO_TYPE,
    ZONE_KIT,
    ZONE_TYPE,
)


class Properties:
    """The properties of the zone.

        Intended to be the properties that are fixed for the lifecycle of the zone
    """

    id: int = 0
    name: str = ""
    zone_type: int = 0
    subtype: int = 0
    type_name: str = ""
    has_room_sensor: bool = False

    def __init__(self):
        return

    def update(self, json):
        """Parse the json and use it to populate the properties data class."""

        self.id = json["iID"]
        self.name = json["strName"]
        self.zone_type = iType = json["iType"]
        self.subtype = json["zoneSubType"]
        self.type_name = ITYPE_TO_TYPE[iType]
        self.has_room_sensor = json["iFlagExpectedKit"] & ZONE_KIT.PIR

        if iType == ZONE_TYPE.TPI and json["zoneSubType"] == 0:
            self.type_name = ITYPE_TO_TYPE[ZONE_TYPE.ControlOnOffPID]
            self.zone_type = ZONE_TYPE.ControlOnOffPID

    def populate_v1_data(self, result):
        result["id"] = self.id
        result["name"] = self.name
        result["type"] = self.type_name

        return result
