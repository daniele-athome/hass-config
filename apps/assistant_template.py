
import appdaemon.plugins.hass.hassapi as hass

import os
import glob
import random

#
# A helper app providing random template selection and rendering.
#
# This app could be used by Smart Assistants to provide some "randomness" in the assistant words.
#


# noinspection PyAttributeOutsideInit
class AssistantTemplate(hass.Hass):

    def initialize(self):
        self.add_namespace('assistant')
        self.register_service('assistant/template', self.template_service, namespace='assistant')
        self.language = self.args['language']
        self.templates_path = self.args['templates_path']
        self.log("Assistant Template support started for language %s", self.language, level='INFO')

    def template_service(self, namespace, domain, service, data):
        self.log("Service: %r", data, level='DEBUG')
        tmpl_name = data['template']
        tmpl_variables = data.get('variables')

        tmpl_dir = self.template_dirname(tmpl_name)
        if os.path.isdir(tmpl_dir):
            tmpl_file = self.select_template(tmpl_dir)
        else:
            tmpl_file = self.template_filename(tmpl_name)

        return self.render_template_file(tmpl_file, tmpl_variables)

    # noinspection PyMethodMayBeStatic
    def select_template(self, tmpl_dir):
        return random.choice(glob.glob(os.path.join(tmpl_dir, '*.jinja2')))

    def render_template_file(self, tmpl_file, variables):
        with open(tmpl_file, mode='r', encoding='utf-8') as tmpl_fp:
            tmpl_content = tmpl_fp.read()

            self.log('Rendering template text: %r', tmpl_content)
            return self.call_service('template/render',
                                     template=tmpl_content,
                                     variables=variables,
                                     namespace='hass')

    def template_dirname(self, name):
        return os.path.join(self.templates_path, self.language, name)

    def template_filename(self, name):
        return os.path.join(self.templates_path, self.language, name + '.jinja2')
