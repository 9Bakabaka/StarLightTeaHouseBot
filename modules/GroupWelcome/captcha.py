import datetime
import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler, filters

from modules.LLM.fetch_LLM import LLM

# Track users currently undergoing captcha (per chat & user)
_captcha_inflight = set()

# use llm to get a captcha question
async def captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    key = (chat_id, user_id)

    # If a captcha is already in progress for this user in this chat, do not start another
    if key in _captcha_inflight:
        await context.bot.send_message(
            chat_id=chat_id,
            text="You already have an active captcha. Please answer the previous question or wait for it to timeout.",
            reply_to_message_id=update.message.message_id,
        )
        return

    # Mark as in-flight and launch the worker
    _captcha_inflight.add(key)
    asyncio.create_task(captcha_thread(update, context))


# Helper: wait for a text reply from the same user in the same chat, with a timeout
async def wait_for_user_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, timeout: int = 300) -> Update:
    """Wait for a text message from the same user in the same chat, with a timeout (seconds)."""
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()

    async def _catcher(u: Update, c: ContextTypes.DEFAULT_TYPE):
        # Only accept messages from the same chat & same user, and ensure their text.
        if (
            u.effective_chat
            and u.effective_user
            and u.effective_chat.id == update.effective_chat.id
            and u.effective_user.id == update.effective_user.id
            and u.message
            and u.message.text is not None
        ):
            if not future.done():
                future.set_result(u)

    # Register a one-off handler to capture the next text message from this user in this chat
    handler = MessageHandler(
        filters.Chat(update.effective_chat.id)
        & filters.User(update.effective_user.id)
        & filters.TEXT
        & ~filters.COMMAND,
        _catcher,
    )

    # Use a high group index so we don't interfere with other handlers
    context.application.add_handler(handler, group=99999)

    try:
        # Wait for the next message or time out
        return await asyncio.wait_for(future, timeout=timeout)
    finally:
        # Always remove the temporary handler
        context.application.remove_handler(handler, group=99999)

async def captcha_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    key = (chat_id, user_id)

    sent = await context.bot.send_message(
        chat_id=chat_id,
        text=f"Please complete the captcha in 300 seconds:\nGenerating captcha, please wait...",
        reply_to_message_id=update.message.message_id,
    )

    try:
        user_message = ""
        print(datetime.datetime.now(), "\t", "[captcha] User answered:", user_message)
        sys_prompt = (
            "You are a helpful assistant that generates a question with average difficulty to verify if the user is human. "
            "Provide only the question without any additional text. "
        )
        usr_prompt = "After user response you should verify the answer by only responding with 'T' or 'F'."

        # fetch from LLM (offload sync calls to a thread to avoid blocking the event loop)
        llm = LLM(sys_prompt)
        captcha_title = await asyncio.to_thread(llm.multi_round_chat, usr_prompt)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            text=f"Please complete the captcha in 300 seconds:\n{captcha_title}",
            message_id=sent.message_id,
        )
        print(datetime.datetime.now(), "\t", "[captcha] User answered:", user_message)

        # Wait for the user's next text message (same chat & same user) with a 300s timeout
        try:
            user_update = await wait_for_user_reply(update, context, timeout=300)
        except asyncio.TimeoutError:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Captcha timeout! No answer received within 300 seconds.",
                reply_to_message_id=sent.message_id,
            )
            print(datetime.datetime.now(), "\t", "[captcha] User answered:", user_message)
            return

        user_message = user_update.message.text or ""
        print(datetime.datetime.now(), "\t", "[captcha] User answered:", user_message)

        # Add user answer to message history and get verification result (again offload sync call)
        llm.add_message("user", user_message)
        verification_result = await asyncio.to_thread(llm.send_payload)

        if str(verification_result).strip().upper().startswith("T"):
            await context.bot.send_message(
                chat_id=chat_id,
                text="Captcha passed! You are verified as human.",
                reply_to_message_id=sent.message_id,
            )
            # handle user passed

        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Captcha failed! You are not verified as human.",
                reply_to_message_id=sent.message_id,
            )
            # handle user failed

    finally:
        # Ensure we clear the in-flight flag even if exceptions/timeouts happen
        _captcha_inflight.discard(key)
