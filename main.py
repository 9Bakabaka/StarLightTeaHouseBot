### By Longtail Amethyst Eralbrunia 2024-09-26
### Stop posting your shit to Internet
import json
import time
import datetime
import asyncio
from lib2to3.fixes.fix_input import context
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultCachedSticker
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters, \
    InlineQueryHandler
from telegram.ext.filters import MessageFilter

import notifyAdmin

# import token from file
with open('bottoken', 'r', encoding='utf-8') as file:
    botToken = file.read().replace('\n', '')
    # print(botToken)


# import quotes from file
def load_quotes(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


# '国行' reaction filter
class AppleCNMSGFilter(MessageFilter):
    def filter(self, message):
        if message.text and ('国行' in message.text or '國行' in message.text):
            return 1


# new user filter
class NewUserFilter(MessageFilter):
    def filter(self, message):
        return message.new_chat_members


# sticker filter
class StickerFilter(MessageFilter):
    def filter(self, message):
        print(datetime.datetime.now(), "\t", "Received a sticker.")
        return message.sticker


# start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Sending start message.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nya")


# sticker handler
async def get_sticker_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Sending sticker ID.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.sticker.file_id)


class NewUserVerify:
    # If a new user joins the group, send a welcome message
    WaitingForReply = 1
    verification_timeout = 300  # seconds
    new_user_data = {}

    async def send_group_welcome_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for new_member in update.message.new_chat_members:
            self.new_user_data[new_member.id] = {'NewUser': True}
            print(datetime.datetime.now(), "\t", "User_data updated to: ", self.new_user_data)
            print(datetime.datetime.now(), "\t", "Sending welcome message to new user.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"@{new_member.username}\n"
                     f"{new_member.first_name or ''} {new_member.last_name or ''} Welcome to the group!\n"
                     f"Please provide your twitter account(@username) in order to verify your identity."
                     f"You shall only type @yourID into the chat box. But not like 'I am yourID'."
            )
            asyncio.create_task(self.verify_timer(new_member.id))
        return self.WaitingForReply

    async def verify_twitter_user_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(datetime.datetime.now(), "\t", "VerifyTwitterUserName Called")
        userID = update.message.from_user.id
        userData = context.user_data.get(userID, {})
        if update.message.text.startswith('@') and userData.get('NewUser', True):
            print(datetime.datetime.now(), "\t", "Delete the new user from new_user_data")
            del self.new_user_data[userID]
            print(datetime.datetime.now(), "\t", "User_data updated to: ", self.new_user_data)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Your twitter account is verifying... Please wait for group admin to verify your identity."
            )
            return ConversationHandler.END

    async def verify_timer(self, new_member_id):
        print(datetime.datetime.now(), "\t", "VerifyTimer Called")
        await asyncio.sleep(self.verification_timeout)
        # if new_member_id is still in user_data after timeout
        if new_member_id in self.new_user_data:
            # put your custom methods here
            # for example, I will call notify_admin from notifyAdmin.py
            print(datetime.datetime.now(), "\t", "User verification timeout.")
            notifyAdmin.notify_admin(context, f"User {new_member_id} has not verified their account in time.")
        return


# mark a crown emoji on the message if it contains '国行'
async def apple_cn_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🤡')


# when bot mentioned inline, reply with quote
async def inline_query(update: Update, context):
    print(datetime.datetime.now(), "\t", "Calling inlineQuery")
    query = update.inline_query.query.strip()
    # if user input nothing, show the list instead of 'Nya'
    '''
    if not query:
        # default result: when user inputs nothing
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title='Nya',  # the title
                input_message_content=InputTextMessageContent('Nya')  # the content user will send
            )
        ]
        await update.inline_query.answer(results)
        return
    '''
    loadedQuotes = load_quotes('quotes.json')
    # this would read the json everytime the query function called
    # which is not good, improvement will be needed but later
    # quotes = ['quote1', 'quote2', 'quote3']   # for debug only
    # search quotes according to user input
    filtered_quotes = sorted(
        loadedQuotes,
        key=lambda quote: (quote['quote'].count(query) + quote['speaker'].count(query)),
        reverse=True
    )
    '''
    if not filtered_quotes:  # if quote not found
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title='No matching quotes found nya',
                input_message_content=InputTextMessageContent('')
            )
        ]
    else:
    '''
    results = []
    if "哎呀" in query:
        results += [(
            InlineQueryResultCachedSticker(
                id=str(uuid4()),
                sticker_file_id="CAACAgUAAxkBAAIBA2cgmvcwGcdCVA1HwwsnjALyL80-AAJdBAAC_9CJVsMSLkHioimoNgQ",

            )
        )]

    results.extend([
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=quote['quote'],  # the title
            description=quote['speaker'],  # the subtitle
            input_message_content=InputTextMessageContent(quote['quote'])  # the content user will send
        )
        for quote in filtered_quotes
    ])
    await update.inline_query.answer(results)


def main():
    application = ApplicationBuilder().token(botToken).build()
    # start handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # sticker handler
    stickerFilter = StickerFilter()
    sticker_handler = MessageHandler(stickerFilter, get_sticker_id)
    application.add_handler(sticker_handler)

    # apple CN message handler
    appleCNMSGFilter = AppleCNMSGFilter()
    AppleCNMSG_handler = MessageHandler(appleCNMSGFilter, apple_cn_msg)
    application.add_handler(AppleCNMSG_handler)

    # new user handler
    new_user_verify = NewUserVerify()
    newUserFilter = NewUserFilter()
    welcomeMSG_handler = ConversationHandler(
        entry_points=[MessageHandler(newUserFilter, new_user_verify.send_group_welcome_msg)],
        states={
            new_user_verify.WaitingForReply: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_user_verify.verify_twitter_user_name)]
        },
        fallbacks=[]
    )
    application.add_handler(welcomeMSG_handler)

    # inline mentioned handler
    application.add_handler(InlineQueryHandler(inline_query))

    # start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
