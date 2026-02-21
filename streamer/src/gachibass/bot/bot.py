"""Telegram bot initialization and setup.

This module handles bot Application creation and handler registration.
"""

import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from . import handlers

logger = logging.getLogger(__name__)

__bot = None


def get_bot(token: str, station_manager) -> Application:
    """Get or create the Telegram bot Application.

    Args:
        token: Telegram bot token
        station_manager: StationManager instance for bot handlers to use

    Returns:
        Configured telegram.ext.Application instance
    """
    global __bot
    if not __bot:
        __bot = Application.builder().token(token).build()

        # Store station_manager in bot_data for handlers to access
        __bot.bot_data["station_manager"] = station_manager

        # Register command handlers
        __bot.add_handler(CommandHandler("list", handlers.list_stations))
        __bot.add_handler(CommandHandler("select", handlers.select))

        # Register message handlers
        __bot.add_handler(MessageHandler(filters.AUDIO, handlers.new_song))
        __bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.echo))

        logger.info("Bot initialized with handlers")
    return __bot
