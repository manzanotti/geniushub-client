"""Python client library for the Genius Hub API."""

import json
import logging
from abc import abstractmethod
from typing import Dict, Optional  # Any, List, Set, Tuple

from .const import ATTRS_DEVICE, DEVICE_HASH_TO_TYPE, SKU_BY_HASH, STATE_ATTRS

_LOGGER = logging.getLogger(__name__)


class GeniusBase:
    """The base class for any Genius object: Zone, Device or Issue."""

    def __init__(self, entity_id, raw_json, hub, entity_attrs) -> None:
        self.id = entity_id
        self._raw = raw_json
        self._hub = hub
        self._attrs = entity_attrs

        self._data = {}

    def __str__(self) -> str:
        return json.dumps(
            {k: v for k, v in self.data.items() if k in self._attrs["summary_keys"]}
        )

    @property
    def info(self) -> Dict:
        """Return information of the GH entity, detail according to verbosity."""
        if self._hub.verbosity == 3:
            return self._raw

        # tip: grep -E '("bOutRequestHeat"|"bInHeatEnabled")..true'
        if self._hub.verbosity == 2:
            return self.data

        keys = self._attrs["summary_keys"]
        if self._hub.verbosity == 1:
            keys += self._attrs["detail_keys"]

        return {k: v for k, v in self.data.items() if k in keys}

    @property
    @abstractmethod
    def data(self) -> Dict:
        """Return the data describing the entity."""
        pass


class GeniusDevice(GeniusBase):
    """The class for a Genius Device."""

    def __init__(self, device_id, raw_json, hub) -> None:
        super().__init__(device_id, raw_json, hub, ATTRS_DEVICE)

    @property
    def data(self) -> Dict:
        """Convert a device's v3 JSON to the v1 schema."""
        if self._data:
            return self._data
        if self._hub.api_version == 1:
            self._data = self._raw
            return self._data

        self._data = result = {"id": self._raw["addr"]}

        try:
            node = self._raw["childValues"]

            if "hash" in node:
                dev_type = DEVICE_HASH_TO_TYPE.get(node["hash"]["val"])
                if dev_type:
                    result["type"] = dev_type
            elif (
                "SwitchBinary" in node and node["SwitchBinary"]["path"].count("/") == 3
            ):
                result["type"] = f"Dual Channel Receiver - Channel {result['id'][-1]}"
            elif (
                "ThermostatMode" in node
                and node["ThermostatMode"]["path"].count("/") == 3
            ):
                result["type"] = f"Powered Room Thermostat - Channel {result['id'][-1]}"
            elif "TEMPERATURE" in node and node["TEMPERATURE"]["path"].count("/") == 3:
                result["type"] = f"Powered Room Thermostat - Channel {result['id'][-1]}"
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
            for val in ("lastComms", "setback"):
                if val in node:
                    _state[val] = node[val]["val"]
            if "WakeUp_Interval" in node:
                _state["wakeupInterval"] = node["WakeUp_Interval"]["val"]

            node_cfg = self._raw["childNodes"]["_cfg"]["childValues"]

            result["_config"] = _config = {}
            for val in ("max_sp", "min_sp", "sku"):
                if val in node_cfg:
                    _config[val] = node_cfg[val]["val"]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Device %s extras.", result["id"])

        try:
            result["_diagnostics"] = _diagnostics = {}
            node = self._raw["childValues"]

            # Device model/SKU from hash
            if "hash" in node:
                device_hash = node["hash"]["val"]
                sku = SKU_BY_HASH.get(device_hash)
                if sku:
                    _diagnostics["sku"] = sku.upper()  # Match app format (DA-WRV-B)
                _diagnostics["hash"] = device_hash

            # Firmware and protocol information
            for val in ("ApplicationVersion", "ProtocolVersion", "LibraryType"):
                if val in node:
                    _diagnostics[val] = node[val]["val"]

            # Device health and manufacturer
            for val in ("health", "manfID"):
                if val in node:
                    _diagnostics[val] = node[val]["val"]

            # Wake-up target node
            if "WakeUp_TargetNode" in node:
                _diagnostics["wakeupTargetNode"] = node["WakeUp_TargetNode"]["val"]

            # Protection state (for radiator valves)
            if "ProtectionState" in node:
                _diagnostics["protectionState"] = node["ProtectionState"]["val"]

            # Clock information (for devices that have it)
            if "ClockHour" in node and "ClockMinute" in node:
                _diagnostics["clockTime"] = {
                    "hour": node["ClockHour"]["val"],
                    "minute": node["ClockMinute"]["val"]
                }
                if "ClockWeekday" in node:
                    _diagnostics["clockTime"]["weekday"] = node["ClockWeekday"]["val"]

        except (AttributeError, LookupError, TypeError, ValueError):
            _LOGGER.exception("Failed to convert Device %s diagnostics.", result["id"])

        return self._data

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

    @property
    def battery_level(self) -> Optional[int]:
        """Return the battery level percentage, if available."""
        try:
            return self.data["state"].get("batteryLevel")
        except (KeyError, TypeError):
            return None

    @property
    def last_communication(self) -> Optional[int]:
        """Return the last communication timestamp (Unix epoch), if available."""
        try:
            return self.data["_state"].get("lastComms")
        except (KeyError, TypeError):
            return None

    @property
    def measured_temperature(self) -> Optional[float]:
        """Return the measured temperature in Celsius, if available."""
        try:
            return self.data["state"].get("measuredTemperature")
        except (KeyError, TypeError):
            return None

    @property
    def setpoint(self) -> Optional[float]:
        """Return the setpoint temperature in Celsius, if available."""
        try:
            return self.data["state"].get("setTemperature")
        except (KeyError, TypeError):
            return None

    @property
    def valve_offset(self) -> Optional[float]:
        """Return the valve hidden offset (setback), if available."""
        try:
            return self.data["_state"].get("setback")
        except (KeyError, TypeError):
            return None

    @property
    def wakeup_interval(self) -> Optional[int]:
        """Return the wake-up interval in seconds, if available."""
        try:
            return self.data["_state"].get("wakeupInterval")
        except (KeyError, TypeError):
            return None

    @property
    def protocol_version(self) -> Optional[str]:
        """Return the protocol version, if available."""
        try:
            return self.data["_diagnostics"].get("ProtocolVersion")
        except (KeyError, TypeError):
            return None

    @property
    def application_version(self) -> Optional[str]:
        """Return the application/firmware version, if available."""
        try:
            return self.data["_diagnostics"].get("ApplicationVersion")
        except (KeyError, TypeError):
            return None

    @property
    def location(self) -> Optional[str]:
        """Return the device location/zone name."""
        try:
            return self.data["assignedZones"][0]["name"]
        except (KeyError, TypeError, IndexError):
            return None

    @property
    def device_model(self) -> Optional[str]:
        """Return the device model/SKU (e.g., 'DA-WRV-B', 'HO-WRT-B')."""
        try:
            return self.data["_diagnostics"].get("sku")
        except (KeyError, TypeError):
            return None
