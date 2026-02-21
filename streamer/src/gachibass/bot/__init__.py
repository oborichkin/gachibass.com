"""Telegram bot submodule for Gachibass.

This submodule handles all Telegram bot functionality including
command handlers and bot initialization.
"""

from .bot import get_bot
from . import handlers

__all__ = ["get_bot", "handlers"]
