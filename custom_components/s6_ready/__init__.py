import logging
import os

import homeassistant.helpers.config_validation as cv
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant, callback

DOMAIN = "s6_ready"
FD = 3
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    @callback
    def _notify(_event: Event) -> None:
        try:
            os.write(FD, b"\n")
            os.close(FD)
        except OSError as err:
            _LOGGER.warning("s6 readiness notification failed: %s", err)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _notify)
    return True
