
import appdaemon.plugins.mqtt.mqttapi as mqtt

import json

#
# App implementing the Hermes protocol for the Dialogue Manager part.
#
# Mainly used to keep track of the current session. Also useful as an utility module.


# noinspection PyAttributeOutsideInit
class HermesDialogue(mqtt.Mqtt):

    def initialize(self):
        self.session_id = None
        self.listen_event(self.session_started, 'MQTT_MESSAGE',
                          topic='hermes/dialogueManager/sessionStarted',
                          namespace='mqtt')
        self.listen_event(self.session_ended, 'MQTT_MESSAGE',
                          topic='hermes/dialogueManager/sessionEnded',
                          namespace='mqtt')
        self.register_service('dialogue/continue', self.continue_session, namespace='hermes')
        self.register_service('dialogue/end', self.end_session, namespace='hermes')
        self.log("Hermes Dialogue support started", level='INFO')

    def session_started(self, event, data, kwargs):
        message = json.loads(data['payload'])
        self.session_id = message['sessionId']

    def session_ended(self, event, data, kwargs):
        self.session_id = None

    def continue_session(self, namespace, domain, service, data):
        if not self.session_id:
            return False

        message = {
            'sessionId': self.session_id,
            'text': data['text'],
        }
        if 'intent_filter' in data and data['intent_filter']:
            intent_filter = data['intent_filter']
            message['intentFilter'] = intent_filter if not isinstance(intent_filter, str) else [intent_filter]
        if 'custom_data' in data and data['custom_data']:
            message['customData'] = data['custom_data']

        self.mqtt_publish('hermes/dialogueManager/continueSession', json.dumps(message), namespace='mqtt')
        return True

    def end_session(self, namespace, domain, service, data):
        if not self.session_id:
            return False

        message = {
            'sessionId': self.session_id,
        }
        if 'text' in data and data['text']:
            message['text'] = data['text']
        if 'custom_data' in data and data['custom_data']:
            message['customData'] = data['custom_data']

        self.mqtt_publish('hermes/dialogueManager/endSession', json.dumps(message), namespace='mqtt')
        return True
