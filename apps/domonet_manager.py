import json
import subprocess
from time import sleep
from typing import Any

import appdaemon.plugins.hass.hassapi as hass

DOMONET_ENTITY_SENSOR_DEVICES = "sensor.domonet_devices"
DOMONET_ENTITY_SWITCH_GLOBAL_INTERNET = "switch.domonet_internet_all"
DOMONET_ENTITY_SWITCH_DEVICE_INTERNET_PREFIX = "switch.domonet_internet_device_"

HA_STATE_UNAVAILABLE = "unavailable"


class DomonetManager(hass.Hass):

    # noinspection attribute-outside-init
    def initialize(self):
        self.domonet_interface = self.args["domonet_interface"]
        self.external_interface = self.args["external_interface"]
        self.check_global_command = self.args["check_global_command"]
        self.enable_global_command = self.args["enable_global_command"]
        self.disable_global_command = self.args["disable_global_command"]
        self.device_list_command = self.args["device_list_command"]
        self.check_device_command = self.args["check_device_command"]
        self.enable_device_command = self.args["enable_device_command"]
        self.disable_device_command = self.args["disable_device_command"]

        self.set_namespace("domonet")

        # FIXME workaround for race condition: the hass namespace might not exist yet
        while not self.namespace_exists("hass"):
            self.logger.debug("Waiting for hass namespace")
            sleep(1)

        # initialize some internal and external (i.e., on HA) state
        self.init_state()

        # subscribe to all switch events so we can handle our own switches
        for svc in ("turn_on", "turn_off", "toggle"):
            # noinspection bad-argument-type
            self.listen_event(self._on_service, "call_service",
                              domain="switch", service=svc, namespace="hass")

    def init_state(self):
        # make sure the entity exists before doing the first real check
        self.update_global_internet_entity(None)

        global_state = self.query_global_internet_status()
        self.update_global_internet_entity(global_state)

        self._on_update_devices()
        # setup timer for periodic device list updates
        self.run_every(self._on_update_devices, "now", 15)

    def _on_update_devices(self, **kwargs):
        devices = self.query_devices()
        self.update_device_list_entity(devices)
        if devices:
            self.create_device_entities(devices)

    def _on_service(self, event_type: str, data: dict[str, Any],
                    **kwargs: Any) -> None:
        service_data = data["service_data"]
        entity_ids = service_data.get("entity_id")
        if not entity_ids:
            return
        if type(entity_ids) == str:
            entity_ids = [entity_ids]

        for entity_id in entity_ids:
            if entity_id == DOMONET_ENTITY_SWITCH_GLOBAL_INTERNET:
                self.on_global_internet_switch(data["service"])
            elif entity_id.startswith(DOMONET_ENTITY_SWITCH_DEVICE_INTERNET_PREFIX):
                self.on_device_internet_switch(entity_id, data["service"])

    def on_global_internet_switch(self, service: str):
        """Handle operations (turn off, turn on, toggle) on the global internet switch entity."""
        self.logger.debug("Global internet switch actioned (%s)", service)
        enabled = self.query_global_internet_status()
        if enabled is None:
            self.logger.warning("Unable to determine global internet status")
            # unable to get current status, disable entity and give up
            self.update_global_internet_entity(None)
        else:
            if service == "turn_on":
                if not enabled:
                    self.enable_global_internet()
            elif service == "turn_off":
                if enabled:
                    self.disable_global_internet()
            elif service == "toggle":
                if enabled:
                    self.disable_global_internet()
                else:
                    self.enable_global_internet()
            else:
                raise ValueError("Unsupported switch operation: " + service)

            enabled = self.query_global_internet_status()
            self.update_global_internet_entity(enabled)

    def on_device_internet_switch(self, entity_id: str, service: str):
        self.logger.debug("Device '%s' internet switch actioned (%s)", entity_id, service)
        # we need the entity state for the device name and address
        entity_state = self.get_state(entity_id, attribute="all", namespace="hass")
        device_name = entity_state.get("attributes", {}).get("device_name")
        device_address = entity_state.get("attributes", {}).get("device_address")
        self.logger.debug("Device name: %s, address: %s", device_name, device_address)
        if not device_name or not device_address:
            # something is wrong, do not proceed
            return

        enabled = self.query_device_internet_status(device_name, device_address)
        if enabled is None:
            self.logger.warning("Unable to determine device '%s' internet status", device_name)
            # unable to get current status, disable entity and give up
            self.update_device_internet_entity(device_name, device_address, None)
        else:
            if service == "turn_on":
                if not enabled:
                    self.enable_device_internet(device_name, device_address)
            elif service == "turn_off":
                if enabled:
                    self.disable_device_internet(device_name)
            elif service == "toggle":
                if enabled:
                    self.disable_device_internet(device_name)
                else:
                    self.enable_device_internet(device_name, device_address)
            else:
                raise ValueError("Unsupported switch operation: " + service)

            enabled = self.query_device_internet_status(device_name, device_address)
            self.update_device_internet_entity(device_name, device_address, enabled)

    def query_global_internet_status(self) -> bool | None:
        """
        Query the status of the global internet firewall.
        :return: A boolean for the status, or ``None`` if unable to determine.
        """
        cmd = self.check_global_command.split(" ")
        device_status = self._exec_simple(*cmd,
                                          self.domonet_interface,
                                          self.external_interface)
        if device_status is not None:
            # self.logger.debug("Status: %s", device_status)
            return device_status == "1"
        else:
            return None

    def enable_global_internet(self) -> bool:
        cmd = self.enable_global_command.split(" ")
        result = self._exec_simple(*cmd,
                                   self.domonet_interface,
                                   self.external_interface)
        return result is not None

    def disable_global_internet(self) -> bool:
        cmd = self.disable_global_command.split(" ")
        result = self._exec_simple(*cmd,
                                   self.domonet_interface,
                                   self.external_interface)
        return result is not None

    def update_global_internet_entity(self, state: bool | None):
        if state is None:
            entity_state = "unavailable"
        else:
            entity_state = "on" if state else "off"

        self.set_state(DOMONET_ENTITY_SWITCH_GLOBAL_INTERNET,
                       state=entity_state, attributes={
                "friendly_name": "Domonet global internet access",
                "icon": "mdi:home-automation",
                "last_changed": (self.datetime()).replace(
                    microsecond=0).isoformat(),
            }, check_existence=False, namespace="hass")

    def query_devices(self) -> list | None:
        cmd = self.device_list_command.split(" ")
        device_status = self._exec_json(cmd[0], *cmd[1:],
                                        self.domonet_interface)
        if device_status and device_status.get("clients"):
            return device_status["clients"]
        else:
            return None

    def update_device_list_entity(self, device_list: list | None):
        if device_list:
            self.set_state(DOMONET_ENTITY_SENSOR_DEVICES,
                           state=len(device_list), attributes={
                    "friendly_name": "Domonet devices",
                    "icon": "mdi:home-automation",
                    "last_changed": (self.datetime()).replace(
                        microsecond=0).isoformat(),
                    "clients": device_list,
                }, check_existence=False, namespace="hass")

    def create_device_entities(self, device_list):
        for device in device_list:
            device_name = device["name"]
            device_address = device["address"]
            state = self.query_device_internet_status(device_name, device_address)
            self.update_device_internet_entity(device_name, device_address, state)

    def update_device_internet_entity(self, device_name: str, device_address: str, state: bool | None):
        if state is None:
            entity_state = "unavailable"
        else:
            entity_state = "on" if state else "off"

        self.set_state(DOMONET_ENTITY_SWITCH_DEVICE_INTERNET_PREFIX + self._normalize_device_name(device_name),
                       state=entity_state, attributes={
                "friendly_name": self._friendly_device_name(device_name),
                "icon": "mdi:home-automation",
                "device_name": device_name,
                "device_address": device_address,
                "last_changed": (self.datetime()).replace(microsecond=0).isoformat(),
            }, namespace="hass")

    def enable_device_internet(self, device_name: str, device_address: str) -> bool:
        cmd = self.enable_device_command.split(" ")
        result = self._exec_simple(*cmd,
                                   self.domonet_interface,
                                   self.external_interface,
                                   device_address,
                                   device_name)
        return result is not None

    def disable_device_internet(self, device_name: str) -> bool:
        cmd = self.disable_device_command.split(" ")
        result = self._exec_simple(*cmd, device_name)
        return result is not None

    @staticmethod
    def _friendly_device_name(name: str):
        return name \
            .replace("_", " ") \
            .replace("-", " ") \
            .strip() \
            .title()

    @staticmethod
    def _normalize_device_name(name: str):
        return name.replace("-", "")

    def query_device_internet_status(self, device_name: str, device_address: str):
        cmd = self.check_device_command.split(" ")
        device_status = self._exec_simple(*cmd,
                                          self.domonet_interface,
                                          self.external_interface,
                                          device_name,
                                          device_address)
        if device_status is not None:
            # self.logger.debug("Status: %s", device_status)
            return device_status == "1"
        else:
            return None

    def _exec_simple(self, *args: Any) -> str | None:
        """For commands returning a single line of output."""
        self.logger.debug("Executing command: %s", args)
        process = subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        exit_status = process.wait()
        if exit_status == 0:
            return stdout.strip("\n\r")
        else:
            self.logger.warning("Command returned %d", exit_status)
            return None

    def _exec_json(self, *args: Any) -> dict | None:
        """For commands returning a JSON object output."""
        self.logger.debug("Executing command: %s", args)
        process = subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        exit_status = process.wait()
        if exit_status == 0:
            return json.loads(stdout)
        else:
            self.logger.warning("Command returned %d", exit_status)
            return None
