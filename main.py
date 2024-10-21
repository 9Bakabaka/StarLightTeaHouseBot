### By Longtail Amethyst Eralbrunia 2024-09-26
### Stop posting your shit to Internet
import json
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters, InlineQueryHandler
from telegram.ext.filters import MessageFilter


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


# when bot mentioned inline, reply with quote
async def inlineQuery(update: Update, context):
    print("Calling inlineQuery")
    query = update.inline_query.query.strip()
    if not query:
        # default result: when user inputs nothing
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title='Nya',    # the title
                input_message_content=InputTextMessageContent('Nya')    # the content user will send
            )
        ]
        await update.inline_query.answer(results)
        return

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
    if not filtered_quotes:     # if quote not found
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title='No matching quotes found nya',
                input_message_content=InputTextMessageContent('')
            )
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=quote['quote'],  # the title
                description=quote['speaker'],   # the subtitle
                input_message_content=InputTextMessageContent(quote['quote'])  # the content user will send
            )
            for quote in filtered_quotes
        ]
    await update.inline_query.answer(results)


def main():
    application = ApplicationBuilder().token(botToken).build()
    # start handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # apple CN message handler
    appleCNMSGFilter = AppleCNMSGFilter()
    AppleCNMSG_handler = MessageHandler(appleCNMSGFilter, AppleCNMSG)
    application.add_handler(AppleCNMSG_handler)

    # new user handler
    newUserFilter = NewUserFilter()
    welcomeMSG_handler = ConversationHandler(
        entry_points=[MessageHandler(newUserFilter, SendGroupWelcomeMSG)],
        states={
            WaitingForReply: [MessageHandler(filters.TEXT & ~filters.COMMAND, VerifyTwitterUserName)]
        },
        fallbacks=[]
    )
    application.add_handler(welcomeMSG_handler)

    # inline mentioned handler
    application.add_handler(InlineQueryHandler(inlineQuery))

    # start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
