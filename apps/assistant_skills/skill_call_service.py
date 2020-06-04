import importer

import appdaemon.plugins.hass.hassapi as hass

import json

import util
import hermes_dialogue

import hermes.constants as hermes_constants

from rhasspyhermes.nlu import NluIntent

#
# Skill for calling any AppDaemon service, optionally asking for confirmation by the user.
#


# noinspection PyAttributeOutsideInit
class CallServiceSkill(hass.Hass, hermes_dialogue.DialogueSupport):

    def initialize(self):
        hermes_dialogue.DialogueSupport.initialize(self)
        self.intents = self.args['intents']
        self.confirm_intent = self.args['confirm_intent']
        self.cancel_intent = self.args['cancel_intent']

        self.events = [
            self.listen_event(self.handle_confirm, hermes_constants.INTENT_EVENT,
                              intent=self.confirm_intent,
                              namespace='hermes'),
            self.listen_event(self.handle_cancel, hermes_constants.INTENT_EVENT,
                              intent=self.cancel_intent,
                              namespace='hermes'),
        ]

        for intent_name, intent_config in self.intents.items():
            self.events.append(self.listen_event(self.handle_intent, hermes_constants.INTENT_EVENT,
                                                 intent=intent_name,
                                                 namespace='hermes'))

    def terminate(self):
        for e in self.events:
            self.cancel_listen_event(e)

    def handle_intent(self, event, data: dict, kwargs):
        intent_data: NluIntent = data['message']
        session_id = intent_data.session_id

        intent_name = data['intent']
        intent_config = self.intents[intent_name]
        service_name = intent_config['service']
        service_space = intent_config['namespace']

        if intent_config.get('confirm', False):
            self.session_start(session_id)
            self.continue_session(session_id=session_id,
                                  text=util.render_template(self, intent_config['confirm_template']),
                                  intent_filter=[self.confirm_intent, self.cancel_intent],
                                  custom_data={'intentName': intent_name, 'handleCancel': True})
        else:
            self.execute_intent(session_id, service_name, intent_config.get('arguments', {}),
                                intent_config.get('ok_template'), namespace=service_space)

    def handle_confirm(self, event, data: dict, kwargs):
        intent_data: NluIntent = data['message']
        session_id = intent_data.session_id
        if self.is_session_owner(session_id):
            try:
                custom_data = json.loads(intent_data.custom_data)
                intent_name = custom_data.get('intentName', None)
            except:
                intent_name = None

            if intent_name:
                intent_config = self.intents[intent_name]
                self.execute_intent(session_id,
                                    intent_config['service'],
                                    intent_config['arguments'],
                                    intent_config.get('ok_template'),
                                    namespace=intent_config['namespace'])
            else:
                self.log("Invalid session, discarding", level='WARNING')
        else:
            self.log("Not our session, discarding", level='DEBUG')

    def handle_cancel(self, event, data: dict, kwargs):
        intent_data: NluIntent = data['message']
        session_id = intent_data.session_id
        if self.is_session_owner(session_id):
            try:
                custom_data = json.loads(intent_data.custom_data)
                intent_name = custom_data.get('intentName', None)
            except:
                intent_name = None

            if intent_name:
                intent_config = self.intents[intent_name]
                cancel_template_name = intent_config.get('cancel_template')
                tts_text = util.render_template(self, cancel_template_name) if cancel_template_name else None
                self.end_session(session_id=session_id, text=tts_text)
            else:
                self.log("Invalid session, discarding", level='WARNING')
        else:
            self.log("Not our session, discarding", level='DEBUG')

    def execute_intent(self, session_id, name, kwargs, ok_template=None, namespace=None):
        kwargs['namespace'] = namespace
        self.call_service(name, **kwargs)
        self.end_session(session_id=session_id,
                         text=util.render_template(self, ok_template) if ok_template else "")
