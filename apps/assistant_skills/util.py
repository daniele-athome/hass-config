
import appdaemon.adapi as adapi

from datetime import timedelta
import typing
from rhasspyhermes.intent import Slot


def convert_slots(slots: typing.List[Slot]) -> {}:
    """Convert slots to usable values. Can handle Rasa NLU and Snips NLU slots format."""
    resolved = {}

    for slot in slots:
        slot_name = slot.slot_name
        slot_value = slot.value

        slot_entity = slot.entity
        if slot_entity.startswith('snips/'):
            resolved[slot_name] = slot.value
            resolved[slot_name + '_raw'] = slot.raw_value
        else:
            # assuming Rasa NLU slot
            slot_extractor = slot_value['extractor']
            if not slot_extractor:
                slot_extractor = 'Unknown'
            else:
                del slot_value['extractor']

            if slot_name not in resolved:
                resolved[slot_name] = {}
            if slot_extractor not in resolved[slot_name]:
                resolved[slot_name][slot_extractor] = []

            # take the text entity extractor as the raw value
            if slot_extractor == 'CRFEntityExtractor':
                resolved[slot_name + '_raw'] = slot.raw_value

            resolved[slot_name][slot_extractor].append(slot_value)

    return resolved


def normalize_duration(slot: {}) -> (timedelta, str):
    if 'kind' in slot and slot['kind'] == 'Duration':
        delta_parts = {
            'weeks': 0,
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
        }

        for unit in ['weeks', 'days', 'hours', 'minutes', 'seconds']:
            if unit in slot:
                delta_parts[unit] = slot[unit]

        return timedelta(
            weeks=delta_parts['weeks'],
            days=delta_parts['days'],
            hours=delta_parts['hours'],
            minutes=delta_parts['minutes'],
            seconds=delta_parts['seconds'],
        ), None

    elif 'DucklingHTTPExtractor' in slot:
        text_parts = []
        delta_parts = {
            'week': 0,
            'day': 0,
            'hour': 0,
            'minute': 0,
            'second': 0,
        }

        for unit in ['week', 'day', 'hour', 'minute', 'second']:
            for value in slot['DucklingHTTPExtractor']:
                if value['additional_info']['unit'] == unit:
                    delta_parts[unit] = value['additional_info'][unit]
                    text_parts.append(value['value'])

        return timedelta(
            weeks=delta_parts['week'],
            days=delta_parts['day'],
            hours=delta_parts['hour'],
            minutes=delta_parts['minute'],
            seconds=delta_parts['second'],
        ), ', '.join(text_parts)

    else:
        raise ValueError('Not a duration slot')


def render_template(app: adapi.ADAPI, template: str, variables=None):
    return app.call_service('assistant/template',
                            template=template,
                            variables=variables,
                            namespace='assistant')
