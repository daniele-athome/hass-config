import importer

import hermes.constants as hermes_constants
import hermes.hermesapi as hermes

from rhasspyhermes.dialogue import DialogueSessionStarted, DialogueSessionEnded

#
# App used by the smart assistant for speaking.
#
# The main purpose of this is to randomly select a template from a list of templates of a given type
# to introduce some "randomness" in assistant speaking.
#


# noinspection PyAttributeOutsideInit
class AssistantSpeak(hermes.Hermes):

    def initialize(self):
        self.session_id = None
        self.add_namespace('assistant')
        self.events = [
            self.listen_event(self.tts_event,
                              'assistant_speak_tts',
                              namespace='hass'),
            self.listen_event(self.session_started,
                              hermes_constants.DIALOGUE_SESSION_STARTED_EVENT,
                              namespace='hermes'),
            self.listen_event(self.session_ended,
                              hermes_constants.DIALOGUE_SESSION_ENDED_EVENT,
                              namespace='hermes'),
        ]
        self.register_service('assistant/speak', self.tts_speak, namespace='assistant')
        self.log("Assistant Speak support started", level='INFO')

    def terminate(self):
        for e in self.events:
            self.cancel_listen_event(e)

    def session_started(self, event, data: dict, kwargs):
        self.session_id = data['session_id']
        self.log("Starting assistant speak session", level='INFO')

    def session_ended(self, event, data: dict, kwargs):
        if data['session_id'] == self.session_id:
            self.log("Ending assistant speak session", level='INFO')
            self.session_id = None

    def tts_event(self, event, data, kwargs):
        if 'template' in data:
            data['template'] = 'assistant_' + data['template']
        self.tts_speak('assistant', 'assistant', 'speak', data)

    def tts_speak(self, namespace, domain, service, data):
        self.log("Service: %r", data, level='DEBUG')
        tmpl_name = data['template']
        tmpl_variables = data.get('variables', {})
        custom_data = data.get('custom_data')

        if tmpl_name is not None:
            tmpl_text = self.call_service('assistant/template',
                                          template=tmpl_name,
                                          variables=tmpl_variables,
                                          namespace='assistant')
        else:
            tmpl_text = None
        self.speak_template(tmpl_text, tmpl_variables, custom_data)

    def speak_template(self, tmpl_text, variables, custom_data=None):
        self.log('Speaking template text: %r', tmpl_text)
        if self.session_id:
            return self.end_session(self.session_id, text=tmpl_text, namespace='hermes')
        else:
            # no session active, use low-level TTS
            return self.tts_say(tmpl_text, namespace='hermes')
