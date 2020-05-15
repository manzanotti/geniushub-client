"""Python client library for the Genius Hub API."""

import logging
import re
from typing import Dict, List  # Any, Optional, Set, Tuple
from dataclasses import dataclass

from .const import (
    ATTRS_ZONE,
    FOOTPRINT_MODES,
    IDAY_TO_DAY,
    IMODE_TO_MODE,
    ITYPE_TO_TYPE,
    MODE_TO_IMODE,
    TYPE_TO_ITYPE,
    ZONE_KIT,
    ZONE_MODE,
    ZONE_TYPE,
)
from .device import GeniusBase

_LOGGER = logging.getLogger(__name__)


def natural_sort(dict_list, dict_key) -> List[Dict]:
    """Return a case-insensitively sorted list with '11' after '2-2'."""

    def alphanum_key(k):
        return [
            int(c) if c.isdigit() else c.lower()
            for c in re.split("([0-9]+)", k[dict_key])
        ]

    return sorted(dict_list, key=alphanum_key)


@dataclass
class CurrentState:
    """The current state of the zone.

        Intended to be properties that can change in the lifecycle of the zone.
    """

    is_active: bool = False
    is_requesting_heat: bool = False
    mode: int = 0
    mode_name: str = ""
    temperature: float = 0.0
    setpoint: float = 0.0  # TODO: was set_point
    is_occupied: bool = False


@dataclass
class Properties:
    """The properties of the zone.

        Intended to be the properties that are fixed for the lifecycle of the zone
    """

    type: int = 0  # TODO: avoid 'type' - I think reserved word, zone_type?
    type_name: str = ""
    has_room_sensor: bool = False


@dataclass
class DaySchedule:
    """The day in a schedule. Contains a list of heating periods."""

    index: int
    name: str  # TODO: do we need both - one is a Fx of the other
    default_setpoint: float
    heating_periods: List  # TODO: set a default value for this & for all?


@dataclass
class HeatingPeriod:
    """The heating period data."""

    start: int
    end: int
    setpoint: float  # TODO: set_point


@dataclass
class Override:
    """The override data for the zone."""

    duration: int
    setpoint: float  # TODO: was set_point


@dataclass
class WarmUp:
    """The warmup data for the zone."""

    enabled: bool = False
    calcs_enabled: bool = False
    lag_time: int = 0
    rise_rate: float = 0
    rise_time: int = 0
    total_time: int = 0


@dataclass
class Reactive:
    """The reactive data for the zone."""

    activity_level: float = 0.0


@dataclass
class Footprint:
    """The footprint data for the zone."""

    is_night: bool = False
    reactive: Reactive = None


@dataclass
class Trigger:
    """The trigger data for the zone."""

    reactive: bool = False
    output: int = 0


class GeniusZone(GeniusBase):
    """The class for a Genius Zone."""

    def __init__(self, zone_id, raw_json, hub) -> None:
        super().__init__(zone_id, raw_json, hub, ATTRS_ZONE)

        self._state = CurrentState()
        self._properties = Properties()
        self._footprint = Footprint()
        self._trigger = Trigger()
        self._timer_schedule = []
        self._footprint_schedule = []
        self._override = None
        self._warmup = WarmUp()
        self.device_objs = []
        self.device_by_id = {}

        if self._hub.api_version == 3:
            self.update(raw_json)

    def update(self, json):
        """Parse the json and use it to populate the data classes."""
        self.update_properties(json)
        self.update_state(json)

        # TODO: Whole-house zones don't have time schedules
        if json["iType"] not in [ZONE_TYPE.Manager, ZONE_TYPE.Surrogate]:
            self.update_timer_schedule(json)

        if json["iType"] in [ZONE_TYPE.ControlSP]:
            self.update_footprint_schedule(json)
            self.update_footprint(json)
            self.update_warmup(json)  # TODO: leave here, or with timer (or both)?

        self.update_override(json)
        self.update_trigger(json)
        self.update_is_occupied(json)
        return

    @property
    def data_new(self) -> Dict:  # TODO replace data with something like this
        """Make this is the missing docstring."""
        if self._hub.api_version == 1:
            return self._raw

        return {
            k[1:]: v
            for k, v in self.__dict__.items()
            if k.startswith("_") and k not in ["_attrs", "_data", "_raw", "_hub"]
        }

    @property
    def data(self) -> Dict:
        """Convert a zone's v3 JSON to the v1 schema."""
        if self._data:
            return self._data
        if self._hub.api_version == 1:
            self._data = self._raw
            return self._data

        def is_occupied(node) -> bool:  # from web app v5.2.4
            """Occupancy vs Activity (code from app.js, search for 'occupancyIcon').

            R = occupancy not detected (valid in any mode)
            O = occupancy detected (valid in any mode)
            A = occupancy detected, sufficient to call for heat (iff in Sense/FP mode)

            l = null != i.settings.experimentalFeatures && i.settings.experimentalFeatures.timerPlus,
            p = parseInt(n.iMode) === e.zoneModes.Mode_Footprint || l,    # sense mode?
            u = parseInt(n.iFlagExpectedKit) & e.equipmentTypes.Kit_PIR,  # has a PIR
            d = n.trigger.reactive && n.trigger.output,
            c = parseInt(n.zoneReactive.fActivityLevel) || 0,
            s = t.isInFootprintNightMode(n),                              # night time

            occupancyIcon() = p && u && d && !s ? a : c > 0 ? o : r

            Hint: the following returns "XX">> true ? "XX" : "YY"
            """
            A = O = True  # noqa: E741
            R = False

            l = True  # noqa: E741                                         TODO: WIP
            p = node["iMode"] == ZONE_MODE.Footprint | l  # #                    Checked
            u = node["iFlagExpectedKit"] & ZONE_KIT.PIR  # #                     Checked
            d = node["trigger"]["reactive"] & node["trigger"]["output"]  # #     Checked
            c = node["zoneReactive"]["fActivityLevel"]  # # needs int()?   TODO: WIP
            s = node["objFootprint"]["bIsNight"]  # #                      TODO: WIP

            return A if p and u and d and (not s) else (O if c > 0 else R)

        def timer_schedule(raw_json) -> Dict:
            root = {"weekly": {}}
            day = -1

            setpoints = raw_json["objTimer"]
            for idx, setpoint in enumerate(setpoints):
                tm_next = setpoint["iTm"]
                sp_next = setpoint["fSP"]
                if raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                    sp_next = bool(sp_next)

                if setpoint["iDay"] > day:
                    day += 1
                    node = root["weekly"][IDAY_TO_DAY[day]] = {}
                    node["defaultSetpoint"] = sp_next
                    node["heatingPeriods"] = []

                elif sp_next != node["defaultSetpoint"]:
                    # reactive = self._hub._sense_mode & bool(setpoint.get("bReactive"))
                    if len(setpoints) == idx + 1 or setpoints[idx + 1]["iTm"] == -1:
                        tm_last = 86400  # 24 * 60 * 60
                    else:
                        tm_last = setpoints[idx + 1]["iTm"]

                    node["heatingPeriods"].append(
                        {"end": tm_last, "start": tm_next, "setpoint": sp_next}
                    )

            return root

        def footprint_schedule(raw_json) -> Dict:
            root = {"weekly": {}}
            day = -1

            footprint_data = raw_json["objFootprint"]

            footprint_away_setpoint = footprint_data["fFootprintAwaySP"]
            footprint_tm_night_start = footprint_data["iFootprintTmNightStart"]

            footprint_setpoints = footprint_data["lstSP"]
            for idx, setpoint in enumerate(footprint_setpoints):
                tm_next = setpoint["iTm"]
                sp_next = setpoint["fSP"]

                if setpoint["iDay"] > day:
                    day += 1
                    node = root["weekly"][IDAY_TO_DAY[day]] = {}
                    node["defaultSetpoint"] = footprint_away_setpoint
                    node["heatingPeriods"] = []

                if sp_next != footprint_away_setpoint:
                    if tm_next == footprint_tm_night_start:
                        tm_last = 86400  # 24 * 60 * 60
                    else:
                        tm_last = footprint_setpoints[idx + 1]["iTm"]

                    node["heatingPeriods"].append(
                        {"end": tm_last, "start": tm_next, "setpoint": sp_next}
                    )

            return root

        self._data = result = {"id": self._raw["iID"], "name": self._raw["strName"]}
        raw_json = self._raw  # TODO: remove raw_json, use self._raw

        try:  # convert zone (v1 attributes)
            result["type"] = ITYPE_TO_TYPE[raw_json["iType"]]
            if raw_json["iType"] == ZONE_TYPE.TPI and raw_json["zoneSubType"] == 0:
                result["type"] = ITYPE_TO_TYPE[ZONE_TYPE.ControlOnOffPID]

            result["mode"] = IMODE_TO_MODE[raw_json["iMode"]]

            self.update_properties(raw_json)

            if raw_json["iType"] in [ZONE_TYPE.ControlSP, ZONE_TYPE.TPI]:
                # some zones have a fPV without raw_json["activeTemperatureDevices"]
                result["temperature"] = raw_json["fPV"]
                result["setpoint"] = raw_json["fSP"]

            if raw_json["iType"] == ZONE_TYPE.Manager:
                if raw_json["fPV"]:
                    result["temperature"] = raw_json["fPV"]

            elif raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                result["setpoint"] = bool(raw_json["fSP"])

            if self._has_pir:
                if TYPE_TO_ITYPE[result["type"]] == ZONE_TYPE.ControlSP:
                    result["occupied"] = is_occupied(raw_json)
                else:
                    result["_occupied"] = is_occupied(raw_json)

            if raw_json["iType"] in [
                ZONE_TYPE.OnOffTimer,
                ZONE_TYPE.ControlSP,
                ZONE_TYPE.TPI,
            ]:
                result["override"] = {}
                result["override"]["duration"] = raw_json["iBoostTimeRemaining"]
                if raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                    result["override"]["setpoint"] = raw_json["fBoostSP"] != 0
                else:
                    result["override"]["setpoint"] = raw_json["fBoostSP"]

            result["schedule"] = {"timer": {}, "footprint": {}}  # for all zone types

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Zone %s.", result["id"])

        try:  # convert timer schedule (v1 attributes)
            if raw_json["iType"] not in [
                ZONE_TYPE.Manager,
                ZONE_TYPE.Surrogate,
            ]:  # timer = {} if: Manager, Group
                result["schedule"]["timer"] = timer_schedule(raw_json)

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Zone %s timer schedule.", result["id"])

        try:  # convert footprint schedule (v1 attributes)
            if raw_json["iType"] in [ZONE_TYPE.ControlSP]:
                # footprint={...} iff: ControlSP, _even_ if no PIR, otherwise ={}
                result["schedule"]["footprint"] = footprint_schedule(raw_json)
                result["_schedule"] = {
                    "footprint": {
                        "profile": FOOTPRINT_MODES[raw_json["objFootprint"]["iProfile"]]
                    }
                }

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception(
                "Failed to convert Zone %s footprint schedule.", result["id"]
            )

        try:  # convert extras (v3 attributes)
            keys = ["bIsActive", "bOutRequestHeat"]
            result["_state"] = {k: raw_json[k] for k in keys}

            self.update_state(raw_json)

            if raw_json["iType"] in [ZONE_TYPE.ControlSP]:
                key = "bInHeatEnabled"
                result["_state"][key] = raw_json[key]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Zone %s extras.", result["id"])

        return self._data

    def update_state(self, json):
        """Parse the json and use it to populate the state data class."""
        try:
            self._state.is_active = json["bIsActive"]
            self._state.is_requesting_heat = json["bOutRequestHeat"]

            if json["iType"] in [ZONE_TYPE.ControlSP, ZONE_TYPE.TPI]:
                # some zones have a fPV without raw_json["activeTemperatureDevices"]
                self._state.temperature = json["fPV"]
                self._state.setpoint = json["fSP"]  # TODO: setpoint for consistency

            if json["iType"] == ZONE_TYPE.Manager and "fPV" in json:
                # TODO: this attr should not exist rather than be None/Unassigned
                self._state.temperature = json["fPV"]  # that's why this isn't a .get()

            self._state.mode = json["iMode"]
            self._state.mode_name = IMODE_TO_MODE[self._state.mode]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s state.", self.id)

    def update_properties(self, json):
        """Parse the json and use it to populate the properties data class."""
        try:
            self._properties.type = iType = json["iType"]
            if iType == ZONE_TYPE.TPI and json["zoneSubType"] == 0:
                self._properties.type = ZONE_TYPE.ControlOnOffPID

            self._properties.type_name = ITYPE_TO_TYPE[self._properties.type]
            self._properties.has_room_sensor = json["iFlagExpectedKit"] & ZONE_KIT.PIR

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s properties.", self.id)

    def update_footprint(self, json):
        """Parse the json and use it to populate the footprint data class."""
        try:
            self._footprint.is_night = json["objFootprint"]["bIsNight"]

            self._footprint.reactive = Reactive(
                json["objFootprint"]["objReactive"]["fActivityLevel"]
            )

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s footprint.", self.id)

    def update_trigger(self, json):
        """Parse the json and use it to populate the trigger data class."""
        try:
            self._trigger.reactive = json["trigger"]["reactive"]
            self._trigger.output = json["trigger"]["output"]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s trigger.", self.id)

    def update_is_occupied(self, json):
        """Parse the json and use it to populate is_occupied on the state data class."""
        try:
            if not self._properties.has_room_sensor:
                self._state.is_occupied = False
            elif self._footprint.is_night:
                self._state.is_occupied = False
            elif not self._trigger.reactive | self._trigger.output:
                self._state.is_occupied = False
            else:
                self._state.is_occupied = self._footprint.reactive.activity_level > 0.0

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s is_occupied.", self.id)

    def update_timer_schedule(self, json):
        """Parse the json and use it to populate the timer_schedule data class."""
        try:
            day_idx = -1
            setpoints = json["objTimer"]  # NOTE: Zone 0 does not have

            for idx, setpoint in enumerate(setpoints):
                start_time = setpoint["iTm"]
                temperature = setpoint["fSP"]
                if json["iType"] == ZONE_TYPE.OnOffTimer:
                    temperature = bool(temperature)

                if setpoint["iDay"] > day_idx:
                    day_idx += 1
                    day = DaySchedule(day_idx, IDAY_TO_DAY[day_idx], json["fSP"], [])
                    self._timer_schedule.append(day)

                # Only create a heating period if the temperature isn't at the default
                # setpoint for the room
                if temperature != day.default_setpoint:
                    # reactive = self._hub._sense_mode & bool(setpoint.get("bReactive"))
                    end_time = 86400  # default to the end of the day (in seconds)

                    # Unless the next heating period has a value
                    if (
                        len(setpoints) != idx + 1
                        and setpoints[idx + 1]["iTm"] != -1  # noqa: W503
                    ):
                        end_time = setpoints[idx + 1]["iTm"]

                    day.heating_periods.append(
                        HeatingPeriod(start_time, end_time, temperature)
                    )
                    self._timer_schedule[day_idx] = day

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s timer schedule.", self.id)

    def update_footprint_schedule(self, json):
        """Parse the json and use it to populate the footprint_schedule data class."""
        try:
            day_idx = -1
            setpoints = json["objFootprint"]["lstSP"]

            for idx, setpoint in enumerate(setpoints):
                start_time = setpoint["iTm"]
                temperature = setpoint["fSP"]

                if setpoint["iDay"] > day_idx:
                    day_idx += 1
                    day = DaySchedule(
                        day_idx,
                        IDAY_TO_DAY[day_idx],
                        json["objFootprint"]["fFootprintAwaySP"],
                        [],
                    )
                    self._footprint_schedule.append(day)

                # Only create a heating period if the temperature isn't at the default set point
                # for the room.
                if temperature != day.default_setpoint:
                    # reactive = self._hub._sense_mode & bool(setpoint.get("bReactive"))
                    end_time = 86400  # default to the end of the day (in seconds)

                    # Unless the next start time doesn't equal the default start of night time
                    if start_time != json["objFootprint"]["iFootprintTmNightStart"]:
                        end_time = setpoints[idx + 1]["iTm"]

                    day.heating_periods.append(
                        HeatingPeriod(start_time, end_time, temperature)
                    )
                    self._footprint_schedule[day_idx] = day

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s footprint schedule.", self.id)

    def update_override(self, json):
        """Parse the json and use it to populate the override data class."""
        self._override = None
        try:
            if json["iType"] in [
                ZONE_TYPE.OnOffTimer,
                ZONE_TYPE.ControlSP,
                ZONE_TYPE.TPI,
            ]:
                if json["iBoostTimeRemaining"] != 0:
                    self._override = Override(
                        json["iBoostTimeRemaining"], json["fBoostSP"]
                    )

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s override.", self.id)

    def update_warmup(self, json):
        """Parse the json and use it to populate the warmup data class."""
        try:
            warmup = json["warmupDuration"]
            if warmup is not None:
                self._warmup.enabled = warmup["bEnable"]
                self._warmup.calcs_enabled = warmup["bEnableCalcs"]
                self._warmup.rise_rate = warmup["fRiseRate"]
                self._warmup.lag_time = warmup["iLagTime"]
                self._warmup.rise_time = warmup["iRiseTime"]
                self._warmup.total_time = warmup["iTotalTime"]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to set Zone %s warmup.", self.id)

    @property
    def state(self) -> CurrentState:
        """Return the current state of the zone."""
        return self._state

    @property
    def properties(self) -> Properties:
        """Return the properties of the zone."""
        return self._properties

    @property
    def timer_schedule(self) -> List:
        """Return the timer schedule."""
        return self._timer_schedule

    @property
    def footprint_schedule(self) -> List:
        """Return the footprint schedule."""
        return self._footprint_schedule

    @property
    def override(self) -> Override:
        """Return the override data."""
        return self._override

    @property
    def warmup(self) -> WarmUp:
        """Return the warmup data."""
        return self._warmup

    @property
    def footprint(self) -> Footprint:
        """Return the footprint data (not including the schedule)."""
        return self._footprint

    @property
    def trigger(self) -> Trigger:
        """Return the trigger data."""
        return self._trigger

    @property
    def name(self) -> str:
        """Return the name of the zone, which can change."""
        return self.data["name"]

    @property
    def _has_pir(self) -> bool:
        """Return True if the zone has a PIR (movement sensor)."""
        if self._hub.api_version == 1:
            return "occupied" in self.data
        return self._raw["iFlagExpectedKit"] & ZONE_KIT.PIR

    @property
    def devices(self) -> List:
        """Return information for devices assigned to a zone.

          This is a v1 API: GET /zones/{zoneId}devices
        """
        key = "addr" if self._hub.verbosity == 3 else "id"
        return natural_sort([d.info for d in self.device_objs], key)

    @property
    def issues(self) -> List:
        """Return a list of Issues known to the Zone."""
        raise NotImplementedError

    async def set_mode(self, mode) -> None:
        """Set the mode of the zone.

          mode is in {'off', 'timer', footprint', 'override'}
        """
        allowed_modes = [ZONE_MODE.Off, ZONE_MODE.Override, ZONE_MODE.Timer]

        if self._has_pir:
            allowed_modes += [ZONE_MODE.Footprint]
        allowed_mode_strs = [IMODE_TO_MODE[i] for i in allowed_modes]

        if isinstance(mode, int) and mode in allowed_modes:
            mode_str = IMODE_TO_MODE[mode]
        elif isinstance(mode, str) and mode in allowed_mode_strs:
            mode_str = mode
            mode = MODE_TO_IMODE[mode_str]
        else:
            raise TypeError(f"Zone.set_mode(): mode='{mode}' isn't valid.")

        _LOGGER.debug(
            "Zone(%s).set_mode(mode=%s, mode_str='%s')...", self.id, mode, mode_str
        )

        if self._hub.api_version == 1:
            url = f"zones/{self.id}/mode"  # v1 API uses strings
            resp = await self._hub.request("PUT", url, data=mode_str)
        else:  # self._hub.api_version == 3
            url = f"zone/{self.id}"  # TODO: check: is it PUT(POST?) vs PATCH
            resp = await self._hub.request("PATCH", url, data={"iMode": mode})

        if resp:  # for v1, resp = None?
            resp = resp["data"] if resp["error"] == 0 else resp
        _LOGGER.debug("Zone(%s).set_mode(): response = %s", self.id, resp)

    async def set_override(self, setpoint, duration=None) -> None:
        """Set the zone to override to a certain temperature.

          duration is in seconds
          setpoint is in degrees Celsius
        """
        setpoint = float(setpoint)
        duration = int(duration) if duration else 3600

        _LOGGER.debug(
            "Zone(%s).set_override(setpoint=%s, duration=%s)...",
            self.id,
            setpoint,
            duration,
        )

        if self._hub.api_version == 1:
            url = f"zones/{self.id}/override"
            data = {"setpoint": setpoint, "duration": duration}
            resp = await self._hub.request("POST", url, data=data)
        else:  # self._hub.api_version == 3
            url = f"zone/{self.id}"
            data = {
                "iMode": ZONE_MODE.Boost,
                "fBoostSP": setpoint,
                "iBoostTimeRemaining": duration,
            }
            resp = await self._hub.request("PATCH", url, data=data)

        if resp:  # for v1, resp = None?
            resp = resp["data"] if resp["error"] == 0 else resp
        _LOGGER.debug("Zone(%s).set_override_temp(): response = %s", self.id, resp)
