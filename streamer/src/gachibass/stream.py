import gi
import os
import logging
import pathlib
import threading
from typing import List, Dict

from .common import IcecastConfig

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

streams: Dict[str, "RadioStation"] = {}


def is_admin(station_id: str, user_id: int):
    return user_id in streams[station_id].admins


class RadioStation(threading.Thread):
    def __init__(
            self,
            stream_name: str,
            music_directory: str,
            icecast_config: IcecastConfig,
            mount: str,
            admins: List[int],
            *args, **kwargs
        ):

        self.stream_name = stream_name
        self.music_directory = pathlib.Path(music_directory)
        self.icecast_config = icecast_config
        self.mount = mount
        self.admins = admins

        self.playlist: List[str] = []

        self.__current_track_index = -1

        self.loop = GLib.MainLoop()

        self._setup_pipelines()
        self._load_music_files()

        super().__init__(*args, **kwargs)

    def _setup_pipelines(self):
        self.pipeline = Gst.Pipeline.new("music-streamer")

        self.filesrc = Gst.ElementFactory.make("filesrc", "file-source")
        self.decodebin = Gst.ElementFactory.make("decodebin", "decoder")
        self.audioconvert = Gst.ElementFactory.make("audioconvert", "converter")
        self.audioresample = Gst.ElementFactory.make("audioresample", "resampler")
        self.volume = Gst.ElementFactory.make("volume", "volume-control")
        self.lame = Gst.ElementFactory.make("lamemp3enc", "mp3-encoder")
        self.icecast = Gst.ElementFactory.make("shout2send", "icecast-sink")

        if not all([self.filesrc, self.decodebin, self.audioconvert, self.audioresample, 
                   self.volume, self.lame, self.icecast]):
            raise RuntimeError("Failed to create GStreamer elements")

        self.lame.set_property("bitrate", 128)
        self.lame.set_property("quality", 2)

        self.icecast.set_property("streamname", self.stream_name)
        self.icecast.set_property("mount", self.mount)
        self.icecast.set_property("ip", self.icecast_config.server)
        self.icecast.set_property("port", self.icecast_config.port)
        self.icecast.set_property("password", self.icecast_config.password)
        self.icecast.set_property("username", self.icecast_config.username)

        elements = [self.filesrc, self.decodebin, self.audioconvert, self.audioresample,
                   self.volume, self.lame, self.icecast]

        for element in elements:
            self.pipeline.add(element)

        self.filesrc.link(self.decodebin)
        self.decodebin.connect("pad-added", self.on_decodebin_pad_added)

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def on_decodebin_pad_added(self, element, pad):
        """Handle dynamic pad addition from decodebin"""
        caps = pad.get_current_caps()
        if caps and caps.get_structure(0).get_name().startswith('audio/'):
            sink_pad = self.audioconvert.get_static_pad("sink")
            pad.link(sink_pad)
            self.audioconvert.link(self.audioresample)
            self.audioresample.link(self.volume)
            self.volume.link(self.lame)
            self.lame.link(self.icecast)

    def _load_music_files(self):
        """Load all supported audio files from the music directory"""
        supported_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}

        if not self.music_directory.exists():
            os.makedirs(self.music_directory.absolute())

        self.playlist = [
            str(file) for file in self.music_directory.rglob('*') 
            if file.suffix.lower() in supported_extensions and file.is_file()
        ]

        logger.info(f"Loaded {len(self.playlist)} music files")

        self.__current_track_index = -1

    def play_next_track(self):

        if not self.playlist:
            logger.warning("Nothing to play")
            return

        self.__current_track_index = (self.__current_track_index + 1) % len(self.playlist)
        next_track = self.playlist[self.__current_track_index]
        self.pipeline.set_state(Gst.State.READY)
        self.filesrc.set_property("location", next_track)
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.play_next_track()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"{err}, {debug}")
            self.play_next_track()
        return True

    def run(self):
        try:
            self.play_next_track()
            self.loop.run()
        finally:
            self.pipeline.set_state(Gst.State.NULL)
