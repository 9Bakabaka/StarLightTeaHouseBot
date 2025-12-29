### By Longtail Amethyst Eralbrunia 2024-09-26
### Stop posting your shit to Internet
import datetime
import asyncio
import os
import shutil
import nest_asyncio

nest_asyncio.apply()  # for pycharm

from functools import partial
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, InlineQueryHandler
from dotenv import load_dotenv


# todo: 尾巴触电
# todo: add quote, print quote list and delete quote
# todo: verification timeout customize

async def main():
    load_dotenv()
    # load_dotenv('.env.test')
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # start handler
    from modules.start import start
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # system status handler
    from modules.start import system_status
    status_handler = CommandHandler('status', system_status)
    application.add_handler(status_handler)

    # for optional modules
    # if function enabled in .env
    #     load module and add handler
    # else
    #     add a handler to reply function not enabled message

    # sticker handler
    if os.getenv("ENABLE_STICKER_HANDLER").lower() == "true":
        from modules.stickers import get_sticker_id, StickerFilter
        stickerFilter = StickerFilter()
        sticker_handler = MessageHandler(stickerFilter, get_sticker_id)
        application.add_handler(sticker_handler)

    # apple CN message handler
    if os.getenv("ENABLE_APPLE_CN_MSG_HANDLER").lower() == "true":
        from modules.replies import AppleCNMSGFilter, apple_cn_msg
        appleCNMSGFilter = AppleCNMSGFilter()
        AppleCNMSG_handler = MessageHandler(appleCNMSGFilter, apple_cn_msg)
        application.add_handler(AppleCNMSG_handler)

    # jm comic handler
    if os.getenv("ENABLE_JM_DOWNLOAD").lower() == "true":
        from modules.jm import jm_comic
        # write absolute download path to jm_dl_option.yml
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(datetime.datetime.now(), "\t", "[main] Setting jmcomic download path to ",
              os.path.join(base_dir, "download", "cache"))
        with open(os.path.join(base_dir, 'config', 'jm_dl_option.yml'), 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(os.path.join(base_dir, 'config', 'jm_dl_option.yml'), 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith('base_dir:'):
                    f.write(f'  base_dir: "{os.path.join(base_dir, "download", "cache")}"\n')
                else:
                    f.write(line)
        jm_comic_handler = CommandHandler('jm', jm_comic)
    else:
        from modules.start import function_not_enabled
        jm_comic_handler = CommandHandler('jm', function_not_enabled)

    application.add_handler(jm_comic_handler)

    # AI chat handler
    if os.getenv("ENABLE_AI_CHAT").lower() == "true":
        from modules.LLM.chat import llm
        AI_chat_handler = CommandHandler('llm', llm)
    else:
        from modules.start import function_not_enabled
        AI_chat_handler = CommandHandler('llm', function_not_enabled)

    application.add_handler(AI_chat_handler)

    # group welcome message setting handler
    from modules.GroupWelcome.welcome_messages import NewUserVerify, NewUserFilter, group_welcome_msg_settings, new_user_verify_instance
    group_welcome_msg_handler = CommandHandler('groupwelcome', group_welcome_msg_settings)
    application.add_handler(group_welcome_msg_handler)

    # new user handler
    new_user_verify = new_user_verify_instance
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

    # captcha handler
    # if ... enabled, but not now
    from modules.GroupWelcome.captcha import captcha
    captcha_handler = CommandHandler('captcha', captcha)
    application.add_handler(captcha_handler)

    # xm and fire settings handler
    from modules.replies import XMAndFireReactionFilter, xm_and_fire, xm_and_fire_settings, WhatToEatFilter, what_to_eat, manual_xm, manual_fire, un_xm
    # create an object in order to use it in the following xm and fire handlers
    xm_and_fire_reaction_filter = XMAndFireReactionFilter()
    # read possibility for each group from config/xm_and_fire.json, this config file would be in the ram
    xm_and_fire_reaction_filter.reload_config()
    # pass the object to settings function
    xm_and_fire_settings_handler = CommandHandler('xianmufire', partial(xm_and_fire_settings,
                                                                        xm_and_fire_filter_obj=xm_and_fire_reaction_filter))
    application.add_handler(xm_and_fire_settings_handler)

    # manual xm and fire handlers
    manual_xm_handler = CommandHandler('xm', manual_xm)
    application.add_handler(manual_xm_handler)
    manual_fire_handler = CommandHandler('fire', manual_fire)
    application.add_handler(manual_fire_handler)
    un_xm_handler = CommandHandler('unxm', un_xm)
    application.add_handler(un_xm_handler)

    from modules.backdoor import backdoor, backdoor_del
    backdoor_handler = CommandHandler('bd', backdoor)
    application.add_handler(backdoor_handler)
    backdoor_delete_handler = CommandHandler('bddel', backdoor_del)
    application.add_handler(backdoor_delete_handler)

    # message handlers at the end
    # what to eat today handler
    if os.getenv("ENABLE_WHAT_TO_EAT").lower() == "true":
        what_to_eat_filter = WhatToEatFilter()
        what_to_eat_handler = MessageHandler(what_to_eat_filter, what_to_eat)
    else:
        from modules.start import function_not_enabled
        what_to_eat_handler = CommandHandler('eattoday', function_not_enabled)

    application.add_handler(what_to_eat_handler)

    # denno mienmien mao handler
    if os.getenv("ENABLE_DINNO_MIENMIEN_MAO_HANDLER").lower() == "true":
        from modules.replies import DennoMienmienMaoFilter, denno_mienmien_mao_nonnon
        denno_mienmien_mao_filter = DennoMienmienMaoFilter()
        dinno_mienmien_mao_handler = MessageHandler(denno_mienmien_mao_filter, denno_mienmien_mao_nonnon)
        application.add_handler(dinno_mienmien_mao_handler)

    # xm and fire reaction handler
    # this handler must be put after all message handlers
    xm_and_fire_reaction_filter.reload_config()
    xm_and_fire_reaction_handler = MessageHandler(xm_and_fire_reaction_filter, xm_and_fire)
    application.add_handler(xm_and_fire_reaction_handler)

    # inline mentioned handler
    from modules.inline import inline_query
    application.add_handler(InlineQueryHandler(inline_query))

    from telegram.error import TimedOut
    while True:
        try:
            # clear received message before bot starts
            print(datetime.datetime.now(), "\t", "[main] Clearing received messages...")
            await application.bot.get_updates(offset=-1)

            # start the bot
            print(datetime.datetime.now(), "\t", "[main] All handlers are loaded. Starting the bot now...")
            await application.run_polling(
                timeout=30,
            )
        except TimedOut:
            print(datetime.datetime.now(), "\t", "[main] Timed out.")
            pass  # My connection is really really really bad.


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Cannot close a running event loop" in str(e):
            # For environments with existing event loops (like PyCharm)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
