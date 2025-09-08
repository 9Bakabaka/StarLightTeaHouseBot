# This file is a copy of LLM.py in Must2502 SE252 project
import os

from openai import OpenAI, APIStatusError

# with open('DSapi.txt', 'r') as f:
#     DS_api = f.read()
# with open('GPTapi.txt', 'r') as f:
#     GPT_api = f.read()

# platform: "DS" "GPT"
def fetch_from_AI(platform, sys_prompt, user_prompt):
    print("Start fetching from AI")
    AI_model = ""
    if platform == "DS":
        base_url = "https://api.deepseek.com"
        AI_model = "deepseek-chat"
    elif platform == "GPT":
        # base_url = "https://api.openai.com"
        base_url = "https://api.f2gpt.com"
        AI_model = "gpt-3.5-turbo"
    else:
        print("Error: Invalid platform")
        return "Error"

    response = None
    client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=base_url)
    try:
        response = client.chat.completions.create(
            model=AI_model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
    except APIStatusError as e: # handle APIStatusError
        if e.status_code == 402:
            print("Insufficient Balance")
        else:
            print(f"APIStatusError: {e}")
        return "Error"

    except Exception as e:  # handle other exceptions
        print(f"Error: {e}")
        return "Error"

    if response:
        print("AI response: ", response.choices[0].message.content)
        return response.choices[0].message.content

    return "Error"

# if excepting model "remember context", user_prompt = last_user_prompt + this_user_prompt
