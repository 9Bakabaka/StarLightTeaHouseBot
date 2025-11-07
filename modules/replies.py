import datetime
import random
import re
import json
import os

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext.filters import MessageFilter

# Get the base directory (two levels up from this file)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# '国行' reaction filter
class AppleCNMSGFilter(MessageFilter):
    def filter(self, message):
        if message.text and ('国行' in message.text or '國行' in message.text):
            return True
        return False

# mark a crown emoji on the message if it contains '国行'
async def apple_cn_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🤡')


# \non non/! filter
class DennoMienmienMaoFilter(MessageFilter):
    def filter(self, message):
        if message.text and re.match(r'电.*脑.*眠.*眠.*猫', message.text):
            return True
        return False

# \non non!/
async def denno_mienmien_mao_nonnon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "[replies] Received 电脑眠眠猫.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="\\non non!/")


class WhatToEatFilter(MessageFilter):
    def filter(self, message):
        if message.text:
            if '/eattoday' in message.text:
                return 1
            if re.search(r'今天吃什么|等会吃什么|早上吃什么|中午吃什么|下午吃什么|晚上吃什么|饿了(?!么)|好饿|饿饿', message.text):
                return 1
            return None
        return None

# random reply a kind of food when calling /eattoday
async def what_to_eat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "[replies] What to eat today called.")
    # 5% chance trigger I EAT MYSELF
    chance_I_EAT_MYSELF = 0.05
    if random.random() < chance_I_EAT_MYSELF:
        await update.message.reply_text(
            "吃" + update.message.from_user.first_name + update.message.from_user.last_name + "！")
    else:
        # food = ['麻辣烫', '炒饭', '炒面', '炒粉', '炒河粉', '炒米粉', '炒土豆丝', '炒青菜', '炒西兰花', '炒芹菜', '炒莴笋', '炒豆角', '炒茄子']
        try:
            foodlist_path = os.path.join(base_dir, 'config', 'foodlist.txt')
            with open(foodlist_path, 'r', encoding='utf-8') as food_list_file:
                food = [line.strip() for line in food_list_file.readlines()]
        except Exception as e:
            print(datetime.datetime.now(), "\t", "[replies] Error reading foodlist.txt: ", e)
            await update.message.reply_text("Error: " + str(e) + "\nPlease contact the admin.")

        await update.message.reply_text("吃" + random.choice(food) + "！")


# xm and fire possibility filter
class XMAndFireReactionFilter(MessageFilter):
    # get possibility from the global array xm_and_fire_possibility
    # define before use, typical c++ style, aha-aha
    possibility_list = None

    class GroupConfig:
        def __init__(self, groupid=None, possibility=0, enabled=False, suppress_until=None):
            self.groupid = groupid
            self.possibility = possibility
            self.enabled = enabled
            self.suppress_until = suppress_until

        @classmethod
        def from_dict(cls, data):
            # Create GroupConfig from dictionary
            # Convert Unix timestamp to datetime
            suppress_until = data.get('suppress_until', None)
            if suppress_until is not None:
                suppress_until = datetime.datetime.fromtimestamp(suppress_until)
            return cls(
                groupid=data.get('groupid', None),
                possibility=data.get('possibility', 0),
                enabled=data.get('enabled', False),
                suppress_until=suppress_until
            )

        def to_dict(self):
            # Convert GroupConfig to dictionary
            # Convert datetime to Unix timestamp
            suppress_until = None
            if self.suppress_until is not None:
                suppress_until = int(self.suppress_until.timestamp())
            return {
                    'groupid': self.groupid,
                    'possibility': self.possibility,
                    'enabled': self.enabled,
                    'suppress_until': suppress_until
                }

        def suppress_for(self, minutes):
            self.suppress_until = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

        def is_suppressed(self):
            if self.suppress_until is None:
                return False
            return datetime.datetime.now() < self.suppress_until

    # reload the config file and return the possibility list
    def reload_config(self):
        try:
            config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
            with open(config_path, 'r', encoding='utf-8') as config_file:
                json_data = json.load(config_file)
                # Convert JSON data to GroupConfig objects
                self.possibility_list = [self.GroupConfig.from_dict(item) for item in json_data]
        except FileNotFoundError:
            self.possibility_list = []
            config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
            with open(config_path, 'w', encoding='utf-8') as config_file:
                json.dump(self.possibility_list, config_file, ensure_ascii=False, indent=4)
        return self.possibility_list

    def save_config(self, xm_and_fire_possibility):
        config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
        with open(config_path, 'w', encoding='utf-8') as file:
            # Convert GroupConfig objects to dict if needed
            if xm_and_fire_possibility and isinstance(xm_and_fire_possibility[0], self.GroupConfig):
                json_data = [group.to_dict() for group in xm_and_fire_possibility]
            else:
                json_data = xm_and_fire_possibility
            json.dump(json_data, file, ensure_ascii=False, indent=4)


    def filter(self, message):
        # Load config if not loaded
        if self.possibility_list is None:
            self.reload_config()

        # Find group config for this chat
        group = None
        for g in self.possibility_list:
            if g.groupid == message.chat.id:
                group = g
                break

        # If group not found, create and save new config
        if group is None:
            group = self.GroupConfig(
                groupid=message.chat.id,
                possibility=0,
                enabled=False,
                suppress_until=None
            )
            self.possibility_list.append(group)
            self.save_config(self.possibility_list)
            return False

        # Check if enabled and not suppressed
        if not group.enabled or group.is_suppressed():
            return False

        # if time < suppress_until, return False
        if group.is_suppressed():
            return False

        # Learning C++ would ruin your Python code style aha
        # return random_result < self.possibility ? 1 : 0
        return True if random.random() < group.possibility else False

# random reply '羡慕' and fire reaction according to possibility
async def xm_and_fire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 50 50 羡慕 or fire
    if random.random() < 0.5:
        print(datetime.datetime.now(), "\t", "[replies] Replying 羡慕")
        try:
            await update.message.reply_text('羡慕')
        except AttributeError:  # when message is edited, it would call AttributeError, but it's OK
            pass
    else:
        print(datetime.datetime.now(), "\t", "[replies] Reacting 🔥")
        await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🔥')

# xm and fire settings handler
# I think this function should only process one group instead of reading all group configs
# form security aspect, this is not good and may cause data leak, but I don't want to fix it
async def xm_and_fire_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, xm_and_fire_filter_obj):
    print(datetime.datetime.now(), "\t", "[replies] Received " + update.message.text + ", ", end="")
    usage_msg = ("Usage:\n"
                 "/xianmufire <on/off> Toggle xm and fire reaction.\n"
                 "/xianmufire set <possibility> Set xm and fire possibility in [0, 1].\n"
                 "/xianmufire % Show current settings.\n"
                 "/xianmufire suppress <minutes> Suppress this function for a period of time.")
    if update.effective_chat.type not in ['group', 'supergroup']:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="This command is only available in group.")
        print("Not a group chat.")
        return
    # if only /xmfire, show usage
    if update.message.text == '/xianmufire':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=usage_msg)
        print(datetime.datetime.now(), "\t", "[replies] Received " + update.message.text + ", ", end="")
        return

    # only group admins can change the settings
    # if not admin, return
    if not (await update.effective_chat.get_member(update.effective_user.id)).status in ['administrator',
                                                                                         'creator']:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Only group admins can use this command.")
        print("Not admin. Return now.")
        return

    # read config file, locate current group and ready to edit
    xm_and_fire_possibilities = xm_and_fire_filter_obj.reload_config()

    # search for this group in config
    # if not found, use default group config, if found, use the found group config
    group = None
    for timer in xm_and_fire_possibilities:
        if timer.groupid == update.effective_chat.id:
            group = timer
            break

    # If group not found, create a new one with default values
    if group is None:
        group = xm_and_fire_filter_obj.GroupConfig(
            groupid=update.effective_chat.id,
            possibility=0,
            enabled=False,
            suppress_until=None
        )

    command = update.message.text.replace('/xianmufire ', '')
    # command handler
    if command == 'on':
        group.enabled = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text="XM and Fire reaction enabled.")
        print("XM and Fire reaction enabled.")
    elif command == 'off':
        group.enabled = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text="XM and Fire reaction disabled.")
        print("XM and Fire reaction disabled.")
    elif command.startswith('set'):
        group.possibility = float(command.replace('set ', ''))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="XM and Fire possibility updated.")
        print("\t", "XM and Fire possibility updated.")
    elif command == '%':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current XM and Fire possibility: {group.possibility}\nEnabled: {group.enabled}")
        print("Showing current settings.")
    elif command.startswith('suppress'):
        supress_time = int(command.replace('suppress ', ''))
        group.suppress_for(supress_time)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"XM and Fire reaction suppressed for {supress_time} minutes.")
        print(f"XM and Fire reaction suppressed for {supress_time} minutes.")
    else:
        # default aka not recognized
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=usage_msg)
        print("Command not recognized. Showing usage")

    # save changes to list
    if group not in xm_and_fire_possibilities:
        xm_and_fire_possibilities.append(group)
    else:
        # Update the existing group in the list
        for i, g in enumerate(xm_and_fire_possibilities):
            if g.groupid == group.groupid:
                xm_and_fire_possibilities[i] = group
                break

    # save config file
    xm_and_fire_filter_obj.save_config(xm_and_fire_possibilities)

    # reload config file
    xm_and_fire_filter_obj.reload_config()

# manual xm and fire handlers
async def manual_xm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "[replies] Received " + update.message.text + ", ", end="")
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
    print(datetime.datetime.now(), "\t", "[replies] Received " + update.message.text + ", ", end="")
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

async def un_xm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "[replies] Received /unxm, ", end="")
    usage_msg = "Usage: /unxm <message link>\nOr reply a message with /unxm."
    if update.message.reply_to_message:
        await delete_xm_msg(context, update.effective_chat.id, update.message.reply_to_message)
        return
    else:
        if not re.match(r'^/xm https://t\.me/c/(\d+)/(\d+)$', update.message.text):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=usage_msg)
            print("Showing usage")
            return
        else:
            try:
                message_id = int(re.match(r'^/xm https://t\.me/c/(\d+)/(\d+)$', update.message.text).group(2))
                await delete_xm_msg(context, update.effective_chat.id, context.bot.get_message(chat_id=update.effective_chat.id, message_id=message_id))
            except Exception as e:
                print("Error: ", e)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Error: " + str(e))

# message: the message that is about to be deleted
async def delete_xm_msg(context, chat_id, message):
    # All prints in this function would be attached to the message from function un_xm, so no datetime or prefix needed.
    if message.from_user.id != context.bot.id:
        print("Not bot's message.")
        await context.bot.send_message(chat_id=chat_id, text="Bot can only remove its own message.")
        return
    if message.text != '羡慕':
        print("Not a 羡慕 message.")
        await context.bot.send_message(chat_id=chat_id, text="This message is not 羡慕.")
        return
    await context.bot.delete_message(chat_id=chat_id, message_id=message.id)
    print("Deleting 羡慕")
