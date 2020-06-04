import importer

import hermes.constants as hermes_constants
import hermes.hermesapi as hermes

from rhasspyhermes.tts import TtsSay


#
# App implementing the Hermes protocol for the TTS part.
#
# Use the speak_device argument to define the entity ID of the media player for speaking


# noinspection PyAttributeOutsideInit
class HermesTTS(hermes.Hermes):

    # noinspection PyTypeChecker
    def initialize(self):
        self.tts_id = None

        self.mqtt_tts_say_event = self.listen_event(self.tts_say_event,
                                                    hermes_constants.TTS_SAY_EVENT,
                                                    namespace='hermes')
        self.hass_media_finished_event = self.listen_state(self.media_finished, self.args['speak_device'],
                                                           namespace='hass', old='playing', new='idle')
        self.log("Hermes TTS support started", level='INFO')

    def terminate(self):
        self.cancel_listen_event(self.mqtt_tts_say_event)
        self.cancel_listen_state(self.hass_media_finished_event)

    def tts_say_event(self, event, data: dict, kwargs):
        message: TtsSay = data['message']
        self.tts_id = message.id
        self.call_service('script/say_something', message=message.text, namespace='hass')

    # TODO handle multiple sessions (for sites)
    def media_finished(self, entity, attribute, old, new, kwargs):
        self.log('Media finished: entity=%s, attribute=%s, old=%s, new=%s', entity, attribute, old, new, level='DEBUG')
        # TODO session id doesn't make sense here because the device we speak through is only one
        # if self.hermes_dialogue.session_id: ...
        self.tts_say_finished(self.tts_id, namespace='hermes')
