"""Python client library for the Genius Hub API."""

import logging
from typing import Dict, Optional  # Any, List, Set, Tuple

import json

from .const import ATTRS_DEVICE, DEVICE_HASH_TO_TYPE, STATE_ATTRS

_LOGGER = logging.getLogger(__name__)


class GeniusBase:
    """The base class for any Genius object: Zone, Device or Issue."""

    def __init__(self, hub, object_attrs) -> None:
        self._hub = hub
        self._attrs = object_attrs

        self.data = {}
        self._raw = {}

    def __repr__(self) -> str:
        return json.dumps(
            {k: v for k, v in self.data.items() if k in self._attrs["summary_keys"]}
        )

    @property
    def info(self) -> Dict:
        """Return all information for the object."""
        if self._hub.verbosity == 3:
            return self._raw

        # tip: grep -E '("bOutRequestHeat"|"bInHeatEnabled")..true'
        if self._hub.verbosity == 2:
            return self.data

        keys = self._attrs["summary_keys"]
        if self._hub.verbosity == 1:
            keys += self._attrs["detail_keys"]

        return {k: v for k, v in self.data.items() if k in keys}


class GeniusDevice(GeniusBase):
    """The class for a Genius Device."""

    def __init__(self, device_id, raw_json, hub) -> None:
        super().__init__(hub, ATTRS_DEVICE)

        self.id = device_id

        self._convert(raw_json)

    def _convert(self, raw_json) -> None:
        """Convert a device's v3 JSON to the v1 schema."""
        self._raw = raw_json
        if self._hub.api_version == 1:
            self.data = raw_json
            return

        self.data = result = {"id": raw_json["addr"]}

        try:
            node = raw_json["childValues"]

            if "hash" in node:
                dev_type = DEVICE_HASH_TO_TYPE.get(node["hash"]["val"])
                if dev_type:
                    result["type"] = dev_type
            elif node["SwitchBinary"]["path"].count("/") == 3:
                result["type"] = f"Dual Channel Receiver - Channel {result['id'][-1]}"
            else:
                result["type"] = None

            result["assignedZones"] = [{"name": None}]
            if node["location"]["val"]:
                result["assignedZones"] = [{"name": node["location"]["val"]}]

            result["state"] = state = {}
            state.update(
                [(v, node[k]["val"]) for k, v in STATE_ATTRS.items() if k in node]
            )
            if "outputOnOff" in state:  # this one should be a bool
                state["outputOnOff"] = bool(state["outputOnOff"])

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Device %s.", result["id"])

        try:
            result["_state"] = _state = {}
            for val in ["lastComms", "setback"]:
                if val in node:
                    _state[val] = node[val]["val"]
            if "WakeUp_Interval" in node:
                _state["wakeupInterval"] = node["WakeUp_Interval"]["val"]

            node = raw_json["childNodes"]["_cfg"]["childValues"]

            result["_config"] = _config = {}
            for val in ["max_sp", "min_sp", "sku"]:
                if val in node:
                    _config[val] = node[val]["val"]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Device %s extras.", result["id"])

    @property
    def type(self) -> Optional[str]:
        """Return the type of the device, which can change."""
        return self.data.get("type")

    @property
    def assigned_zone(self) -> Optional[object]:
        """Return the primary assigned zone, which can change."""
        try:
            return self._hub.zone_by_name[self.data["assignedZones"][0]["name"]]
        except KeyError:
            return None
