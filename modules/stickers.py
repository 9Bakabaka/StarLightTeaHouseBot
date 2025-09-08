import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext.filters import MessageFilter

class StickerFilter(MessageFilter):
    def filter(self, message):
        if message.sticker and message.chat.type == 'private':
            print(datetime.datetime.now(), "\t", "Received a sticker.")
            return message.sticker
        return None


async def get_sticker_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Sending sticker ID.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.sticker.file_id)
