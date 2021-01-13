
import appdaemon.adbase as adbase
import appdaemon.adapi as adapi
from appdaemon.appdaemon import AppDaemon

import typing
import json

from rhasspyhermes.audioserver import AudioFrame
from rhasspyhermes.dialogue import DialogueAction, DialogueNotification
from rhasspyhermes.dialogue import DialogueStartSession, DialogueContinueSession
from rhasspyhermes.nlu import NluQuery
from rhasspyhermes.asr import AsrTextCaptured, AsrStartListening, AsrStopListening


class Hermes(adbase.ADBase, adapi.ADAPI):
    """
    Base class providing facilities for using the Hermes plugin.
    """

    def __init__(self, ad: AppDaemon, name, logging, args, config, app_config, global_vars, ):
        """
        Constructor for the app.

        Args:
            ad: AppDaemon object.
            name: name of the app.
            logging: reference to logging object.
            args: app arguments.
            config: AppDaemon config.
            app_config: config for all apps.
            global_vars: reference to global variables dict.
        """
        # Call Super Classes
        adbase.ADBase.__init__(self, ad, name, logging, args, config, app_config, global_vars)
        adapi.ADAPI.__init__(self, ad, name, logging, args, config, app_config, global_vars)

    # TTS services

    def tts_say(self, text, site_id='default', lang=None, tts_id=None, session_id=None, **kwargs):
        kwargs['text'] = text
        kwargs['site_id'] = site_id
        kwargs['lang'] = lang
        kwargs['tts_id'] = tts_id
        kwargs['session_id'] = session_id
        return self.call_service('hermes/tts_say', **kwargs)

    def tts_say_finished(self, tts_id=None, session_id=None, **kwargs):
        # TODO site_id is not mentioned in Hermes specifications
        kwargs['tts_id'] = tts_id
        kwargs['session_id'] = session_id
        return self.call_service('hermes/tts_say_finished', **kwargs)

    # Dialogue services

    def start_session(self, init: typing.Union[DialogueAction, DialogueNotification], site_id='default', custom_data=None, **kwargs):
        message = DialogueStartSession(init, site_id, custom_data)
        # TODO plugin should register a service and we should use that
        kwargs['topic'] = message.topic()
        kwargs['payload'] = message.to_json()
        kwargs['namespace'] = self._get_namespace(**kwargs)
        return self.call_service('mqtt/publish', **kwargs)

    def continue_session(self, session_id, text, intent_filter=None, custom_data=None,
                         send_intent_not_recognized=False, slot=None, **kwargs):
        # TODO site_id is not mentioned in Hermes specifications
        kwargs['session_id'] = session_id
        kwargs['text'] = text
        kwargs['intent_filter'] = intent_filter
        kwargs['custom_data'] = custom_data
        kwargs['send_intent_not_recognized'] = send_intent_not_recognized
        kwargs['slot'] = slot
        return self.call_service('hermes/continue_session', **kwargs)

    def end_session(self, session_id, text=None, **kwargs):
        # TODO site_id and custom_data are not mentioned in Hermes specifications
        kwargs['session_id'] = session_id
        kwargs['text'] = text
        return self.call_service('hermes/end_session', **kwargs)

    # ASR services

    def asr_start_listening(self, site_id='default', session_id=None, stop_on_silence=True, **kwargs):
        message = AsrStartListening(site_id=site_id, session_id=session_id, stop_on_silence=stop_on_silence)
        # TODO plugin should register a service and we should use that
        kwargs['topic'] = message.topic()
        kwargs['payload'] = message.to_json()
        kwargs['namespace'] = self._get_namespace(**kwargs)
        return self.call_service('mqtt/publish', **kwargs)

    def asr_stop_listening(self, site_id='default', session_id=None, **kwargs):
        message = AsrStopListening(site_id=site_id, session_id=session_id)
        # TODO plugin should register a service and we should use that
        kwargs['topic'] = message.topic()
        kwargs['payload'] = message.to_json()
        kwargs['namespace'] = self._get_namespace(**kwargs)
        return self.call_service('mqtt/publish', **kwargs)

    def asr_audio_frame(self, wav_file, site_id='default', **kwargs):
        with open(wav_file, 'rb') as wav_in:
            wav_bytes = wav_in.read()
            message = AudioFrame(wav_bytes)
            # TODO plugin should register a service and we should use that
            kwargs['topic'] = message.topic(site_id=site_id)
            kwargs['payload'] = message.wav_bytes
            kwargs['namespace'] = self._get_namespace(**kwargs)
            return self.call_service('mqtt/publish', **kwargs)

    def asr_text_captured_static(self, text, site_id='default', session_id=None, **kwargs):
        # FIXME passing parameters ad cazzum
        message = AsrTextCaptured(text, 1, 1, site_id=site_id, session_id=session_id)
        # TODO plugin should register a service and we should use that
        kwargs['topic'] = message.topic()
        kwargs['payload'] = message.to_json()
        kwargs['namespace'] = self._get_namespace(**kwargs)
        return self.call_service('mqtt/publish', **kwargs)

    # NLU services

    def nlu_query(self, text, intent_filter=None, request_id=None, session_id=None, site_id=None, **kwargs):
        # TODO site_id and others are not mentioned in Hermes specifications
        message = NluQuery(text, intent_filter=intent_filter, id=request_id, session_id=session_id, site_id=site_id)
        # TODO plugin should register a service and we should use that
        kwargs['topic'] = message.topic()
        kwargs['payload'] = message.to_json()
        kwargs['namespace'] = self._get_namespace(**kwargs)
        return self.call_service('mqtt/publish', **kwargs)

    @staticmethod
    def _prepare_custom_data(custom_data):
        if custom_data is not None:
            if isinstance(custom_data, str):
                return custom_data
            else:
                return json.dumps(custom_data)
        return custom_data
