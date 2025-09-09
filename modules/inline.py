import datetime
import json
import re
import os

from uuid import uuid4
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineQueryResultCachedSticker

# when bot mentioned inline, reply with quote
async def inline_query(update: Update, context):
    print(datetime.datetime.now(), "\t", "Calling inlineQuery")
    query = update.inline_query.query.strip()
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'quotes.json'), 'r', encoding='utf-8') as f:
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
    # If start with >>, send everything behind as a user custom quote
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
