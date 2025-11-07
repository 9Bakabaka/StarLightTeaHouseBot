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
    print(datetime.datetime.now(), "\t", "Received 电脑眠眠猫.")
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
    print(datetime.datetime.now(), "\t", "What to eat today called.")
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
            print(datetime.datetime.now(), "\t", "Error reading foodlist.txt: ", e)
            await update.message.reply_text("Error: " + str(e) + "\nPlease contact the admin.")

        await update.message.reply_text("吃" + random.choice(food) + "！")


# xm and fire possibility filter
class XMAndFireReactionFilter(MessageFilter):
    # get possibility from the global array xm_and_fire_possibility
    # define before use, typical c++ style, aha-aha
    enabled = 0
    possibility = 0
    possibility_list = None

    # reload the config file and return the possibility list
    def reload_config(self):
        try:
            config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
            with open(config_path, 'r', encoding='utf-8') as config_file:
                self.possibility_list = json.load(config_file)
        except FileNotFoundError:
            self.possibility_list = []
            config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
            with open(config_path, 'w', encoding='utf-8') as config_file:
                json.dump(self.possibility_list, config_file, ensure_ascii=False, indent=4)
        return self.possibility_list

    def save_config(self, xm_and_fire_possibility):
        config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
        with open(config_path, 'w', encoding='utf-8') as file:
            json.dump(xm_and_fire_possibility, file, ensure_ascii=False, indent=4)

    def filter(self, message):
        # try to get possibility from possibility list
        self.enabled = False
        try:
            for group in self.possibility_list:
                if group['groupid'] == message.chat.id:
                    self.enabled = group['enabled']
                    self.possibility = group['possibility']
        except KeyError:  # if not found, set possibility to 0
            self.possibility = 0
            self.possibility_list[message.chat.id] = {'groupid': message.chat.id, 'possibility': 0, 'enabled': False}
            # save change to file
            config_path = os.path.join(base_dir, 'config', 'xm_and_fire.json')
            with open(config_path, 'w', encoding='utf-8') as config_file:
                json.dump(self.possibility_list, config_file, ensure_ascii=False, indent=4)
            # reload the file
            with open(config_path, 'r', encoding='utf-8') as config_file:
                self.possibility_list = json.load(config_file)
            return False

        # if not enabled, return False
        if not self.enabled:
            return False
        # return random_result < self.possibility ? 1 : 0
        return True if random.random() < self.possibility else False

# random reply '羡慕' and fire reaction according to possibility
async def xm_and_fire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 50 50 羡慕 or fire
    if random.random() < 0.5:
        print(datetime.datetime.now(), "\t", "Replying 羡慕")
        try:
            await update.message.reply_text('羡慕')
        except AttributeError:  # when message is edited, it would call AttributeError, but it's OK
            pass
    else:
        print(datetime.datetime.now(), "\t", "Reacting 🔥")
        await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🔥')

# xm and fire settings handler
# I think this function should only process one group instead of reading all group configs
# form security aspect, this is not good and may cause data leak, but I don't want to fix it
async def xm_and_fire_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, xm_and_fire_filter_obj):
    print(datetime.datetime.now(), "\t", "Received " + update.message.text + ", ", end="")
    usage_msg = "Usage:\n/xianmufire <on/off> Toggle xm and fire reaction.\n/xmfire set <possibility> Set xm and fire possibility in [0, 1].\n/xmfire suppress <minutes> Suppress this function for a period of time. (Not Finished Yet)"
    if update.effective_chat.type not in ['group', 'supergroup']:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="This command is only available in group.")
        print("Not a group chat.")
        return
    # if only /xmfire, show usage
    if update.message.text == '/xianmufire':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=usage_msg)
        print(datetime.datetime.now(), "\t", "Received " + update.message.text + ", ", end="")
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
    group = {'groupid': update.effective_chat.id,
             'possibility': 0,
             'enabled': False,
             'supress_until': None
             }
    for timer in xm_and_fire_possibilities:
        if timer['groupid'] == update.effective_chat.id:
            group['groupid'] = timer.get('groupid', update.effective_chat.id)
            group['possibility'] = timer.get('possibility', 0)
            group['enabled'] = timer.get('enabled', False)
            group['supress_until'] = timer.get('supress_until', None)
            break

    command = update.message.text.replace('/xianmufire ', '')
    # command handler
    if command == 'on':
        group['enabled'] = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text="XM and Fire reaction enabled.")
        print("XM and Fire reaction enabled.")
    elif command == 'off':
        group['enabled'] = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text="XM and Fire reaction disabled.")
        print("XM and Fire reaction disabled.")
    elif command.startswith('set'):
        group['possibility'] = float(command.replace('set ', ''))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="XM and Fire possibility updated.")
        print("\t", "XM and Fire possibility updated.")
    elif command == '%':
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current XM and Fire possibility: {group['possibility']}\nEnabled: {group['enabled']}")
        print("Showing current settings.")
    elif command.startswith('supress'):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="This function is not finished yet.")
        print("Suppress function not finished yet.")
    else:
        # default aka not recognized
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=usage_msg)
        print("Command not recognized. Showing usage")

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

async def un_xm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "Received /unxm, ", end="")
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
