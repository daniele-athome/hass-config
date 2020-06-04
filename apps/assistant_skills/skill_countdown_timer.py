import importer

import appdaemon.plugins.hass.hassapi as hass

from datetime import timedelta

import util
import hermes_dialogue

import hermes.constants as hermes_constants

from rhasspyhermes.nlu import NluIntent

#
# Skill for a simple countdown timer.
#


# noinspection PyAttributeOutsideInit
class CountdownTimerSkill(hass.Hass, hermes_dialogue.DialogueSupport):

    def initialize(self):
        hermes_dialogue.DialogueSupport.initialize(self)
        self.timer_entity = self.args['timer_entity']
        self.tts_templates = self.args['templates']
        self.cancel_intent = self.args['cancel_intent']

        self.events = [
            self.listen_event(self.handle_set_timer, hermes_constants.INTENT_EVENT,
                              intent=self.args['intents']['set'],
                              namespace='hermes'),
            self.listen_event(self.handle_set_timer_duration, hermes_constants.INTENT_EVENT,
                              intent=self.args['intents']['slot_duration'],
                              namespace='hermes'),
            self.listen_event(self.handle_get_timer, hermes_constants.INTENT_EVENT,
                              intent=self.args['intents']['get'],
                              namespace='hermes'),
            self.listen_event(self.handle_cancel_timer, hermes_constants.INTENT_EVENT,
                              intent=self.args['intents']['cancel'],
                              namespace='hermes'),
        ]

        self.log("Countdown Timer Skill started", level='INFO')

    def terminate(self):
        for e in self.events:
            self.cancel_listen_event(e)

    def handle_set_timer(self, event, data: dict, kwargs):
        self.log("Message=%r", data, level='DEBUG')

        self.session_start(data['message'].session_id)
        self._handle_set_timer(data['message'])

    def handle_set_timer_duration(self, event, data: dict, kwargs):
        self.log("Message=%r", data, level='DEBUG')

        if self.is_session_owner(data['message'].session_id):
            self._handle_set_timer(data['message'])
        else:
            self.log("Not our session, discarding", level='DEBUG')

    def _handle_set_timer(self, message: NluIntent):
        slots = util.convert_slots(message.slots)
        self.log("Slots=%r", slots, level='DEBUG')

        if 'duration' in slots:
            duration, text = util.normalize_duration(slots['duration'])
            if text is None:
                text = slots['duration_raw']

            self.log('Duration=%r', duration, level='DEBUG')
            self.start_countdown(duration)

            self.end_session(session_id=message.session_id,
                             text=util.render_template(self, self.tts_templates['set_ok'], {'duration_raw': text}))
        else:
            self.log('No duration, continuing dialogue', level='DEBUG')
            self.continue_session(session_id=message.session_id,
                                  text=util.render_template(self, self.tts_templates['set_noduration']),
                                  intent_filter=[self.args['intents']['slot_duration'], self.cancel_intent])

    # noinspection PyUnresolvedReferences
    def handle_get_timer(self, event, data: dict, kwargs):
        message = data['message']
        self.log("Message=%r", message, level='DEBUG')

        timer_state = self.get_state(self.timer_entity, 'all', namespace='hass')
        if timer_state['state'] == 'active':
            # workaround to update current remaining time
            self.call_service('timer/pause', entity_id=self.timer_entity, namespace='hass')
            self.call_service('timer/start', entity_id=self.timer_entity, namespace='hass')
            timer_state = self.get_state(self.timer_entity, 'all', namespace='hass')

            self.end_session(session_id=message.session_id,
                             text=util.render_template(self, self.tts_templates['get_ok'],
                                                       {'remaining': timer_state['attributes']['remaining']}))
        else:
            self.end_session(session_id=message.session_id,
                             text=util.render_template(self, self.tts_templates['get_notimer']))

    def handle_cancel_timer(self, event, data: dict, kwargs):
        message = data['message']
        self.log("Message=%r", message, level='DEBUG')

        timer_state = self.get_state(self.timer_entity, namespace='hass')
        if timer_state == 'active':
            self.call_service('timer/cancel', entity_id=self.timer_entity, namespace='hass')
            self.end_session(session_id=message.session_id,
                             text=util.render_template(self, self.tts_templates['cancel_ok']))
        else:
            self.end_session(session_id=message.session_id,
                             text=util.render_template(self, self.tts_templates['cancel_notimer']))

    def start_countdown(self, duration: timedelta):
        self.log("Starting timer: %r", duration, level='DEBUG')
        self.call_service('timer/cancel', entity_id=self.timer_entity, namespace='hass')
        self.call_service('timer/start', entity_id=self.timer_entity, duration=duration.seconds, namespace='hass')
