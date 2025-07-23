
import appdaemon.plugins.hass.hassapi as hass

import string
import subprocess

#
# Creates binary sensors dynamically by watching the list of available domonet clients.
# Each binary sensor will reflect the Internet status for each device.
#


# noinspection PyAttributeOutsideInit
class DomonetDevices(hass.Hass):

    def initialize(self):
        self.add_namespace('domonet')
        self.devices_entity = self.args['devices_entity']
        self.devices_attribute = self.args['devices_attribute']
        self.check_command = self.args['check_command']
        self.domonet_interface = self.args['domonet_interface']
        self.external_interface = self.args['external_interface']
        self._timers = {}
        self.listen_event(self.update_event_single, 'domonet_update', namespace='hass')
        self.listen_state(self.update_event, self.devices_entity,
                          attribute=self.devices_attribute,
                          immediate=True,
                          namespace='hass')
        self.log("Domonet binary sensors support app started", level='INFO')

    async def update_event_single(self, event, data, kwargs):
        return await self.update_device(data)

    def update_event(self, entity, attribute, old, new, kwargs):
        self.log("Domonet clients changed: %s", new, level='DEBUG')
        for timer in self._timers.values():
            self.cancel_timer(timer)
        self._timers.clear()
        for device in new:
            self._timers[device['name']] = self.run_every(self.update_device, 'now', 60,
                                                          device_address=device['address'], device_name=device['name'])

    async def update_device(self, kwargs):
        device_name = kwargs['device_name']
        device_address = kwargs['device_address']
        self.log("Will update domonet client: %s [%s]", device_name, device_address, level='DEBUG')
        process = subprocess.Popen([*self.check_command.split(' '),
                                   self.domonet_interface,
                                   self.external_interface,
                                   device_name,
                                   device_address], stdout=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        exit_status = process.wait()
        if exit_status == 0:
            device_status = stdout.strip("\n\r")
            #self.log('Status: %s', device_status, level='DEBUG')
            state = 'on' if device_status == '1' else 'off'
            await self.set_state('binary_sensor.domonet_allowed_{}'.format(self._normalize_device_name(device_name)),
                                 state=state, attributes={
                    'friendly_name': self._friendly_device_name(device_name),
                    'device_name': device_name,
                    'device_address': device_address,
                    'last_changed': (await self.datetime()).replace(microsecond=0).isoformat(),
                }, namespace='hass')
        else:
            self.log('Client check command returned %d', exit_status, level='WARN')

    @staticmethod
    def _friendly_device_name(name: str):
        return name\
            .replace('_', ' ')\
            .replace('-', ' ')\
            .translate(str.maketrans('', '', string.digits))\
            .strip()\
            .title()

    @staticmethod
    def _normalize_device_name(name: str):
        return name.replace('-', '')
