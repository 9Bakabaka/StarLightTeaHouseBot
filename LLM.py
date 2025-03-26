from openai import OpenAI, APIStatusError

with open('DSapi.txt', 'r') as f:
    DS_api = f.read()
# with open('GPTapi.txt', 'r') as f:
#     GPT_api = f.read()

# platform: "DS" "GPT"
def fetch_from_AI(platform, sys_prompt, user_prompt):
    if platform == "DS":
        base_url = "https://api.deepseek.com"
    elif platform == "GPT":
        base_url = "https://api.openai.com"
    else:
        return "Error: Invalid platform."

    response = None
    client = OpenAI(api_key=DS_api, base_url=base_url)
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )
    except APIStatusError as e:
        if e.status_code == 402:
            print("Insufficient Balance")
            return e
        else:
            print(f"APIStatusError: {e}")
            return e

    if response:
        print(response.choices[0].message.content)
        return response.choices[0].message.content

# if excepting model "remember context", user_prompt = last_user_prompt + this_user_prompt
