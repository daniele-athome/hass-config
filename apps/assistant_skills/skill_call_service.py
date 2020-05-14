
import appdaemon.plugins.hass.hassapi as hass

import json
import util
import hermes_dialogue

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

        self.listen_event(self.handle_confirm, 'MQTT_MESSAGE',
                          topic='hermes/intent/' + self.confirm_intent,
                          namespace='mqtt')
        self.listen_event(self.handle_cancel, 'MQTT_MESSAGE',
                          topic='hermes/intent/' + self.cancel_intent,
                          namespace='mqtt')

        for intent_name, intent_config in self.intents.items():
            self.listen_event(self.handle_intent, 'MQTT_MESSAGE',
                              topic='hermes/intent/' + intent_name,
                              namespace='mqtt')

    def handle_intent(self, event, data, kwargs):
        intent_name = data['topic'][len('hermes/intent/'):]
        intent_config = self.intents[intent_name]
        service_name = intent_config['service']
        service_space = intent_config['namespace']

        message = json.loads(data['payload'])
        if intent_config.get('confirm', False):
            self.session_start(message['sessionId'], {'intent_name': intent_name})
            self.continue_session(session_id=message['sessionId'],
                                  text=util.render_template(self, intent_config['confirm_template']),
                                  intent_filter=[self.confirm_intent, self.cancel_intent])
        else:
            self.execute_intent(message['sessionId'], service_name, intent_config['arguments'],
                                intent_config.get('ok_template'), namespace=service_space)

    def handle_confirm(self, event, data, kwargs):
        message = json.loads(data['payload'])
        session_id = message['sessionId']
        session_data = self.get_session_data(session_id)
        if session_data:
            intent_config = self.intents[session_data['intent_name']]
            self.execute_intent(session_id,
                                intent_config['service'],
                                intent_config['arguments'],
                                intent_config.get('ok_template'),
                                namespace=intent_config['namespace'])
        else:
            self.log("Not our session, discarding", message, level='DEBUG')

    def handle_cancel(self, event, data, kwargs):
        message = json.loads(data['payload'])
        session_id = message['sessionId']
        session_data = self.get_session_data(session_id)
        if session_data:
            intent_config = self.intents[session_data['intent_name']]
            ok_template_name = intent_config.get('ok_template')
            self.end_session(session_id=session_id,
                             text=util.render_template(self, ok_template_name) if ok_template_name else "")
        else:
            self.log("Not our session, discarding", message, level='DEBUG')

    def execute_intent(self, session_id, name, kwargs, ok_template=None, namespace=None):
        kwargs['namespace'] = namespace
        self.call_service(name, **kwargs)
        self.end_session(session_id=session_id,
                         text=util.render_template(self, ok_template) if ok_template else "")
