from slixmpp.plugins import xep_0066

import importer

import hermes.constants as hermes_constants
import hermes.hermesapi as hermes

import os
import cgi
import tempfile
import shutil
import slixmpp
import urllib3

from rhasspyhermes.dialogue import DialogueAction, DialogueSessionStarted
from rhasspyhermes.tts import TtsSay

#
# App used by the smart assistant for acting as a Rhasspy satellites using XMPP.
#
# Basically it allows you to send commands via XMPP. Replies are sent back via XMPP as well.
# Inspired by POC here: https://github.com/mariohock/Chatty


# noinspection PyAttributeOutsideInit
class AssistantXMPP(hermes.Hermes):

    async def initialize(self):
        # TODO handle multiple sessions (and use a data class)
        self.session_id = None
        self.session_input_text = None
        self.session_input_audio = None
        self.session_sender = None
        self.events = [
            self.listen_event(self.session_started,
                              hermes_constants.DIALOGUE_SESSION_STARTED_EVENT,
                              namespace='hermes'),
            self.listen_event(self.tts_say_event,
                              hermes_constants.TTS_SAY_EVENT,
                              namespace='hermes')
        ]
        self.site_id = self.args['site_id']

        xmpp_username = self.args['xmpp_username']
        xmpp_password = self.args['xmpp_password']
        self.allowed_senders = [x.casefold() for x in self.args['allowed_senders']]

        self.start_xmpp(xmpp_username, xmpp_password)

        self.log("Assistant XMPP support started", level='INFO')

    async def terminate(self):
        for e in self.events:
            await self.cancel_listen_event(e)

        self.log("Terminating XMPP session", level='DEBUG')
        self.xmpp.do_reconnections = False
        self.xmpp.disconnect()
        await self.xmpp.disconnected
        del self.xmpp
        self.log("XMPP session terminated.", level='DEBUG')

    def start_xmpp(self, username, password):
        self.log("Starting XMPP connection for %s" % username, level='DEBUG')
        self.xmpp = XMPPconnector(username, password, self)
        self.xmpp.register_plugin('xep_0030')  # Service Discovery
        self.xmpp.register_plugin('xep_0199')  # XMPP Ping
        self.xmpp.register_plugin('xep_0066')  # Out of Band Data
        self.xmpp.connect()

    async def on_incoming_message(self, msg):
        sender: slixmpp.JID = msg["from"]
        url = msg["oob"]["url"]
        message = msg["body"]
        if message:
            self.log("Incoming: '%s', from '%s'" % (message, sender), level='DEBUG')
        elif url:
            self.log("Incoming: (media), from '%s'" % sender, level='DEBUG')

        if not message and not url:
            self.log("Empty message, discarding", level='INFO')
            return None

        if sender.bare.casefold() not in self.allowed_senders:
            self.log("Unauthorized sender: %s" % sender, level='WARN')
            return None

        # TEST
        # TODO in theory we could use custom data to store the text, but Hermes doesn't officially support it
        if url:
            self.session_input_text = None
            self.session_input_audio = url
        else:
            self.session_input_text = message
            self.session_input_audio = None
        self.session_sender = sender.bare

        session_init = DialogueAction(can_be_enqueued=False)
        # TODO session continuation
        self.start_session(session_init, self.site_id, namespace='hermes')
        # will wait for session started to proceed

        # TEST autonomous session
        """
        from uuid import uuid4
        self.session_id = str(uuid4())
        self.nlu_query(self.session_input_text,
                       session_id=self.session_id,
                       request_id=self.session_id,
                       site_id=self.site_id,
                       namespace='hermes')
        """

        return None

    def session_started(self, event, data: dict, kwargs):
        message: DialogueSessionStarted = data['message']
        if message.site_id != self.site_id:
            self.log("Session is not for us. Dismissing.", level='DEBUG')
            return

        session_id = data['session_id']
        self.session_id = session_id

        if self.session_input_audio:
            # download audio
            wav_file = self.download_audio()
            if wav_file:
                """
                TODO start listening is sent by the dialogue manager after session start
                self.asr_start_listening(site_id=self.site_id,
                                         session_id=self.session_id,
                                         stop_on_silence=False,
                                         namespace='hermes')
                """
                self.asr_audio_frame(wav_file,
                                     site_id=self.site_id,
                                     namespace='hermes')
                self.asr_stop_listening(site_id=self.site_id,
                                        session_id=self.session_id,
                                        namespace='hermes')
            else:
                self.log("Audio file decoding failed, aborting session")
                self.end_session(session_id=self.session_id, namespace='hermes')
                self.session_id = None
        else:
            self.asr_text_captured_static(self.session_input_text,
                                          site_id=self.site_id,
                                          session_id=self.session_id,
                                          namespace='hermes')
            # AsrTextCaptured will trigger the rest of the pipeline
            #self.nlu_query(self.session_input_text, session_id=self.session_id, site_id=self.site_id, namespace='hermes')

    def download_audio(self):
        audio_in = None
        http = urllib3.PoolManager()
        with http.request('GET', self.session_input_audio, preload_content=False) as resp, \
                tempfile.NamedTemporaryFile(delete=False) as out_file:
            if resp.status == 200:
                shutil.copyfileobj(resp, out_file)
                _, params = cgi.parse_header(resp.headers.get('Content-Disposition', ''))
                filename = params['filename']
                if filename:
                    _, file_ext = os.path.splitext(filename)
                    audio_in = out_file.name + file_ext
                    os.rename(out_file.name, out_file.name + file_ext)

        resp.release_conn()

        if audio_in:
            audio_out = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
            if os.system('ffmpeg -y -i {} -acodec pcm_s16le -ar 16000 {}'.format(audio_in, audio_out)) == 0:
                self.log("Converted to: %s" % audio_out)
                return audio_out

    def tts_say_event(self, event, data: dict, kwargs):
        message: TtsSay = data['message']
        if message.site_id == self.site_id:
            # send message to XMPP user
            self.xmpp.send_message_to(self.session_sender, message.text)
            self.tts_say_finished(message.id, namespace='hermes')


class XMPPconnector(slixmpp.ClientXMPP):
    def __init__(self, jid, password, message_handler):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.message_handler = message_handler
        self.log = message_handler.log

        self.do_reconnections = True
        self.is_first_connection = True

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.on_message)
        self.add_event_handler("disconnected", self.on_disconnect)
        self.add_event_handler("connection_failed", self.on_connection_failure)
        self.register_handler(
            slixmpp.Callback('IM',
                             slixmpp.MatchXPath('{%s}message/{%s}%s' % (self.default_ns,
                                                                        xep_0066.stanza.OOB.namespace,
                                                                        xep_0066.stanza.OOB.name)),
                             self._handle_message))

    def _handle_message(self, msg):
        """Workaround for handling body-less messages with OOB."""
        if 'body' not in msg:
            if not self.is_component and not msg['to'].bare:
                msg['to'] = self.boundjid
            self.event('message', msg)

    def start(self, event):
        self.log("Connection established.", level='INFO')
        self.send_presence()
        self.get_roster()

        if self.is_first_connection:
            self.is_first_connection = False
        else:
            self.log("Reconnected after connection loss.", level='INFO')

    def on_disconnect(self, event):
        if self.do_reconnections:
            self.connect()

    def on_connection_failure(self, event):
        self.log("XMPP connection failed. Try to reconnect in 5min.")
        self.schedule("Reconnect after connection failure", 60*5, self.on_disconnect, event)

    def send_message_to(self, recipient, message):
        try:
            self.send_message(mto=recipient, mbody=message, mtype='chat')
        except slixmpp.xmlstream.xmlstream.NotConnectedError:
            self.log("Message NOT SENT, not connected.")
            ## TODO enqueue message for sending after reconnect
        except:
            self.log("Message NOT SENT, due to unexpected error!")

    async def on_message(self, msg):
        """
        called by slixmpp on incoming XMPP messages
        """

        if msg['type'] in ('chat', 'normal'):
            try:
                answer = await self.message_handler.on_incoming_message(msg)
            except:
                answer = None
                self.log("Error handling incoming message", level='ERROR', exc_info=True)

            if answer:
                try:
                    msg.reply(answer).send()
                except slixmpp.xmlstream.xmlstream.NotConnectedError:
                    self.log("Reply NOT SENT, not connected.", level='WARN')
                    ## TODO enqueue message for sending after reconnect
                except:
                    self.log("Reply NOT SENT, due to unexpected error!", level='WARN')
