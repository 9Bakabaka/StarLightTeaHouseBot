import asyncio
import datetime
import json
import re

from telegram import Update
from telegram.ext import ContextTypes,ConversationHandler
from telegram.ext.filters import MessageFilter
import notify_admin

class NewUserFilter(MessageFilter):
    def filter(self, message):
        if message.new_chat_members:
            for user in message.new_chat_members:
                if user.id == message.from_user.id:
                    return True
        return False

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
                with open('../../config/welcome_msg_config.json', 'r', encoding='utf-8') as file:
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
            with open('../../config/welcome_msg_config.json', 'r', encoding='utf-8') as file:
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
            # for example, I will call notify_admin from notify_admin.py
            notify_admin.notify_admin()
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

# group welcome message setting handler
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
            with open('../../config/welcome_msg_config.json', 'r', encoding='utf-8') as file:
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
        with open('../../config/welcome_msg_config.json', 'w', encoding='utf-8') as config_file:
            json.dump(welcome_msg_config, config_file, ensure_ascii=False, indent=4)

