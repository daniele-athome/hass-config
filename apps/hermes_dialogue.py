import importer

from dataclasses import dataclass

import appdaemon.adapi as adapi
import appdaemon.adbase as adbase

import json

import hermes.constants as hermes_constants
import hermes.hermesapi as hermes

from rhasspyhermes.nlu import NluIntent

#
# App implementing the Hermes protocol for the Dialogue Manager part.
#
# Mainly used to keep track of the current session. Also useful as an utility module.


# noinspection PyAttributeOutsideInit
class HermesDialogue(hermes.Hermes):

    # TODO handle multiple sessions (for sites)

    def initialize(self):
        self.add_namespace('hermes')
        self.sessions = {}
        self.cancel_template = self.args['cancel_template']

        self.events = [
            self.listen_event(self.session_started,
                              hermes_constants.DIALOGUE_SESSION_STARTED_EVENT,
                              namespace='hermes'),
            self.listen_event(self.session_ended,
                              hermes_constants.DIALOGUE_SESSION_ENDED_EVENT,
                              namespace='hermes'),
            self.listen_event(self.cancel_intent,
                              hermes_constants.INTENT_EVENT,
                              intent=self.args['cancel_intent'],
                              namespace='hermes'),
        ]
        # TODO these services should be in HermesPlugin
        self.register_service('dialogue/continue', self.service_continue_session, namespace='hermes')
        self.register_service('dialogue/end', self.service_end_session, namespace='hermes')
        self.log("Hermes Dialogue support started", level='INFO')

    def terminate(self):
        for e in self.events:
            self.cancel_listen_event(e)

    def register_session(self, session_id: str, app: adbase.ADBase):
        """Associate a session with the given app."""
        self.log("Registering app %s as owner for session %s", app.name, session_id)
        self.sessions[session_id].owner_app = app.name

    def session_started(self, event, data: dict, kwargs):
        session_id = data['session_id']
        self.sessions[session_id] = DialogueSession(session_id)

    def session_ended(self, event, data: dict, kwargs):
        session_id = data['session_id']
        try:
            del self.sessions[session_id]
        except KeyError:
            pass

    def cancel_intent(self, event, data: dict, kwargs):
        intent_data: NluIntent = data['message']
        session_id = intent_data.session_id
        try:
            custom_data = json.loads(intent_data.custom_data)
            handle_cancel = custom_data.get('handleCancel', False)
        except:
            handle_cancel = False

        if not handle_cancel or (session_id in self.sessions and self.sessions[session_id].owner_app is None):
            tmpl_text = self.call_service('assistant/template',
                                          template=self.cancel_template,
                                          namespace='assistant')
            if not self.call_service('dialogue/end', session_id=session_id, text=tmpl_text, namespace='hermes'):
                # no session active, use low-level TTS
                self.tts_say(tmpl_text)
        else:
            self.log("Session currently owned by another app, not handling cancel intent", level='DEBUG')

    def service_continue_session(self, namespace, domain, service, data):
        session_id = data['session_id']
        if session_id not in self.sessions:
            return False

        if 'intent_filter' in data and data['intent_filter']:
            intent_filter = data['intent_filter'] if not isinstance(data['intent_filter'], str) else [data['intent_filter']]
        else:
            intent_filter = None
        custom_data = data['custom_data'] if 'custom_data' in data else None

        return self.continue_session(session_id, data['text'], intent_filter, custom_data, namespace='hermes')

    def service_end_session(self, namespace, domain, service, data):
        session_id = data['session_id']
        if session_id not in self.sessions:
            return False

        text = data['text'] if 'text' in data else None

        return self.end_session(session_id, text, namespace='hermes')


# noinspection PyAttributeOutsideInit
class DialogueSupport(adapi.ADAPI):
    """
    Support abstract class for apps using the HermesDialogue app.
    Mainly used to simplify calls to the services exposed by HermesDialogue.
    """

    def initialize(self):
        # noinspection PyTypeChecker
        self.app_dialogue: HermesDialogue = self.get_app('app_hermes_dialogue')

    def session_start(self, session_id: str):
        # noinspection PyTypeChecker
        self.app_dialogue.register_session(session_id, self)

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
