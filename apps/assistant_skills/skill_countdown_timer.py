
import appdaemon.plugins.hass.hassapi as hass

from datetime import timedelta

import json
import util

#
# Skill for a simple countdown timer.
#


# noinspection PyAttributeOutsideInit
class CountdownTimerSkill(hass.Hass):

    def initialize(self):
        self.session_id = None
        self.timer_entity = self.args['timer_entity']
        self.tts_templates = self.args['templates']
        self.listen_event(self.handle_set_timer, 'MQTT_MESSAGE',
                          topic='hermes/intent/' + self.args['intents']['set'],
                          namespace='mqtt')
        self.listen_event(self.handle_set_timer_duration, 'MQTT_MESSAGE',
                          topic='hermes/intent/slot_duration',
                          namespace='mqtt')
        self.listen_event(self.handle_get_timer, 'MQTT_MESSAGE',
                          topic='hermes/intent/' + self.args['intents']['get'],
                          namespace='mqtt')
        self.listen_event(self.handle_cancel_timer, 'MQTT_MESSAGE',
                          topic='hermes/intent/' + self.args['intents']['cancel'],
                          namespace='mqtt')
        self.log("Countdown Timer Skill started", level='INFO')

    def handle_set_timer(self, event, data, kwargs):
        message = json.loads(data['payload'])
        self.log("Message=%r", message, level='DEBUG')
        self.session_id = message['sessionId']
        self._handle_set_timer(message)

    def handle_set_timer_duration(self, event, data, kwargs):
        message = json.loads(data['payload'])
        self.log("Message=%r", message, level='DEBUG')
        if self.session_id and self.session_id == message['sessionId']:
            self._handle_set_timer(message)
        else:
            self.log("Not our session, discarding", message, level='DEBUG')

    def _handle_set_timer(self, message):
        slots = util.convert_slots(message['slots'])
        self.log("Slots=%r", slots, level='DEBUG')
        if 'duration' in slots:
            duration, text = util.normalize_duration(slots['duration'])
            self.log('Duration=%r', duration, level='DEBUG')
            self.start_countdown(duration)
            self.call_service('assistant/speak',
                              template=self.tts_templates['set_ok'],
                              variables={
                                  'duration_raw': text
                              },
                              namespace='assistant')
        else:
            self.log('No duration, continuing dialogue', level='DEBUG')
            self.call_service('assistant/speak',
                              template=self.tts_templates['set_noduration'],
                              continue_session='slot_duration',
                              namespace='assistant')

    # noinspection PyUnresolvedReferences
    def handle_get_timer(self, event, data, kwargs):
        self.log("Event=%r, data=%r", event, data, level='DEBUG')
        timer_state = self.get_state(self.timer_entity, 'all', namespace='hass')
        if timer_state['state'] == 'active':
            self.call_service('assistant/speak',
                              template=self.tts_templates['get_ok'],
                              variables={'remaining': timer_state['attributes']['remaining']},
                              namespace='assistant')
        else:
            self.call_service('assistant/speak',
                              template=self.tts_templates['get_notimer'],
                              namespace='assistant')

    def handle_cancel_timer(self, event, data, kwargs):
        self.log("Event=%r, data=%r", event, data, level='DEBUG')
        timer_state = self.get_state(self.timer_entity, namespace='hass')
        if timer_state == 'active':
            self.call_service('timer/cancel', entity_id=self.timer_entity, namespace='hass')
            self.call_service('assistant/speak',
                              template=self.tts_templates['cancel_ok'],
                              namespace='assistant')
        else:
            self.call_service('assistant/speak',
                              template=self.tts_templates['cancel_notimer'],
                              namespace='assistant')

    def start_countdown(self, duration: timedelta):
        self.log("Starting timer: %r", duration, level='DEBUG')
        self.call_service('timer/cancel', entity_id=self.timer_entity, namespace='hass')
        self.call_service('timer/start', entity_id=self.timer_entity, duration=duration.seconds, namespace='hass')
