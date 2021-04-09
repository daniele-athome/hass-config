"""Starts playing music playlists."""
import logging

import voluptuous as vol

from homeassistant.core import Event, HomeAssistant

DOMAIN = "rhasspy_playlists"
CONF_SLOT_FILE = "slot_file"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SLOT_FILE): str,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


# TODO info logs should be debug logs
async def async_setup(hass: HomeAssistant, config):
    """Activate Rhasspy playlists component."""

    async def handle_event(event: Event):
        _LOGGER.info("New event: %s", event)

        playlist_name = event.data['playlist']
        playlist_id = None
        for slot in slot_data:
            if playlist_name.lower() in slot.lower():
                _, playlist_id = slot.split(':', 1)
                break

        if playlist_id:
            _LOGGER.info("Playlist id: %s", playlist_id)
            try:
                await hass.services.async_call('script', 'start_playlist', {'playlist': playlist_id})
            except Exception as e:
                _LOGGER.exception("Error starting script service", exc_info=e)

    with open(config[DOMAIN].get(CONF_SLOT_FILE), mode='r', encoding='utf-8') as file:
        slot_data = [line.rstrip("\n") for line in file]
    hass.bus.async_listen('rhasspy_playlist', handle_event)
    return True
