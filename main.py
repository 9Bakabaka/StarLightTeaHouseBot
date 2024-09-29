### By Longtail Amethyst Eralbrunia 2024-09-26
### Stop posting your shit to Internet

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters
from telegram.ext.filters import MessageFilter

# import token from file
with open('bottoken', 'r', encoding='utf-8') as file:
    botToken = file.read().replace('\n', '')


# print(botToken)

# '国行' reaction filter
class AppleCNMSGFilter(MessageFilter):
    def filter(self, message):
        if message.text:
            return '国行' in message.text


# new user filter
class NewUserFilter(MessageFilter):
    def filter(self, message):
        return message.new_chat_members


# start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Nya")


# If a new user joins the group, send a welcome message
WaitingForReply = 1


async def SendGroupWelcomeMSG(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        context.user_data[new_member.id] = {'NewUser': True}
        print("Sending welcome message to new user.")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"@{new_member.username}\n"
                 f"{new_member.first_name or ''} {new_member.last_name or ''} Welcome to the group!\n"
                 f"Please provide your twitter account(@username) in order to verify your identity."
                 f"You shall only type @yourID into the chat box. But not like 'I am yourID'."
        )
    return WaitingForReply


async def VerifyTwitterUserName(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("VerifyTwitterUserName Called")
    userID = update.message.from_user.id
    userData = context.user_data.get(userID, {})
    if update.message.text.startswith('@') and userData.get('NewUser', True):
        print("Updating NewUser to false.")
        userData.update({'NewUser': False})
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Your twitter account is verifying... Please wait for group admin to verify your identity."
        )
        return ConversationHandler.END


# mark a crown emoji on the message if it contains '国行'
async def AppleCNMSG(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_message_reaction(update.effective_chat.id, update.message.message_id, '🤡')


if __name__ == '__main__':
    application = ApplicationBuilder().token(botToken).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    appleCNMSGFilter = AppleCNMSGFilter()
    AppleCNMSG_handler = MessageHandler(appleCNMSGFilter, AppleCNMSG)
    application.add_handler(AppleCNMSG_handler)

    newUserFilter = NewUserFilter()
    welcomeMSG_handler = ConversationHandler(
        entry_points=[MessageHandler(newUserFilter, SendGroupWelcomeMSG)],
        states={
            WaitingForReply: [MessageHandler(filters.TEXT & ~filters.COMMAND, VerifyTwitterUserName)]
        },
        fallbacks=[]
    )
    application.add_handler(welcomeMSG_handler)

    application.run_polling()
