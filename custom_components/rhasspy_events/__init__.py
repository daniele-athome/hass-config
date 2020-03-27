"""Translate Rhasspy events to HASS intents."""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.core import Event
from homeassistant.helpers import intent

DOMAIN = "rhasspy_events"
CONF_EVENTS = "events"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_EVENTS): [str],
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


# TODO info logs should be debug logs
async def async_setup(hass, config):
    """Activate Rhasspy events component."""

    async def handle_event(event: Event):
        _LOGGER.info("New event: %s", event)

        intent_type = event.event_type.split("_")[-1]
        entities = {}
        for entity_name, entity_value in event.data.items():
            if entity_name.startswith('_'):
                continue

            value, text = resolve_entity_values(entity_value)
            if value is None:
                _LOGGER.warning("Unhandled entity: %s", entity_value)
            entities[entity_name] = {'value': value}
            entities['{}_raw'.format(entity_name)] = {'value': text}

        _LOGGER.info("Slots: %s", entities)
        try:
            await intent.async_handle(
                hass, DOMAIN, intent_type, entities, event.data['_text']
            )
        except intent.UnknownIntent:
            _LOGGER.warning(
                "Received unknown intent %s", event.event_type
            )
        except intent.IntentError:
            _LOGGER.exception("Error while handling intent: %s.", intent_type)

    for event_name in config[DOMAIN].get(CONF_EVENTS):
        hass.bus.async_listen('rhasspy_' + event_name, handle_event)

    return True


def resolve_entity_values(entity: []):
    """Convert entities to usable values."""
    _LOGGER.info("Entity: %s", entity)

    # FIXME content could change depending on my modifications to Rhasspy
    # also this is probably too tied to Rasa NLU
    resolved = None, ""

    for extracted in entity:
        _LOGGER.info("Extraction: %s", extracted)

    match_duckling = [extracted for extracted in entity if extracted['extractor'] == 'DucklingHTTPExtractor']
    if len(match_duckling) > 0:
        match_duration = [extracted for extracted in match_duckling if extracted['entity'] == 'duration']
        if len(match_duration) > 0:
            text_parts = []
            delta_parts = {
                'week': 0,
                'day': 0,
                'hour': 0,
                'minute': 0,
                'second': 0,
            }

            for unit in ['week', 'day', 'hour', 'minute', 'second']:
                for duration in match_duration:
                    if duration['additional_info']['unit'] == unit:
                        delta_parts[unit] = duration['additional_info'][unit]
                        text_parts.append(duration['text'])

            resolved = timedelta(
                weeks=delta_parts['week'],
                days=delta_parts['day'],
                hours=delta_parts['hour'],
                minutes=delta_parts['minute'],
                seconds=delta_parts['second'],
            ).seconds, ', '.join(text_parts)

        # TODO handle other duckling entities
        else:
            for extracted in match_duckling:
                if extracted['entity'] == 'number':
                    resolved = extracted['value'], extracted['text']
                    break

    if resolved[0] is None:
        # fallback to simple entity extractor
        match_simple = [extracted for extracted in entity if extracted['extractor'] == 'CRFEntityExtractor']
        if len(match_simple) > 0:
            resolved = match_simple[0]['value'], match_simple[0]['value']

    return resolved
