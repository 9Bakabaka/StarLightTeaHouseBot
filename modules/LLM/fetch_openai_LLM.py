from modules.LLM.endpoint_settings import endpoints
import os
import datetime
from openai import OpenAI, APIStatusError

# from liulianmao import openai_chat_completion

class openai_request:
    def __init__(self, endpoint: endpoints, sys_prompt=""):
        if endpoint.type != "openai":
            print(datetime.datetime.now(), "\t", "[fetch_openai_LLM] Error: Trying to fetch a non-openai endpoint.")
        self.model = endpoint.model
        self.base_url = endpoint.base_url
        self.stream = False
        self.messages = []
        self.messages.append({"role": "system", "content": sys_prompt})
        self.client = OpenAI(api_key=endpoint.api_key, base_url=self.base_url)

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
        return ""

    # send payload would add the assistant message to messages
    def send_payload(self):
        print(datetime.datetime.now(), "\t", "[modules.fetch_openai_LLM.send_payload] send_payload called.")
        response = None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=self.stream,
                extra_body={
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": "medium"
                }
            )
            if not response:
                print(datetime.datetime.now(), "\t", "[modules.fetch_openai_LLM.send_payload] Error: Response is Empty.")
                return "Error: Response is Empty"

            print(datetime.datetime.now(), "\t", "[modules.fetch_openai_LLM.send_payload] response message:", response.choices[0].message.content)
            content = response.choices[0].message.content
            self.add_message("assistant", content)
            return content
        except APIStatusError as e:  # handle APIStatusError
            if e.status_code == 402:
                print(datetime.datetime.now(), "\t", "[modules.fetch_openai_LLM.send_payload] Error: Insufficient Balance")
                return "Error: Insufficient Balance"
            else:
                print(datetime.datetime.now(), "\t", f"[modules.fetch_openai_LLM.send_payload] Error: APIStatusError: {e}")
                return f"Error: APIStatusError: {e}"
        
        # return openai_chat_completion(prompt_question=self.messages,prompt_system="",model=self.model)

    def multi_round_chat(self, user_prompt):
        self.add_message("user", user_prompt)
        # send payload
        response = self.send_payload()
        return self.get_last_assistant_message()
