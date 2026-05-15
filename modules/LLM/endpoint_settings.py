import json
import os
import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'llm_endpoints.json')

from telegram import Update
from telegram.ext import ContextTypes

def _get_admin_list():
    return [admin_id.strip() for admin_id in os.getenv("ADMIN_LIST", "").split(",") if admin_id.strip()]

class endpoints:
    def __init__(self) -> None:
        # read /config/llm_endpoints.json
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                llm_endpoints_list = json.load(f)

            # get current model
            current_model = llm_endpoints_list.get("current_model")

            # find matched endpoint by alias
            matched = None
            for ep in llm_endpoints_list.get("endpoints", []):
                if ep.get("alias") == current_model:
                    matched = ep
                    break

            if matched is None:
                print(datetime.datetime.now(), "\t", f"[modules.LLM.endpoint_settings.endpoints] No endpoint matched for current_model: {current_model}")
                return

        except Exception as e:
            print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.endpoints] Error reading llm_endpoints.json: ", e)
            return

        self.base_url = matched.get("base_url")
        self.model = matched.get("model")
        self.api_key = matched.get("api_key")
        self.type = matched.get("type")


# /llminfo
async def llminfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings] Received " + update.message.text + ", ", end="")
    usage_msg = ("Usage:\n"
                 "/llminfo -- Show available LLM list and LLM currently using.\n"
                 "/llminfo set <model alias> -- Set LLM to use.")
    # /llminfo, output
    if update.message.text == "/llminfo":
        print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.llminfo] /llminfo called")
        # get llm endpoint list, add " <current>" after the model currently using
        endpoint_list_for_printing = []
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_model = data.get("current_model")
                for ep in data.get("endpoints", []):
                    alias = ep.get("alias")
                    if alias == current_model:
                        endpoint_list_for_printing.append(f"{alias} <current>")
                    else:
                        endpoint_list_for_printing.append(alias)
        except Exception as e:
            print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.llminfo] Error reading llm_endpoints.json: ",
                  e)

        message_for_printing = "\n".join(endpoint_list_for_printing)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Available models:\n" + message_for_printing)
        return

    if update.message.text.startswith("/llminfo set"):
        print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.llminfo] /llminfo set called")

        if str(update.message.from_user.id) not in _get_admin_list():
            print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.llminfo] Not Longtail.")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Only Longtail can perform this operation.")
            return

        change_current_model_to = update.message.text.replace("/llminfo set", "").strip()

        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.llminfo] Error reading llm_endpoints.json: ", e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to read config file.")
            return

        # collect all aliases
        aliases = [ep.get("alias") for ep in data.get("endpoints", [])]

        if change_current_model_to not in aliases:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Model '{change_current_model_to}' not found.")
            return

        # update current_model
        data["current_model"] = change_current_model_to

        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(datetime.datetime.now(), "\t", "[modules.LLM.endpoint_settings.llminfo] Error writing llm_endpoints.json: ",
                  e)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to update config file. Please contact administrator.")
            return

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Current model set to: {change_current_model_to}")
        return

    else:
        # default aka not recognized
        await context.bot.send_message(chat_id=update.effective_chat.id, text=usage_msg)

