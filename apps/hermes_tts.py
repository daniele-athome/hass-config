
import appdaemon.plugins.mqtt.mqttapi as mqtt

import json

import hermes_dialogue

#
# App implementing the Hermes protocol for the TTS part.
#
# When receiving a "say" message from MQTT, it will emit an HASS event on a configured topic.
# When receiving a "tts_finished" event, it will publish a "sayFinished" message to MQTT.


# noinspection PyAttributeOutsideInit
class HermesTTS(mqtt.Mqtt):

    # noinspection PyTypeChecker
    def initialize(self):
        self.hermes_dialogue: hermes_dialogue.HermesDialogue = self.get_app('app_hermes_dialogue')
        self.tts_id = None

        self.mqtt_tts_say_event = self.listen_event(self.tts_say_event, 'MQTT_MESSAGE',
                                                    topic='hermes/tts/say',
                                                    namespace='mqtt')
        self.hass_media_finished_event = self.listen_state(self.media_finished, self.args['speak_device'],
                                                           namespace='hass', old='playing', new='idle')
        self.log("Hermes TTS support started", level='INFO')

    def terminate(self):
        self.cancel_listen_event(self.mqtt_tts_say_event)
        self.cancel_listen_state(self.hass_media_finished_event)

    def tts_say_event(self, event, data, kwargs):
        message = json.loads(data['payload'])
        if 'id' in message:
            self.tts_id = message['id']
        else:
            self.tts_id = None
        self.call_service('script/say_something', message=message['text'], namespace='hass')

    def media_finished(self, entity, attribute, old, new, kwargs):
        self.log('Media finished: entity=%s, attribute=%s, old=%s, new=%s', entity, attribute, old, new, level='DEBUG')
        message = {}
        if self.tts_id:
            message['id'] = self.tts_id
        if self.hermes_dialogue.session_id:
            message['sessionId'] = self.hermes_dialogue.session_id
        self.mqtt_publish('hermes/tts/sayFinished', json.dumps(message), namespace='mqtt')
