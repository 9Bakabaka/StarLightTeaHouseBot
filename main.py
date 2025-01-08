### By Longtail Amethyst Eralbrunia 2024-09-26
### Stop posting your shit to Internet
import json
import time
import datetime
import asyncio
import re
from lib2to3.fixes.fix_input import context
from uuid import uuid4
import random
import psutil
from ping3 import ping

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultCachedSticker
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters, \
    InlineQueryHandler
from telegram.ext.filters import MessageFilter

import notifyAdmin

# import token from file
with open('bottoken', 'r', encoding='utf-8') as file:
    botToken = file.read().replace('\n', '')
    # print(botToken)


# todo: silence for x minutes
# todo: 繁体国行检测开关
# todo: 尾巴触电
# todo: add quote, print quote list and delete quote

# import quotes from file
def load_quotes(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


# '国行' reaction filter
class AppleCNMSGFilter(MessageFilter):
    def filter(self, message):
        if message.text and ('国行' in message.text or '國行' in message.text):
            return 1

# possibility filter
class XMAndFireReactionFilter(MessageFilter):
    possibility = 0.05

    def filter(self, message):
        random_result = random.random()
        # print(datetime.datetime.now(), "\t", "Random possibility: ", random_result)
        if random_result < self.possibility:
            return 1

# 吃什么 filter
class WhatToEatFilter(MessageFilter):
    def filter(self, message):
        if message.text:
            if '/eattoday' in message.text:
                return 1
            if ('今天吃什么' or '等会吃什么' or '早上吃什么' or '中午吃什么' or '下午吃什么' or '晚上吃什么' or '饿了' or '好饿' or '饿' or '饿饿') in message.text:
                return 1


# new user filter
class NewUserFilter(MessageFilter):
    def filter(self, message):
        return message.new_chat_members


# sticker filter
class StickerFilter(MessageFilter):
    def filter(self, message):
        if message.sticker and message.chat.type == 'private':
            print(datetime.datetime.now(), "\t", "Received a sticker.")
            return message.sticker


# start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /start.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nya")


# sticker handler
async def get_sticker_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Sending sticker ID.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.sticker.file_id)


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

# group welcome message setting handler
async def group_welcome_msg_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received " + update.message.text + " ", end="")
    if update.effective_chat.type not in ['group', 'supergroup']:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This command is only available in group.")
        print("Not a group chat.")
        return
    # if only /groupwelcome, show usage
    if update.message.text == '/groupwelcome':
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage:\n/groupwelcome <on/off> Toggle group welcome message.\n/groupwelcome setmsg <message> Set group welcome message.\n/groupwelcome verify <on/off> Set group verify.\n/groupwelcome vffilter <regex> Set group verify filter.\n/groupwelcome setvfmsg <message> Set group verify message.\n/groupwelcome setvffailmsg <message> Set group verify fail message.")
        print("Showing usage")
    else:   # else, read config file, locate current group and ready to edit
        try:
            with open('welcome_msg_config.json', 'r', encoding='utf-8') as file:
                welcome_msg_config = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            welcome_msg_config = []

        # search for this group in config
        # if not found, use default group config, if found, use the found group config
        group = {'groupid': update.effective_chat.id, 'welcome': False, 'message': 'Welcome {new_member_first_name} {new_member_last_name} to the Group!', 'verify': False, 'verify_filter': '.*', 'verify_msg': 'Verification success!', 'verify_fail_msg': 'Verification failed!'}
        for timer in welcome_msg_config:
            if timer['groupid'] == update.effective_chat.id:
                group = timer
                break
        # only group admins can use the following commands
        if not (await update.effective_chat.get_member(update.effective_user.id)).status in ['administrator', 'creator']:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Only group admins can use this command.")
            # command handler in else
        else:
            if update.message.text == '/groupwelcome on':
                group['welcome'] = True
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome message enabled.")
                print("Welcome message enabled.")
            elif update.message.text == '/groupwelcome off':
                group['welcome'] = False
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome message disabled.")
                print("Welcome message disabled.")
            elif update.message.text.startswith('/groupwelcome setmsg '):
                group['message'] = update.message.text.replace('/groupwelcome setmsg ', '')
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome message updated.")
                print("Welcome message updated.")
            elif update.message.text.startswith('/groupwelcome verify on'):
                group['verify'] = True
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Group verify enabled.")
                print("Group verify enabled.")
            elif update.message.text.startswith('/groupwelcome verify off'):
                group['verify'] = False
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Group verify disabled.")
                print("Group verify disabled.")
            elif update.message.text.startswith('/groupwelcome vffilter '):
                group['verify_filter'] = update.message.text.replace('/groupwelcome vffilter ', '')
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Group verify filter updated.")
                print("Group verify filter updated.")
            elif update.message.text.startswith('/groupwelcome setvfmsg '):
                group['verify_msg'] = update.message.text.replace('/groupwelcome setvfmsg ', '')
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Group verify message updated.")
                print("Group verify message updated.")
            elif update.message.text.startswith('/groupwelcome setvffailmsg '):
                group['verify_fail_msg'] = update.message.text.replace('/groupwelcome setvffailmsg ', '')
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Group verify fail message updated.")
                print("Group verify fail message updated.")
            else:
                # default aka not recognized
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage:\n/groupwelcome <on/off> Toggle group welcome message.\n/groupwelcome setmsg <message> Set group welcome message.\n/groupwelcome verify <on/off> Set group verify.\n/groupwelcome vffilter <regex> Set group verify filter.\n/groupwelcome setvfmsg <message> Set group verify message.\n/groupwelcome setvffailmsg <message> Set group verify fail message.")

        # save config file
        if group not in welcome_msg_config:
            welcome_msg_config.append(group)
        else:
            welcome_msg_config[welcome_msg_config.index(group)] = group
        with open('welcome_msg_config.json', 'w', encoding='utf-8') as file:
            json.dump(welcome_msg_config, file, ensure_ascii=False, indent=4)


class NewUserVerify:
    # If a new user joins the group, send a welcome message
    WaitingForReply = 1
    verification_timeout = 300  # seconds
    new_user_data = {}

    async def send_group_welcome_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for new_member in update.message.new_chat_members:
            # get welcome message text from config
            # open file
            try:
                with open('welcome_msg_config.json', 'r', encoding='utf-8') as file:
                    welcome_msg_config = json.load(file)
                if not welcome_msg_config:
                    welcome_msg_config = [{'groupid': update.effective_chat.id, 'welcome': False, 'message': 'Welcome to the Group!', 'verify': False, 'verify_filter': '.*', 'verify_msg': 'Verification success!', 'verify_fail_msg': 'Verification failed!'}]
            except Exception as e:
                welcome_msg_config = [{'groupid': update.effective_chat.id, 'welcome': False, 'message': 'Welcome to the Group!', 'verify': False, 'verify_filter': '.*', 'verify_msg': 'Verification success!', 'verify_fail_msg': 'Verification failed!'}]
            # search for this group in config
            welcome = False
            verify = False
            welcome_msg = ""
            for group in welcome_msg_config:
                if group['groupid'] == update.effective_chat.id:
                    welcome = group['welcome']
                    verify = group['verify']
                    welcome_msg = group['message']
                    # reformat welcome message
                    # {new_member_username}, {new_member_first_name}, {and new_member_last_name} is supported
                    new_member = update.message.new_chat_members[0]
                    welcome_msg = welcome_msg.format(
                        new_member_username=new_member.username or 'Username not visible',
                        new_member_first_name=new_member.first_name or '',
                        new_member_last_name=new_member.last_name or ''
                    )
                    break
            # if welcome is disabled, don't run the following code
            if not welcome:
                return
            print(datetime.datetime.now(), "\t", "Sending welcome message to new user.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{welcome_msg}\n"
            )
            # if verify is disabled, don't run the following code
            if not verify:
                return
            # add new user to verification list
            self.new_user_data[new_member.id] = {'NewUser': True}
            print(datetime.datetime.now(), "\t", "User_data updated to: ", self.new_user_data)
            # set timer for new member
            timer_task = asyncio.create_task(self.verify_timer(new_member.id, update))
            self.new_user_data[new_member.id]['timer_task'] = timer_task
        return self.WaitingForReply

    async def verify_twitter_user_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(datetime.datetime.now(), "\t", "VerifyTwitterUserName Called")
        userID = update.message.from_user.id
        user_data = self.new_user_data.get(userID, {})
        try:
            with open('welcome_msg_config.json', 'r', encoding='utf-8') as file:
                welcome_msg_config = json.load(file)
        except Exception as e:
            print(datetime.datetime.now(), "\t", "Error reading welcome_msg_config.json: ", e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e) + "\nPlease contact the admin.")
        # get filter in regex for this group
        verify_filter = r'.*'
        verify_msg = ''
        verify_fail_msg = ''
        for group in welcome_msg_config:
            if group['groupid'] == update.effective_chat.id:
                verify_filter = group['verify_filter']
                print("Verify filter: ", verify_filter)
                verify_msg = group['verify_msg']
                verify_fail_msg = group['verify_fail_msg']
                break

        if re.match(verify_filter, update.message.text) and user_data.get('NewUser', True):
            print(datetime.datetime.now(), "\t", "Delete the new user from new_user_data")
            # remove the timer
            timer_task = user_data.get('timer_task')
            if timer_task:
                    timer_task.cancel()
            del self.new_user_data[userID]
            print(datetime.datetime.now(), "\t", "User_data updated to: ", self.new_user_data)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{verify_msg}\n"
            )
            return ConversationHandler.END
        else:
            # tell user to send their account in right format
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{verify_fail_msg}\n"
            )
            return self.WaitingForReply

    async def verify_timer(self, new_member_id, update: Update):
        print(datetime.datetime.now(), "\t", "VerifyTimer Called")
        await asyncio.sleep(self.verification_timeout)
        # if new_member_id is still in user_data after timeout
        userID = update.message.from_user.id
        user_data = self.new_user_data.get(userID, {})
        if new_member_id in self.new_user_data:
            # put your custom methods here
            # for example, I will call notify_admin from notifyAdmin.py
            print(datetime.datetime.now(), "\t", "User verification timeout.")
            notifyAdmin.notify_admin(context, f"User {new_member_id} has not verified their account in time.")
            timer_task = user_data.get('timer_task')
            if timer_task:
                timer_task.cancel()
            del self.new_user_data[userID]
        return


# mark a crown emoji on the message if it contains '国行'
async def apple_cn_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🤡')


# random reply '羡慕' and fire reaction according to possibility
async def xm_and_fire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 50 50
    if random.random() < 0.5:
        print(datetime.datetime.now(), "\t", "Replying 羡慕")
        await update.message.reply_text('羡慕')
    else:
        print(datetime.datetime.now(), "\t", "Reacting 🔥")
        await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🔥')


# random reply a kind of food when calling /eattoday
async def what_to_eat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 5% chance trigger I EAT MYSELF
    chance_I_EAT_MYSELF = 0.05
    if random.random() < chance_I_EAT_MYSELF:
        print(datetime.datetime.now(), "\t", "What to eat today called.")
        await update.message.reply_text("吃" + update.message.from_user.first_name + update.message.from_user.last_name + "！")
    else:
        # food = ['麻辣烫', '炒饭', '炒面', '炒粉', '炒河粉', '炒米粉', '炒土豆丝', '炒青菜', '炒西兰花', '炒芹菜', '炒莴笋', '炒豆角', '炒茄子']
        with open('foodlist.txt', 'r', encoding='utf-8') as food_list_file:
            food = [line.strip() for line in food_list_file.readlines()]
        print(datetime.datetime.now(), "\t", "What to eat today called.")
        await update.message.reply_text("吃" + random.choice(food) + "！")


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

    # global function switches
    start_handler_switch = True
    sticker_handler_switch = True
    system_status_handler_switch = True
    apple_cn_msg_handler_switch = False
    what_to_eat_today_handler_switch = True
    xm_ad_fire_switch = False

    # start handler
    if start_handler_switch:
        start_handler = CommandHandler('start', start)
        application.add_handler(start_handler)

    # sticker handler
    if sticker_handler_switch:
        stickerFilter = StickerFilter()
        sticker_handler = MessageHandler(stickerFilter, get_sticker_id)
        application.add_handler(sticker_handler)

    # system status handler
    if system_status_handler_switch:
        status_handler = CommandHandler('status', system_status)
        application.add_handler(status_handler)

    # apple CN message handler
    if apple_cn_msg_handler_switch:
        appleCNMSGFilter = AppleCNMSGFilter()
        AppleCNMSG_handler = MessageHandler(appleCNMSGFilter, apple_cn_msg)
        application.add_handler(AppleCNMSG_handler)

    # what to eat today handler
    if what_to_eat_today_handler_switch:
        what_to_eat_filter = WhatToEatFilter()
        what_to_eat_handler = MessageHandler(what_to_eat_filter, what_to_eat)
        application.add_handler(what_to_eat_handler)

    # group welcome message setting handler
    group_welcome_msg_handler = CommandHandler('groupwelcome', group_welcome_msg_setting)
    application.add_handler(group_welcome_msg_handler)

    # new user handler
    new_user_verify = NewUserVerify()
    newUserFilter = NewUserFilter()
    welcomeMSG_handler = ConversationHandler(
        entry_points=[MessageHandler(newUserFilter, new_user_verify.send_group_welcome_msg)],
        states={
            new_user_verify.WaitingForReply: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_user_verify.verify_twitter_user_name)]
        },
        fallbacks=[]
    )
    application.add_handler(welcomeMSG_handler)

    # this handler must be put after all message handlers
    # xm and fire reaction handler
    if xm_ad_fire_switch:
        xm_and_fire_reaction_filter = XMAndFireReactionFilter()
        xm_and_fire_reaction_handler = MessageHandler(xm_and_fire_reaction_filter, xm_and_fire)
        application.add_handler(xm_and_fire_reaction_handler)

    # inline mentioned handler
    application.add_handler(InlineQueryHandler(inline_query))

    # start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
