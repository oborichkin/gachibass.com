"""Telegram bot command handlers.

This module contains all command handlers for the Telegram bot.
Handlers receive a StationManager instance via bot.user_data for
interacting with radio stations.
"""

import functools
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def authorize(f):
    """Decorator to authorize users as admins before running handler."""
    @functools.wraps(f)
    async def inner(update: Update, context: ContextTypes.DEFAULT_TYPE):
        station_manager = context.bot_data.get("station_manager")
        user_id = update.message.from_user.id

        # Check global admin
        if station_manager and station_manager.is_global_admin(user_id):
            return await f(update, context)

        # Check station-specific admin
        if station_id := context.user_data.get("current_station"):
            if station_manager and station_manager.is_admin(station_id, user_id):
                return await f(update, context)

        await update.message.reply_text("Вы не админ данной станции")
        return None
    return inner


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo back the user's message."""
    await update.message.reply_text(update.message.text)


async def list_stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available radio stations."""
    station_manager = context.bot_data.get("station_manager")
    if not station_manager:
        await update.message.reply_text("Station manager not initialized")
        return

    stations = station_manager.get_station_names()
    if not stations:
        await update.message.reply_text("No stations available")
        return

    await update.message.reply_text("\n".join(stations))


@authorize
async def new_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new audio file uploads.

    Downloads the audio file and saves it to the selected station's playlist.
    """
    station_manager = context.bot_data.get("station_manager")
    station_id = context.user_data.get("current_station")

    if not station_manager:
        await update.message.reply_text("Station manager not initialized")
        return

    if not station_id:
        await update.message.reply_text("Станция не выбрана. Используйте команду `/select <имя>` для выбора станции")
        return

    station = station_manager.get_station(station_id)
    if not station:
        await update.message.reply_text(f"Station {station_id} not found")
        return

    audio_file = update.message.audio
    if not audio_file:
        await update.message.reply_text("Please send an audio file")
        return

    file_id = audio_file.file_id
    new_file = await context.bot.get_file(file_id)

    file_name = audio_file.file_name or f"{file_id}.mp3"
    save_path = station.music_directory / file_name

    try:
        await new_file.download_to_drive(str(save_path))
        await update.message.reply_text("Audio saved")
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("error saving audio file")


async def select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Select the current radio station for admin operations."""
    station_manager = context.bot_data.get("station_manager")
    if not station_manager:
        await update.message.reply_text("Station manager not initialized")
        return

    if not context.args:
        await update.message.reply_text("Supply radio ID")
        return

    station_id = context.args[0]
    if not station_manager.station_exists(station_id):
        await update.message.reply_text("No such radio")
        return

    context.user_data["current_station"] = station_id
    await update.message.reply_text(f"Current radio set to {station_id}")
