from dataclasses import dataclass

import appdaemon.adapi as adapi
import appdaemon.adbase as adbase
import appdaemon.plugins.mqtt.mqttapi as mqtt

import json

#
# App implementing the Hermes protocol for the Dialogue Manager part.
#
# Mainly used to keep track of the current session. Also useful as an utility module.


# noinspection PyAttributeOutsideInit
class HermesDialogue(mqtt.Mqtt):

    # TODO handle multiple sessions (for satellites)

    def initialize(self):
        self.sessions = {}
        self.cancel_template = self.args['cancel_template']
        self.listen_event(self.session_started, 'MQTT_MESSAGE',
                          topic='hermes/dialogueManager/sessionStarted',
                          namespace='mqtt')
        self.listen_event(self.session_ended, 'MQTT_MESSAGE',
                          topic='hermes/dialogueManager/sessionEnded',
                          namespace='mqtt')
        self.listen_event(self.cancel_intent, 'MQTT_MESSAGE',
                          topic='hermes/intent/' + self.args['cancel_intent'],
                          namespace='mqtt')
        self.register_service('dialogue/continue', self.continue_session, namespace='hermes')
        self.register_service('dialogue/end', self.end_session, namespace='hermes')
        self.log("Hermes Dialogue support started", level='INFO')

    def register_session(self, session_id: str, app: adbase.ADBase, custom_data: {} = None):
        """Associate a session with the given app."""
        self.log("Registering app %s as owner for session %s", app.name, session_id)
        self.sessions[session_id].owner_app = app.name
        self.sessions[session_id].custom_data = custom_data or {}

    def session_started(self, event, data, kwargs):
        message = json.loads(data['payload'])
        session_id = message['sessionId']
        self.sessions[session_id] = DialogueSession(session_id)

    def session_ended(self, event, data, kwargs):
        message = json.loads(data['payload'])
        session_id = message['sessionId']
        try:
            del self.sessions[session_id]
        except KeyError:
            pass

    def cancel_intent(self, event, data, kwargs):
        tmpl_text = self.call_service('assistant/template',
                                      template=self.cancel_template,
                                      namespace='assistant')
        message = json.loads(data['payload'])
        session_id = message['sessionId']
        if session_id in self.sessions and self.sessions[session_id].owner_app is None:
            if not self.call_service('dialogue/end', session_id=session_id, text=tmpl_text, namespace='hermes'):
                # no session active, use low-level TTS
                message = {'text': tmpl_text}
                self.call_service('mqtt/publish',
                                  topic='hermes/tts/say',
                                  payload=json.dumps(message),
                                  namespace='mqtt')
        else:
            self.log("Session currently owned by another app, not handling cancel intent", level='DEBUG')

    def continue_session(self, namespace, domain, service, data):
        session_id = data['session_id']
        if session_id not in self.sessions:
            return False

        message = {
            'sessionId': session_id,
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
        session_id = data['session_id']
        if session_id not in self.sessions:
            return False

        message = {
            'sessionId': session_id,
        }
        if 'text' in data and data['text']:
            message['text'] = data['text']
        if 'custom_data' in data and data['custom_data']:
            message['customData'] = data['custom_data']

        self.mqtt_publish('hermes/dialogueManager/endSession', json.dumps(message), namespace='mqtt')
        return True


# noinspection PyAttributeOutsideInit
class DialogueSupport(adapi.ADAPI):
    """
    Support abstract class for apps using the HermesDialogue app.
    Mainly used to simplify calls to the services exposed by HermesDialogue.
    """

    def initialize(self):
        # noinspection PyTypeChecker
        self.app_dialogue: HermesDialogue = self.get_app('app_hermes_dialogue')

    def session_start(self, session_id: str, custom_data: {} = None):
        # noinspection PyTypeChecker
        self.app_dialogue.register_session(session_id, self, custom_data)

    def get_session_data(self, session_id: str) -> {}:
        if self.is_session_owner(session_id):
            return self.app_dialogue.sessions[session_id].custom_data
        return None

    def is_session_owner(self, session_id: str) -> bool:
        try:
            session = self.app_dialogue.sessions[session_id]
            return session.owner_app == self.name
        except KeyError:
            pass
        return False

    def continue_session(self, session_id: str, text: str, intent_filter=None, custom_data=None):
        message = {
            'namespace': 'hermes',
            'session_id': session_id,
            'text': text,
        }
        if intent_filter:
            message['intent_filter'] = intent_filter
        if custom_data:
            message['custom_data'] = custom_data

        self.call_service('dialogue/continue', **message)

    def end_session(self, session_id: str, text: str, custom_data=None):
        message = {
            'namespace': 'hermes',
            'session_id': session_id,
            'text': text,
        }
        if custom_data:
            message['custom_data'] = custom_data

        if not self.call_service('dialogue/end', **message):
            # no session active, use low-level TTS
            message = {'text': text}
            self.call_service('mqtt/publish',
                              topic='hermes/tts/say',
                              payload=json.dumps(message),
                              namespace='mqtt')


@dataclass
class DialogueSession:

    session_id: str
    owner_app: str = None
    custom_data: {} = None


