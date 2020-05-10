
import appdaemon.plugins.hass.hassapi as hass

import os
import glob
import random
import json

#
# App used by the smart assistant for speaking.
#
# The main purpose of this is to randomly select a template from a list of templates of a given type
# to introduce some "randomness" in assistant speaking.
#


# noinspection PyAttributeOutsideInit
class AssistantSpeak(hass.Hass):

    def initialize(self):
        self.listen_event(self.tts_event, 'assistant_speak_tts', namespace='hass')
        self.register_service('assistant/speak', self.tts_speak, namespace='assistant')
        self.language = self.args['language']
        self.templates_path = self.args['templates_path']
        self.log("Assistant Speak support started for language %s", self.language, level='INFO')

    def tts_speak(self, namespace, domain, service, data):
        self.tts_event('assistant_speak_tts', data, None)

    def tts_event(self, event, data, kwargs):
        self.log("Event: %r", event, level='DEBUG')
        tmpl_name = data['template']
        if 'continue_session' in data:
            session_continue = data['continue_session']
        else:
            session_continue = None
        if 'variables' in data:
            tmpl_variables = data['variables']
        else:
            tmpl_variables = {}

        tmpl_dir = self.template_dirname(tmpl_name)
        if os.path.isdir(tmpl_dir):
            self.speak_template_file(self.select_template(tmpl_dir), tmpl_variables, session_continue)
        else:
            self.speak_template_file(self.template_filename(tmpl_name), tmpl_variables, session_continue)

    # noinspection PyMethodMayBeStatic
    def select_template(self, tmpl_dir):
        return random.choice(glob.glob(os.path.join(tmpl_dir, '*.jinja2')))

    def speak_template_file(self, tmpl_file, variables, intent_filter=None):
        with open(tmpl_file, mode='r', encoding='utf-8') as tmpl_fp:
            tmpl_content = tmpl_fp.read()

            self.log('Rendering template text: %r', tmpl_content)
            tmpl_text = self.call_service('template/render',
                                          template=tmpl_content,
                                          variables=variables,
                                          namespace='hass')

            self.log('Speaking template text: %r', tmpl_text)
            if intent_filter and intent_filter != 'NONE':
                self.call_service('dialogue/continue', text=tmpl_text, intent_filter=intent_filter, namespace='hermes')
            else:
                if not self.call_service('dialogue/end', text=tmpl_text, namespace='hermes'):
                    # no session active, use low-level TTS
                    message = {'text': tmpl_text}
                    self.call_service('mqtt/publish',
                                      topic='hermes/tts/say',
                                      payload=json.dumps(message),
                                      namespace='mqtt')

    def template_dirname(self, name):
        return os.path.join(self.templates_path, self.language, 'assistant_' + name)

    def template_filename(self, name):
        return os.path.join(self.templates_path, self.language, 'assistant_' + name + '.jinja2')
