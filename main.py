### By Longtail Amethyst Eralbrunia 2024-09-26
### Stop posting your shit to Internet
import json
import datetime
import asyncio
import re
from uuid import uuid4
import random
import psutil
import telegram.error
from ping3 import ping
from functools import partial
import os
import shutil

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultCachedSticker
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters, \
    InlineQueryHandler, CallbackContext
from telegram.ext.filters import MessageFilter

import notifyAdmin
from download_jm_pdf import download_comic
from LLM import fetch_from_AI

# import token from file
with open('bottoken', 'r', encoding='utf-8') as file:
    botToken = file.read().replace('\n', '')
    # print(botToken)


# todo: silence for x minutes
# todo: 尾巴触电
# todo: add quote, print quote list and delete quote
# todo: verification timeout customize

# '国行' reaction filter
class AppleCNMSGFilter(MessageFilter):
    def filter(self, message):
        if message.text and ('国行' in message.text or '國行' in message.text):
            return 1


# xm and fire possibility filter
# noinspection PyTypeChecker
class XMAndFireReactionFilter(MessageFilter):
    # get possibility from the global array xm_and_fire_possibility
    # define before use, typical c++ style, aha-aha
    enabled = 0
    possibility = 0
    possibility_list = None

    # reload the config file and return the possibility list
    def reload_config(self):
        try:
            with open('xm_and_fire.json', 'r', encoding='utf-8') as config_file:
                self.possibility_list = json.load(config_file)
        except FileNotFoundError:
            self.possibility_list = []
            with open('xm_and_fire.json', 'w', encoding='utf-8') as config_file:
                json.dump(self.possibility_list, config_file, ensure_ascii=False, indent=4)
        return self.possibility_list

    def save_config(self, xm_and_fire_possibility):
        with open('xm_and_fire.json', 'w', encoding='utf-8') as file:
            json.dump(xm_and_fire_possibility, file, ensure_ascii=False, indent=4)

    def filter(self, message):
        # try to get possibility from possibility list
        try:
            for group in self.possibility_list:
                if group['groupid'] == message.chat.id:
                    self.enabled = group['enabled']
                    self.possibility = group['possibility']
        except KeyError:  # if not found, set possibility to 0
            self.possibility = 0
            self.possibility_list[message.chat.id] = {'groupid': message.chat.id, 'possibility': 0, 'enabled': False}
            # save change to file
            with open('xm_and_fire.json', 'w', encoding='utf-8') as file:
                json.dump(self.possibility_list, file, ensure_ascii=False, indent=4)
            # reload the file
            with open('xm_and_fire.json', 'r', encoding='utf-8') as file:
                self.possibility_list = json.load(file)
            return False

        # if not enabled, return False
        if not self.enabled:
            return False
        # return random_result < self.possibility ? 1 : 0
        return True if random.random() < self.possibility else False


class WhatToEatFilter(MessageFilter):
    def filter(self, message):
        if message.text:
            if '/eattoday' in message.text:
                return 1
            if re.search(r'今天吃什么|等会吃什么|早上吃什么|中午吃什么|下午吃什么|晚上吃什么|饿了|好饿|饿饿', message.text):
                return 1


class NewUserFilter(MessageFilter):
    def filter(self, message):
        if message.new_chat_members:
            for user in message.new_chat_members:
                if user.id == message.from_user.id:
                    return True
        return False


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
# noinspection PyTypeChecker
async def group_welcome_msg_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received " + update.message.text + ", ", end="")
    usage_msg = "Usage:\n/groupwelcome <on/off> Toggle group welcome message.\n/groupwelcome setmsg <message> Set group welcome message.\n/groupwelcome verify <on/off> Toggle group verify.\n/groupwelcome vffilter <regex> Set group verify filter.\n/groupwelcome setvfmsg <message> Set group verify message.\n/groupwelcome setvffailmsg <message> Set group verify fail message.\n/groupwelcome approve Approve all user pending."
    if update.effective_chat.type not in ['group', 'supergroup']:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="This command is only available in group.")
        print("Not a group chat.")
        return
    # if only /groupwelcome, show usage
    if update.message.text == '/groupwelcome':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=usage_msg)
        print("Showing usage")
    else:
        # only group admins can change the settings
        # if not admin, return
        if not (await update.effective_chat.get_member(update.effective_user.id)).status in ['administrator',
                                                                                             'creator']:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Only group admins can use this command.")
            return

        # read config file, locate current group and ready to edit
        try:
            with open('welcome_msg_config.json', 'r', encoding='utf-8') as file:
                welcome_msg_config = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            welcome_msg_config = []

        # search for this group in config
        # if not found, use default group config, if found, use the found group config
        default_groupwelcome_config = {'groupid': update.effective_chat.id,
                                       'welcome': False,
                                       'message': 'Welcome {new_member_first_name} {new_member_last_name} to the Group!',
                                       'verify': False,
                                       'verify_filter': '.*',
                                       'verify_msg': 'Verification success!',
                                       'verify_fail_msg': 'Verification failed!'}

        group = default_groupwelcome_config
        for timer in welcome_msg_config:
            if timer['groupid'] == update.effective_chat.id:
                group = timer
                break

        # command handler
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
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Group verify fail message updated.")
            print("Group verify fail message updated.")
        elif update.message.text.startswith('/groupwelcome approve'):
            new_user_verify = NewUserVerify()
            await new_user_verify.verify_twitter_user_name(update, context)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Verify pool cleared.")
            print("Verify pool cleared.")
        else:
            # default aka not recognized
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=usage_msg)

        # save config file
        if group not in welcome_msg_config:
            welcome_msg_config.append(group)
        else:
            welcome_msg_config[welcome_msg_config.index(group)] = group
        with open('welcome_msg_config.json', 'w', encoding='utf-8') as config_file:
            json.dump(welcome_msg_config, config_file, ensure_ascii=False, indent=4)


class NewUserVerify:
    # If a new user joins the group, send a welcome message
    WaitingForReply = 1
    verification_timeout = 300  # seconds
    new_user_data = {}

    async def send_group_welcome_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for new_member in update.message.new_chat_members:
            # get welcome message text from config
            # open file
            default_groupwelcome_config = {'groupid': update.effective_chat.id,
                                           'welcome': False,
                                           'message': 'Welcome {new_member_first_name} {new_member_last_name} to the Group!',
                                           'verify': False,
                                           'verify_filter': '.*',
                                           'verify_msg': 'Verification success!',
                                           'verify_fail_msg': 'Verification failed!'}

            try:
                with open('welcome_msg_config.json', 'r', encoding='utf-8') as file:
                    welcome_msg_config = json.load(file)
                if not welcome_msg_config:
                    welcome_msg_config = [default_groupwelcome_config]
            except Exception as e:
                welcome_msg_config = [default_groupwelcome_config]
                print(datetime.datetime.now(), "\t", "Error reading welcome_msg_config.json: ", e)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e) + "\nPlease contact the admin.")
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
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Error: " + str(e) + "\nPlease contact the admin.")
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

        if update.message.text and re.match(verify_filter, update.message.text) and user_data.get('NewUser', True):
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
            print(datetime.datetime.now(), "\t", f"User {new_member_id} has not verified their account in time.")
            # put your custom methods here
            # for example, I will call notify_admin from notifyAdmin.py
            notifyAdmin.notify_admin()
            timer_task = user_data.get('timer_task')
            if timer_task:
                timer_task.cancel()
            del self.new_user_data[userID]
        return

    async def clear_verify_pool(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(datetime.datetime.now(), "\t", "ClearVerifyPool Called")
        # clear all new user data
        self.new_user_data = {}
        print(datetime.datetime.now(), "\t", "User_data updated to: ", self.new_user_data)


# mark a crown emoji on the message if it contains '国行'
async def apple_cn_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🤡')


# random reply '羡慕' and fire reaction according to possibility
async def xm_and_fire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 50 50 羡慕 or fire
    if random.random() < 0.5:
        print(datetime.datetime.now(), "\t", "Replying 羡慕")
        try:
            await update.message.reply_text('羡慕')
        except AttributeError:
            pass
    else:
        print(datetime.datetime.now(), "\t", "Reacting 🔥")
        await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🔥')


# xm and fire settings handler
# I think this function should only process one group instead of reading all group configs
# form security aspect, this is not good and may cause data leak, but I don't want to fix it
async def xm_and_fire_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, xm_and_fire_filter_obj):
    print(datetime.datetime.now(), "\t", "Received " + update.message.text + ", ", end="")
    usage_msg = "Usage:\n/xmfire <on/off> Toggle xm and fire reaction.\n/xmfire set <possibility> Set xm and fire possibility in [0, 1].\n/xmfire suppress <minutes> Suppress this function for a period of time. (Not Finished Yet)"
    if update.effective_chat.type not in ['group', 'supergroup']:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="This command is only available in group.")
        print("Not a group chat.")
        return
    # if only /xmfire, show usage
    if update.message.text == '/xmfire':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=usage_msg)
        print("Showing usage")
    else:
        # only group admins can change the settings
        # if not admin, return
        if not (await update.effective_chat.get_member(update.effective_user.id)).status in ['administrator',
                                                                                             'creator']:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Only group admins can use this command.")
            return

        # read config file, locate current group and ready to edit
        xm_and_fire_possibilities = xm_and_fire_filter_obj.reload_config()

        # search for this group in config
        # if not found, use default group config, if found, use the found group config
        group = {'groupid': update.effective_chat.id,
                 'possibility': 0,
                 'enabled': False}
        for timer in xm_and_fire_possibilities:
            if timer['groupid'] == update.effective_chat.id:
                group = timer
                break

        # command handler
        if update.message.text == '/xmfire on':
            group['enabled'] = True
            await context.bot.send_message(chat_id=update.effective_chat.id, text="XM and Fire reaction enabled.")
            print("XM and Fire reaction enabled.")
        elif update.message.text == '/xmfire off':
            group['enabled'] = False
            await context.bot.send_message(chat_id=update.effective_chat.id, text="XM and Fire reaction disabled.")
            print("XM and Fire reaction disabled.")
        elif update.message.text.startswith('/xmfire set '):
            group['possibility'] = float(update.message.text.replace('/xmfire set ', ''))
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="XM and Fire possibility updated.")
            print("XM and Fire possibility updated.")
        else:
            # default aka not recognized
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=usage_msg)

        # save changes to list
        if group not in xm_and_fire_possibilities:
            xm_and_fire_possibilities.append(group)
        else:
            xm_and_fire_possibilities[xm_and_fire_possibilities.index(group)] = group

        # save config file
        xm_and_fire_filter_obj.save_config(xm_and_fire_possibilities)

        # reload config file
        xm_and_fire_filter_obj.reload_config()

# manual xm and fire handlers
async def manual_xm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received " + update.message.text + ", ", end="")
    usage_msg = "Usage: /xm <message link>\nOr reply a message with /xm."
    if update.message.reply_to_message:
        await update.message.reply_to_message.reply_text('羡慕')
        print("Replying 羡慕")
    else:
        if not re.match(r'^/xm https://t\.me/c/(\d+)/(\d+)$', update.message.text):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=usage_msg)
            print("Showing usage")
            return
        else:
            try:
                message_id = int(re.match(r'^/xm https://t\.me/c/(\d+)/(\d+)$', update.message.text).group(2))
                await context.bot.send_message(text='羡慕', chat_id=update.effective_chat.id, reply_to_message_id=message_id)
                print("Replying 羡慕")
            except Exception as e:
                print("Error: ", e)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e))

async def manual_fire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received " + update.message.text + ", ", end="")
    usage_msg = "Usage: /fire <message link>\nOr reply a message with /fire."
    if update.message.reply_to_message:
        await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.reply_to_message.message_id, reaction='🔥')
        print("Reacting 🔥")
    else:
        if not re.match(r'^/fire https://t\.me/c/(\d+)/(\d+)$', update.message.text):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=usage_msg)
            print("Showing usage")
            return
        else:
            try:
                message_id = int(re.match(r'^/fire https://t\.me/c/(\d+)/(\d+)$', update.message.text).group(2))
                await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=message_id, reaction='🔥')
                print("Reacting 🔥")
            except Exception as e:
                print("Error: ", e)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e))

# random reply a kind of food when calling /eattoday
async def what_to_eat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "What to eat today called.")
    # 5% chance trigger I EAT MYSELF
    chance_I_EAT_MYSELF = 0.05
    if random.random() < chance_I_EAT_MYSELF:
        await update.message.reply_text(
            "吃" + update.message.from_user.first_name + update.message.from_user.last_name + "！")
    else:
        # food = ['麻辣烫', '炒饭', '炒面', '炒粉', '炒河粉', '炒米粉', '炒土豆丝', '炒青菜', '炒西兰花', '炒芹菜', '炒莴笋', '炒豆角', '炒茄子']
        try:
            with open('foodlist.txt', 'r', encoding='utf-8') as food_list_file:
                food = [line.strip() for line in food_list_file.readlines()]
        except Exception as e:
            print(datetime.datetime.now(), "\t", "Error reading foodlist.txt: ", e)
            await update.message.reply_text("Error: " + str(e) + "\nPlease contact the admin.")

        await update.message.reply_text("吃" + random.choice(food) + "！")

# when bot mentioned inline, reply with quote
async def inline_query(update: Update, context):
    print(datetime.datetime.now(), "\t", "Calling inlineQuery")
    query = update.inline_query.query.strip()
    try:
        with open('quotes.json', 'r', encoding='utf-8') as f:
            loadedQuotes = json.load(f)
    except Exception as e:
        print(datetime.datetime.now(), "\t", "Error reading quotes.json: ", e)
        return
    # this would read the json everytime the query function called
    # which is not good, improvement will be needed but later
    # or it is good? because internet transfer is much slower than reading a file
    # maybe we would need buffer something like "most recent 10 quotes" or "quotes in the last 24 hours"
    # quotes = ['quote1', 'quote2', 'quote3']   # for debug only
    # search quotes according to user input
    filtered_quotes = sorted(
        loadedQuotes,
        key=lambda quote: (quote['quote'].count(query) + quote['speaker'].count(query)),
        reverse=True
    )

    results = []
    if "哎呀" in query:
        results += [(
            InlineQueryResultCachedSticker(
                id=str(uuid4()),
                sticker_file_id="CAACAgUAAxkBAAIBA2cgmvcwGcdCVA1HwwsnjALyL80-AAJdBAAC_9CJVsMSLkHioimoNgQ",

            )
        )]
    # todo: if start with >>, send everything behind as a message
    if re.match(r'^>>.*', query):
        output = query[2:]
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=output,
                description=".*",
                input_message_content=InputTextMessageContent(output)
            )
        ]
        try:
            await update.inline_query.answer(results)
        except Exception as e:
            # do nothing, it's not a bug. Inline query is triggered rapidly when you type custom message.
            print("Inline query triggered too fast: ", e)

    results.extend([
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=quote['quote'],  # the title
            description=quote['speaker'],  # the subtitle
            input_message_content=InputTextMessageContent(quote['quote'])  # the content user will send
        )
        for quote in filtered_quotes
    ])
    try:
        await update.inline_query.answer(results)
    except Exception as e:
        # do nothing, it's not a bug. Inline query is triggered rapidly when you type custom message.
        print("Inline query triggered too fast: ", e)

# download comic from jm and send to chat
async def jm_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Calling jm")
    await update.message.reply_text(f"Downloading comic {update.message.text.replace('/jm ', '')}...")
    comic_id = update.message.text.replace('/jm ', '')
    if not comic_id.isdigit():
        await update.message.reply_text("Usage: /jm <comic_id>")
        return
    try:
        await jm_comic_download(comic_id, update, context)
    except telegram.error.TimedOut:
        pass
    return

async def jm_comic_download(comic_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Downloading comic " + comic_id)
    pdf_file = download_comic(comic_id)
    print(datetime.datetime.now(), "\t", "Comic " + comic_id + " downloaded. Sending to chat...")
    await context.bot.send_document(chat_id=update.effective_chat.id, document=open(f"download/{pdf_file}", 'rb'))
    print(datetime.datetime.now(), "\t", "Comic " + comic_id + " sent to chat.")
    return

async def AI_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "AI chat called.")
    sys_prompt = '你正在和群组内的朋友们聊天，你乐于助人、活泼且言简意赅。你极其厌恶政治，所以当有人谈论到政治话题的时候（无论是世界上哪个地方的政治，或是历史中的政治），你都直接回复他们"咱不懂..."以搪塞过去。'
    usage_msg = "Usage: /llm <message>\nOr reply a message with /llm.\nAlso please aware that all chats are single-turn with no context saved."
    if update.message.reply_to_message:
        print(datetime.datetime.now(), "\t", "Asking: ", update.message.reply_to_message.text)
        feedback = fetch_from_AI("DS", sys_prompt, update.message.reply_to_message.text)
    else:
        if not re.match(r'^/llm .*', update.message.text):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=usage_msg)
            print("Showing usage")
            return
        else:
            print(datetime.datetime.now(), "\t", "Asking: ", update.message.text.replace('/llm ', ''))
            feedback = fetch_from_AI("DS", sys_prompt, update.message.text.replace('/llm ', ''))
    print(datetime.datetime.now(), "\t", "Chat response: ", feedback)
    feedback = f"结果由AI生成，可能不准确。\n{feedback}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=feedback, reply_to_message_id=update.message.message_id)
    print(datetime.datetime.now(), "\t Response sent.")


def main():
    application = ApplicationBuilder().token(botToken).build()

    # global function switches
    start_handler_switch = True
    sticker_handler_switch = True
    system_status_handler_switch = True
    apple_cn_msg_handler_switch = False
    what_to_eat_today_handler_switch = True
    jm_download_switch = True
    AI_chat_switch = True

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

    # jm comic handler
    if jm_download_switch:
        # remove download folder if exists
        if os.path.exists('download'):
            shutil.rmtree('download')
        jm_comic_handler = CommandHandler('jm', jm_comic)
        application.add_handler(jm_comic_handler)

    # AI chat handler
    if AI_chat_switch:
        AI_chat_handler = CommandHandler('llm', AI_chat)
        application.add_handler(AI_chat_handler)

    # group welcome message setting handler
    group_welcome_msg_handler = CommandHandler('groupwelcome', group_welcome_msg_settings)
    application.add_handler(group_welcome_msg_handler)

    # new user handler
    new_user_verify = NewUserVerify()
    newUserFilter = NewUserFilter()
    welcomeMSG_handler = ConversationHandler(
        entry_points=[MessageHandler(newUserFilter, new_user_verify.send_group_welcome_msg)],
        states={
            new_user_verify.WaitingForReply: [
                MessageHandler(
                    # if ((text && not command) || sticker || photo || animation)
                    (filters.TEXT & ~filters.COMMAND) | filters.Sticker.ALL | filters.PHOTO | filters.ANIMATION,
                    # call verify_twitter_user_name
                    new_user_verify.verify_twitter_user_name
                )]
        },
        fallbacks=[]
    )
    application.add_handler(welcomeMSG_handler)

    # xm and fire settings handler
    # create an object in order to use it in the following xm and fire handlers
    xm_and_fire_reaction_filter = XMAndFireReactionFilter()
    # read possibility for each group from xm_and_fire.json, this config file would be in the ram
    xm_and_fire_reaction_filter.reload_config()
    # pass the object to settings function
    xm_and_fire_settings_handler = CommandHandler('xmfire', partial(xm_and_fire_settings, xm_and_fire_filter_obj=xm_and_fire_reaction_filter))
    application.add_handler(xm_and_fire_settings_handler)

    # manual xm and fire handlers
    manual_xm_handler = CommandHandler('xm', manual_xm)
    application.add_handler(manual_xm_handler)
    manual_fire_handler = CommandHandler('fire', manual_fire)
    application.add_handler(manual_fire_handler)

    # xm and fire reaction handler
    # this handler must be put after all message handlers
    xm_and_fire_reaction_filter.reload_config()
    xm_and_fire_reaction_handler = MessageHandler(xm_and_fire_reaction_filter, xm_and_fire)
    application.add_handler(xm_and_fire_reaction_handler)

    # inline mentioned handler
    application.add_handler(InlineQueryHandler(inline_query))

    # start the bot
    print(datetime.datetime.now(), "\t", "All handlers are loaded. Starting the bot now...")
    application.run_polling()


if __name__ == '__main__':
    main()
