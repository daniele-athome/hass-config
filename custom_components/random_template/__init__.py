"""A service for rendering a random template from files in a directory."""
import logging
import os
import random
import glob

import voluptuous as vol

from homeassistant.core import ServiceCall, ServiceResponse, SupportsResponse, HomeAssistant
from homeassistant.helpers import template
from homeassistant.helpers import config_validation as cv

DOMAIN = "random_template"
CONF_TEMPLATES_PATH = "templates_path"
CONF_LANGUAGE = "language"

SERVICE_RENDER = "render"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TEMPLATES_PATH): str,
                vol.Required(CONF_LANGUAGE): str,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_RENDER_SCHEMA = vol.Schema({
    vol.Required("key"): str,
    vol.Optional("variables", default=dict): dict,
})


async def async_setup(hass: HomeAssistant, config):

    async def handle_render(call: ServiceCall) -> ServiceResponse:
        _LOGGER.debug("Service call: %s", call)

        tmpl_name = call.data.get('key')
        tmpl_variables = call.data.get('variables')

        templates_path = config[DOMAIN].get(CONF_TEMPLATES_PATH)
        language = config[DOMAIN].get(CONF_LANGUAGE)

        tmpl_dir = template_dirname(templates_path, language, tmpl_name)
        if os.path.isdir(tmpl_dir):
            tmpl_file = await hass.async_add_executor_job(
                select_template, tmpl_dir
            )
        else:
            tmpl_file = template_filename(templates_path, language, tmpl_name)

        return {
            'text': await render_template_file(hass, tmpl_file, tmpl_variables)
        }

    hass.services.async_register(DOMAIN, SERVICE_RENDER, handle_render,
                                 schema=SERVICE_RENDER_SCHEMA,
                                 supports_response=SupportsResponse.ONLY)

    return True


def select_template(tmpl_dir):
    return random.choice(glob.glob(os.path.join(tmpl_dir, '*.jinja2')))


def read_template_file(tmpl_file: str) -> str:
    with open(tmpl_file, mode='r', encoding='utf-8') as tmpl_fp:
        return tmpl_fp.read()


async def render_template_file(hass: HomeAssistant, tmpl_file, variables):
    tmpl_content = await hass.async_add_executor_job(read_template_file, tmpl_file)
    _LOGGER.debug('Rendering template text: %r', tmpl_content)
    tpl = template.Template(tmpl_content, hass)
    return tpl.async_render(variables=variables, parse_result=False)


def template_dirname(templates_path, language, name):
    return os.path.join(templates_path, language, name)


def template_filename(templates_path, language, name):
    return os.path.join(templates_path, language, name + '.jinja2')
