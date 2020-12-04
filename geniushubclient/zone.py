"""Python client library for the Genius Hub API."""

import logging
import re
from typing import Dict, List  # Any, Optional, Set, Tuple

from geniushubclient.const import (
    ATTRS_ZONE,
    FOOTPRINT_MODES,
    IDAY_TO_DAY,
    IMODE_TO_MODE,
    MODE_TO_IMODE,
    ZONE_KIT,
    ZONE_MODE,
    ZONE_TYPE,
)
from geniushubclient.device import GeniusBase
from geniushubclient.zoneclasses.properties import Properties

_LOGGER = logging.getLogger(__name__)


def natural_sort(dict_list, dict_key) -> List[Dict]:
    """Return a case-insensitively sorted list with '11' after '2-2'."""

    def alphanum_key(k):
        return [
            int(c) if c.isdigit() else c.lower()
            for c in re.split("([0-9]+)", k[dict_key])
        ]

    return sorted(dict_list, key=alphanum_key)


class GeniusZone(GeniusBase):
    """The class for a Genius Zone."""

    def __init__(self, zone_id, raw_json, hub) -> None:
        super().__init__(zone_id, raw_json, hub, ATTRS_ZONE)

        self._properties = Properties()

        self.device_objs = []
        self.device_by_id = {}

        self._update(raw_json, self._hub.api_version)

    def _update(self, json_data: Dict, api_version: int):
        """Parse the json for the zone data."""
        try:
            self._properties._update(json_data, api_version)
        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Zone %s.", self.id)

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

            l = null != i.settings.experimentalFeatures
                && i.settings.experimentalFeatures.timerPlus,
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

            setpoints = raw_json["objFootprint"]
            for idx, setpoint in enumerate(setpoints["lstSP"]):
                tm_next = setpoint["iTm"]
                sp_next = setpoint["fSP"]

                if setpoint["iDay"] > day:
                    day += 1
                    node = root["weekly"][IDAY_TO_DAY[day]] = {}
                    node["defaultSetpoint"] = setpoints["fFootprintAwaySP"]
                    node["heatingPeriods"] = []

                if sp_next != setpoints["fFootprintAwaySP"]:
                    if tm_next == setpoints["iFootprintTmNightStart"]:
                        tm_last = 86400  # 24 * 60 * 60
                    else:
                        tm_last = setpoints["lstSP"][idx + 1]["iTm"]

                    node["heatingPeriods"].append(
                        {"end": tm_last, "start": tm_next, "setpoint": sp_next}
                    )

            return root

        self._data = result = {}
        result["id"] = self.id

        raw_json = self._raw  # TODO: remove raw_json, use self._raw

        try:  # convert zone (v1 attributes)
            properties_data = self._properties._get_v1_data()
            result.update(properties_data)

            result["mode"] = IMODE_TO_MODE[raw_json["iMode"]]

            if raw_json["iType"] in [ZONE_TYPE.ControlSP, ZONE_TYPE.TPI]:
                # some zones have a fPV without raw_json["activeTemperatureDevices"]
                result["temperature"] = raw_json["fPV"]
                result["setpoint"] = raw_json["fSP"]

            if raw_json["iType"] == ZONE_TYPE.Manager:
                if raw_json["fPV"]:
                    result["temperature"] = raw_json["fPV"]
            elif raw_json["iType"] == ZONE_TYPE.OnOffTimer:
                result["setpoint"] = bool(raw_json["fSP"])

            if self._properties.has_room_sensor:
                if raw_json["iType"] == ZONE_TYPE.ControlSP:
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
            result["_state"] = {"bIsActive": raw_json["bIsActive"]}
            result["output"] = int(raw_json["bOutRequestHeat"])

            if raw_json["iType"] in [ZONE_TYPE.ControlSP]:
                result["_state"]["bInHeatEnabled"] = raw_json["bInHeatEnabled"]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Zone %s extras.", result["id"])

        return self._data

    @property
    def properties(self) -> Properties:
        """Return the properties of the zone."""
        return self._properties

    @property
    def _has_pir(self) -> bool:
        """Return True if the zone has a PIR (movement sensor)."""
        return self._properties.has_room_sensor

    @property
    def name(self) -> str:
        """Return the name of the zone, which can change."""
        return self._properties.name

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
