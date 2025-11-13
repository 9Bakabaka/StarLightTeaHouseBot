import os
import datetime

from openai import OpenAI, APIStatusError


class LLM:
    client = None
    model = "deepseek-chat"  # Make it static for now
    base_url = "https://api.deepseek.com"
    # [{"role": "system", "content": sys_prompt},
    # {"role": "user", "content": user_prompt},
    # {"role": "assistant", "content": "response"}]
    stream = False

    def __init__(self, sys_prompt=None):
        self.messages = []
        self.messages.append({"role": "system", "content": sys_prompt})
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=self.base_url)

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def get_payload(self):
        return {
            "model": self.model,
            "messages": self.messages,
            "stream": self.stream
        }

    def get_last_assistant_message(self):
        for message in reversed(self.messages):
            if message["role"] == "assistant":
                return message["content"]
        return None

    # send payload would add the assistant message to messages
    def send_payload(self):
        print(datetime.datetime.now(), "\t", "[fetch_LLM.send_payload] send_payload called.")
        response = None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=self.stream
            )
            if not response:
                print(datetime.datetime.now(), "\t", "[fetch_LLM.send_payload] Error: Response is None.")
                return "Error"

            print(datetime.datetime.now(), "\t", "[fetch_LLM.send_payload] response message:", response.choices[0].message.content)
            content = response.choices[0].message.content
            self.add_message("assistant", content)
            return content
        except APIStatusError as e:  # handle APIStatusError
            if e.status_code == 402:
                print(datetime.datetime.now(), "\t", "[fetch_LLM.send_payload] Error: Insufficient Balance")
            else:
                print(datetime.datetime.now(), "\t", f"[fetch_LLM.send_payload] Error: APIStatusError: {e}")
            return "Error"

    def multi_round_chat(self, user_prompt):
        response = None
        self.add_message("user", user_prompt)
        # send payload
        response = self.send_payload()
        return self.get_last_assistant_message()
