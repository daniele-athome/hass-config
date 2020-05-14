
import appdaemon.plugins.hass.hassapi as hass

import json

#
# App used by the smart assistant for speaking.
#
# The main purpose of this is to randomly select a template from a list of templates of a given type
# to introduce some "randomness" in assistant speaking.
#


# noinspection PyAttributeOutsideInit
# @deprecated
class AssistantSpeak(hass.Hass):

    def initialize(self):
        self.listen_event(self.tts_event, 'assistant_speak_tts', namespace='hass')
        self.register_service('assistant/speak', self.tts_speak, namespace='assistant')
        self.log("Assistant Speak support started", level='INFO')

    def tts_event(self, event, data, kwargs):
        if 'template' in data:
            data['template'] = 'assistant_' + data['template']
        self.tts_speak('assistant', 'assistant', 'speak', data)

    def tts_speak(self, namespace, domain, service, data):
        self.log("Service: %r", data, level='DEBUG')
        tmpl_name = data['template']
        session_continue = data.get('continue_session')
        tmpl_variables = data.get('variables', {})
        custom_data = data.get('custom_data')

        if tmpl_name is not None:
            tmpl_text = self.call_service('assistant/template',
                                          template=tmpl_name,
                                          variables=tmpl_variables,
                                          namespace='assistant')
        else:
            tmpl_text = None
        self.speak_template(tmpl_text, tmpl_variables, session_continue, custom_data)

    def speak_template(self, tmpl_text, variables, intent_filter=None, custom_data=None):
        self.log('Speaking template text: %r', tmpl_text)
        if intent_filter and intent_filter != 'NONE':
            self.call_service('dialogue/continue',
                              text=tmpl_text,
                              intent_filter=intent_filter,
                              custom_data=custom_data,
                              namespace='hermes')
        else:
            if not self.call_service('dialogue/end',
                                     text=tmpl_text,
                                     custom_data=custom_data,
                                     namespace='hermes'):
                # no session active, use low-level TTS
                message = {'text': tmpl_text}
                self.call_service('mqtt/publish',
                                  topic='hermes/tts/say',
                                  payload=json.dumps(message),
                                  namespace='mqtt')
