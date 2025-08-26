#!/usr/bin/env python3
import os
import random
import threading
import time
import gi
import json
from pathlib import Path
from queue import Queue, Empty
from typing import List, Optional, Dict, Any


gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp, GLib


class IcecastStreamer(threading.Thread):
    def __init__(
            self, music_directory: str, icecast_config: Dict[str, Any],
            *args, **kwargs
        ):

        Gst.init(None)

        self.music_directory = music_directory

        self.icecast_config = icecast_config
        self.playlist: List[str] = []

        self.current_track_index = -1

        self.is_playing = False

        self.command_queue = Queue()
        self.loop = GLib.MainLoop()

        self.original_volume = 1.0

        # Initialize GStreamer pipelines
        self.setup_pipelines()

        # Load music files
        self.load_music_files()

        super().__init__(*args, **kwargs)

    def setup_pipelines(self):
        # Main music pipeline
        self.pipeline = Gst.Pipeline.new("music-streamer")

        # Create elements for music pipeline
        self.filesrc = Gst.ElementFactory.make("filesrc", "file-source")
        self.decodebin = Gst.ElementFactory.make("decodebin", "decoder")
        self.audioconvert = Gst.ElementFactory.make("audioconvert", "converter")
        self.audioresample = Gst.ElementFactory.make("audioresample", "resampler")
        self.volume = Gst.ElementFactory.make("volume", "volume-control")
        self.lame = Gst.ElementFactory.make("lamemp3enc", "mp3-encoder")
        self.icecast = Gst.ElementFactory.make("shout2send", "icecast-sink")

        # Check if all elements were created successfully
        if not all([self.filesrc, self.decodebin, self.audioconvert, self.audioresample, 
                   self.volume, self.lame, self.icecast]):
            raise RuntimeError("Failed to create GStreamer elements")

        # Configure elements
        self.lame.set_property("bitrate", 128)
        self.lame.set_property("quality", 2)

        # Configure Icecast for main stream
        self.icecast.set_property("ip", self.icecast_config["server"])
        self.icecast.set_property("port", self.icecast_config["port"])
        self.icecast.set_property("password", self.icecast_config["password"])
        self.icecast.set_property("mount", self.icecast_config["mount"])
        self.icecast.set_property("username", self.icecast_config.get("username", "source"))
        self.icecast.set_property("streamname", self.icecast_config.get("stream_name", "Music Stream"))

        # Add elements to music pipeline
        elements = [self.filesrc, self.decodebin, self.audioconvert, self.audioresample,
                   self.volume, self.lame, self.icecast]

        for element in elements:
            self.pipeline.add(element)

        # Link music pipeline elements
        self.filesrc.link(self.decodebin)
        self.decodebin.connect("pad-added", self.on_decodebin_pad_added)

        # Set up bus for message handling
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def on_decodebin_pad_added(self, element, pad):
        """Handle dynamic pad addition from decodebin"""
        caps = pad.get_current_caps()
        if caps and caps.get_structure(0).get_name().startswith('audio/'):
            sink_pad = self.audioconvert.get_static_pad("sink")
            pad.link(sink_pad)
            # Connect the rest of the music pipeline
            self.audioconvert.link(self.audioresample)
            self.audioresample.link(self.volume)
            self.volume.link(self.lame)
            self.lame.link(self.icecast)

    def load_music_files(self):
        """Load all supported audio files from the music directory"""
        supported_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
        music_dir = Path(self.music_directory)

        if not music_dir.exists():
            raise FileNotFoundError(f"Music directory {self.music_directory} not found")

        self.playlist = [
            str(file) for file in music_dir.rglob('*') 
            if file.suffix.lower() in supported_extensions and file.is_file()
        ]

        if not self.playlist:
            raise ValueError("No supported audio files found in the music directory")

        print(f"Loaded {len(self.playlist)} music files")

    def play_next_track(self):
        self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
        next_track = self.playlist[self.current_track_index]

        print(f"Streaming: {os.path.basename(next_track)}")

        # Stop current playback
        self.pipeline.set_state(Gst.State.READY)

        # Set new file source
        self.filesrc.set_property("location", next_track)

        # Start streaming
        self.pipeline.set_state(Gst.State.PLAYING)
        self.is_playing = True

    def skip_track(self):
        """Skip to the next track"""
        print("Skipping current track...")
        self.play_next_track()

    def pause_resume(self):
        """Toggle pause/resume"""
        if self.is_playing:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.is_playing = False
            print("Streaming paused")
        else:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.is_playing = True
            print("Streaming resumed")

    def on_message(self, bus, message):
        """Handle GStreamer bus messages for music pipeline"""
        t = message.type
        if t == Gst.MessageType.EOS:
            # End of stream, play next track
            print("End of track reached")
            self.play_next_track()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            self.play_next_track()
        return True

    def run(self):
        """Start the main loop"""
        try:
            # Start with first track
            self.play_next_track()
            self.loop.run()
        finally:
            self.pipeline.set_state(Gst.State.NULL)


MUSIC_DIRECTORY = "music/"  # Change this to your music directory
ICECAST_CONFIG = {
    "server": "localhost",  # Change to your Icecast server
    "port": 8000,                         # Change to your Icecast port
    "password": "password",          # Change to your Icecast password
    "mount": "/new",               # Change to your mount point
    "username": "source",                 # Typically 'source' for Icecast
    "stream_name": "My Music Stream",     # Your stream name
}

from fastapi import FastAPI
import uvicorn

import os
from dotenv import load_dotenv
import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]

streamer = IcecastStreamer(MUSIC_DIRECTORY, ICECAST_CONFIG, daemon=True)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


async def next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    streamer.play_next_track()
    await update.message.reply_text("Track skipped")


import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):

    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("next", next))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()
    yield
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()


if __name__ == "__main__":

    api = FastAPI(lifespan=lifespan)

    streamer.start()

    uvicorn.run(api, host="127.0.0.1", port=5000)
