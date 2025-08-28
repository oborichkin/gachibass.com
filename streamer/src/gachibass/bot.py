import functools
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from gachibass.stream import streams, is_admin

logger = logging.getLogger(__name__)

__bot = None


def authorize(f):
    @functools.wraps(f)
    async def inner(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if station := context.user_data.get("current_station"):
            if is_admin(station, update.message.from_user.id):
                return await f(update, context)
            return await update.message.reply_text("Вы не админ данной станции")
        return await update.message.reply_text("Станция не выбрана. Используйте команду `/select <имя>` для выбора станции")
    return inner


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("\n".join(streams.keys()))

@authorize
async def new_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    audio_file = update.message.audio

    if audio_file:
        file_id = audio_file.file_id
        new_file = await context.bot.get_file(file_id)

        file_name = audio_file.file_name or f"{file_id}.mp3"
        save_path = f"downloads/{file_name}"

        try:
            await new_file.download_to_drive(save_path)
            await update.message.reply_text("Audio saved")
        except Exception as e:
            logger.error(str(e))
            await update.message.reply_text("error saving audio file")

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Supply radio ID")
    elif context.args[0] in streams:
        context.user_data["current_station"] = context.args[0]
        await update.message.reply_text("Current radio set")
    else:
        await update.message.reply_text("No such radio")

def get_bot(token):
    global __bot
    if not __bot:
        __bot = Application.builder().token(token).build()
        __bot.add_handler(CommandHandler("list", list))
        __bot.add_handler(CommandHandler("select", select))
        __bot.add_handler(MessageHandler(filters.AUDIO, new_song))
        __bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return __bot
