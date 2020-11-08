from geniushubclient.const import (
    IMODE_TO_MODE,
    ZONE_TYPE,
)


class State:
    """The current state of the zone.

        Intended to be properties that can change in the lifecycle of the zone.
    """

    is_active: bool = False
    is_requesting_heat: bool = False
    mode: int = 0
    mode_name: str = ""
    temperature: float = None
    setpoint: float = None
    is_occupied: bool = False
    heat_in_enabled: bool = None

    _zone_type: str = ""

    def __init__(self):
        return

    def update(self, json, zone_type):
        """Parse the json and use it to populate the state data class."""
        self._zone_type = zone_type
        self.is_active = json["bIsActive"]
        self.is_requesting_heat = json["bOutRequestHeat"]

        if zone_type in [ZONE_TYPE.ControlSP, ZONE_TYPE.TPI]:
            # some zones have a fPV without json["activeTemperatureDevices"]
            self.temperature = json["fPV"]
            self.setpoint = json["fSP"]

        if zone_type == ZONE_TYPE.Manager and "fPV" in json:
            self.temperature = json["fPV"]

        if zone_type == ZONE_TYPE.ControlSP:
            self.heat_in_enabled = json["bInHeatEnabled"]

        if zone_type == ZONE_TYPE.OnOffTimer:
            self.setpoint = json["fSP"]

        mode = json["iMode"]
        self.mode = mode
        self.mode_name = IMODE_TO_MODE[mode]

    def populate_v1_data(self, result):
        result["mode"] = self.mode_name
        result["output"] = int(self.is_requesting_heat)
        result["_state"] = {}
        result["_state"]["bIsActive"] = self.is_active

        if self.temperature is not None:
            result["temperature"] = self.temperature

        if self.setpoint is not None:
            if self._zone_type == ZONE_TYPE.OnOffTimer:
                result["setpoint"] = self.setpoint != 0.0
            else:
                result["setpoint"] = self.setpoint

        if self.heat_in_enabled is not None:
            result["_state"]["bInHeatEnabled"] = self.heat_in_enabled

        return result
