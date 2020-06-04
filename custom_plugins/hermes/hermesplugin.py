
from appdaemon.appdaemon import AppDaemon
from appdaemon.plugins.mqtt.mqttplugin import MqttPlugin

from rhasspyhermes.tts import TtsSay, TtsSayFinished
from rhasspyhermes.dialogue import DialogueStartSession, DialogueContinueSession, DialogueEndSession
from rhasspyhermes.dialogue import DialogueSessionStarted, DialogueSessionEnded
from rhasspyhermes.nlu import NluIntent

# noinspection PyUnresolvedReferences
import constants


class HermesPlugin(MqttPlugin):

    # Hermes messages we support
    _hermes_messages = [
        TtsSay,
        TtsSayFinished,
        DialogueSessionStarted,
        DialogueSessionEnded,
        NluIntent,
    ]

    def __init__(self, ad: AppDaemon, name, args):
        super().__init__(ad, name, args)
        """Initialize Hermes Plugin."""

        self.AD = ad
        self.config = args
        self.name = name

        self.mqtt_client_topics = [x.topic() for x in self._hermes_messages]

        if 'namespace' in self.config:
            self.namespace = self.config['namespace']
        else:
            self.namespace = 'default'

        # Register services
        self.AD.services.register_service(self.namespace, 'hermes', 'tts_say', self.tts_say_service)
        self.AD.services.register_service(self.namespace, 'hermes', 'tts_say_finished', self.tts_say_finished_service)
        self.AD.services.register_service(self.namespace, 'hermes', 'start_session', self.start_session_service)
        self.AD.services.register_service(self.namespace, 'hermes', 'continue_session', self.continue_session_service)
        self.AD.services.register_service(self.namespace, 'hermes', 'end_session', self.end_session_service)

        self.logger.info("Hermes Plugin Initializing")

    async def tts_say_service(self, namespace, domain, service, kwargs):
        if 'text' in kwargs:
            text = kwargs['text']
            message = TtsSay(text)
            message.site_id = kwargs.get('site_id', 'default')
            message.lang = kwargs.get('lang', None)
            message.tts_id = kwargs.get('tts_id', None)
            message.session_id = kwargs.get('session_id', None)

            kwargs = {
                'topic': message.topic(),
                'payload': message.to_json()
            }
            return await self.call_plugin_service(namespace, 'mqtt', 'publish', kwargs)
        else:
            self.logger.warning('Missing parameter \'text\' for service call {!r}.'.format(service))
            raise ValueError("Missing parameter \'text\' for service call")

    async def tts_say_finished_service(self, namespace, domain, service, kwargs):
        # TODO site_id is not mentioned in Hermes specifications
        message = TtsSayFinished()
        message.id = kwargs.get('tts_id', None)
        message.session_id = kwargs.get('session_id', None)
        kwargs = {
            'topic': message.topic(),
            'payload': message.to_json()
        }
        return await self.call_plugin_service(namespace, 'mqtt', 'publish', kwargs)

    async def start_session_service(self, namespace, domain, service, kwargs):
        # TODO
        pass

    async def continue_session_service(self, namespace, domain, service, kwargs):
        if 'session_id' not in kwargs:
            self.logger.warning('Missing parameter \'session_id\' for service call {!r}.'.format(service))
            raise ValueError("Missing parameter 'session_id' for service call")
        if 'text' not in kwargs:
            self.logger.warning('Missing parameter \'text\' for service call {!r}.'.format(service))
            raise ValueError("Missing parameter 'text' for service call")

        # TODO site_id is not mentioned in Hermes specifications
        message = DialogueContinueSession(kwargs['session_id'])
        message.text = kwargs['text']
        message.intent_filter = kwargs.get('intent_filter', None)
        message.custom_data = kwargs.get('custom_data', None)
        message.send_intent_not_recognized = kwargs('send_intent_not_recognized', False)
        message.slot = kwargs.get('slot', None)

    async def end_session_service(self, namespace, domain, service, kwargs):
        if 'session_id' in kwargs:
            # TODO site_id and custom_data are not mentioned in Hermes specifications
            message = DialogueEndSession(kwargs['session_id'])
            message.text = kwargs.get('text', None)
            kwargs = {
                'topic': message.topic(),
                'payload': message.to_json()
            }
            return await self.call_plugin_service(namespace, 'mqtt', 'publish', kwargs)
        else:
            self.logger.warning('Missing parameter \'session_id\' for service call {!r}.'.format(service))
            raise ValueError("Missing parameter 'session_id' for service call")

    async def send_ad_event(self, event):
        """
        Intercepts outgoing events for handling Hermes messages.
        Other MQTT messages will go through so this plugin may also be used as a normal MQTT plugin.
        """

        if event['event_type'] == self.mqtt_event_name and 'topic' in event['data'] and event['data']['topic']:
            data = event['data']
            topic = data['topic']

            if TtsSay.is_topic(topic):
                await self.tts_say_event(TtsSay.from_json(data['payload']))

            elif TtsSayFinished.is_topic(topic):
                await self.tts_say_finished_event(TtsSayFinished.from_json(data['payload']))

            elif DialogueSessionStarted.is_topic(topic):
                await self.dialogue_session_started(DialogueSessionStarted.from_json(data['payload']))

            elif DialogueSessionEnded.is_topic(topic):
                await self.dialogue_session_ended(DialogueSessionEnded.from_json(data['payload']))

            elif NluIntent.is_topic(topic):
                await self.intent_detected(NluIntent.get_intent_name(topic), NluIntent.from_json(data['payload']))

            else:
                await super().send_ad_event(event)

        await super().send_ad_event(event)

    # TTS events

    async def tts_say_event(self, message: TtsSay):
        await self.AD.events.process_event(self.get_namespace(), {
            'event_type': constants.TTS_SAY_EVENT,
            'data': {'message': message}
        })

    async def tts_say_finished_event(self, message: TtsSayFinished):
        await self.AD.events.process_event(self.get_namespace(), {
            'event_type': constants.TTS_SAY_FINISHED_EVENT,
            'data': {'message': message}
        })

    # Dialogue events

    async def dialogue_session_started(self, message: DialogueSessionStarted):
        await self.AD.events.process_event(self.get_namespace(), {
            'event_type': constants.DIALOGUE_SESSION_STARTED_EVENT,
            'data': {'session_id': message.session_id, 'message': message}
        })

    async def dialogue_session_ended(self, message: DialogueSessionEnded):
        await self.AD.events.process_event(self.get_namespace(), {
            'event_type': constants.DIALOGUE_SESSION_ENDED_EVENT,
            'data': {'session_id': message.session_id, 'message': message}
        })

    # Intent events

    async def intent_detected(self, intent_name: str, message: NluIntent):
        await self.AD.events.process_event(self.get_namespace(), {
            'event_type': constants.INTENT_EVENT,
            'data': {'intent': intent_name, 'message': message},
        })
