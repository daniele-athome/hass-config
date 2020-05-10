
from datetime import timedelta


def convert_slots(slots: []) -> {}:
    """Convert slots to usable values. Pretty tied to Rasa NLU slots format."""
    resolved = {}

    for slot in slots:
        slot_name = slot['entity']
        slot_value = slot['value']
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
            resolved[slot_name + '_raw'] = slot['rawValue']

        resolved[slot_name][slot_extractor].append(slot_value)

    return resolved


def normalize_duration(slot: {}) -> (timedelta, str):
    if 'DucklingHTTPExtractor' not in slot:
        raise ValueError('Not a duration slot')

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
