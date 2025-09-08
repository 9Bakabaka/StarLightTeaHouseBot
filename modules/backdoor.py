import datetime
import re

from telegram import Update
from telegram.ext import ContextTypes

# backdoor to send message in any group
# aha not a real back door
async def backdoor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /bd.")
    # only Longtail can use this backdoor
    if not update.message.from_user.id == 5418690874:   # 5418690874: Longtail, change as you wish
        print(datetime.datetime.now(), "\t", "Not Longtail.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not my master. I would refuse your request.")
        return
    if not re.match(r'^/bd -\d+ .*', update.message.text):
        print(datetime.datetime.now(), "\t", "Sending usage.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Format not correct.")
        return
    # usage: /bd group_id message <reply_to message link>
    group_id = update.message.text.split(' ')[1]
    message = update.message.text.replace('/bd ' + group_id + ' ', '')
    reply_to_msg_id = None
    # if reply to message
    if re.match(r'^.*https://t\.me/c/(\d+)/(\d+)$', message):
        reply_to_msg_id = int(re.match(r'^.*https://t\.me/c/(\d+)/(\d+)$', message).group(2))
        message = str(re.match(r'^(.*)https://t\.me/c/(\d+)/(\d+)$', message).group(1))
    # send message
    try:
        print(datetime.datetime.now(), "\t", "Try sending ", message, " to ", group_id)
        send_to_chat = await context.bot.get_chat(chat_id=group_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Try sending\n" + message + "\nto\n" + send_to_chat.title)
        await context.bot.send_message(chat_id=send_to_chat.id, text=message, reply_to_message_id=reply_to_msg_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Success.")
    except Exception as e:
        print(datetime.datetime.now(), "\t", "Error: ", e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e))

async def backdoor_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /bddel.")
    # only Longtail can use this backdoor
    if not update.message.from_user.id == 5418690874:   # 5418690874: Longtail, change as you wish
        print(datetime.datetime.now(), "\t", "Not Longtail.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not my master. I would refuse your request.")
        return
    message_to_delete = update.message.reply_to_message
    if not message_to_delete.from_user.id == context.bot.id:
        print(datetime.datetime.now(), "\t", "Not bot's message.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot can only remove its own message.")
        return
    print(datetime.datetime.now(), "\t", "Deleting message.")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_to_delete.id)
