import datetime
import psutil
from ping3 import ping

from telegram import Update
from telegram.ext import ContextTypes

# start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /start.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nya")

# system status handler
async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /status.")
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    try:
        ping_result = int(ping('8.8.8.8', unit='ms', timeout=10))
        if ping_result is None:
            ping_result = "Timeout"
    except Exception as e:
        ping_result = "Error, " + str(e)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"CPU: {cpu_percent}%\n"
             f"Memory: {memory_info.percent}%\n"
             f"Network: {ping_result} ms to 8.8.8.8"
    )

# return function not enabled message
async def function_not_enabled(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received command for a disabled function.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="This function is not enabled. Please contact the administrator.")
