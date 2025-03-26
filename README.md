# StarLightTeaHouseBot
This is a telegram bot developed for StarLight Tea house.  

[README](README.md) | [中文文档](README_zh.md)  

# Usage:  
### Most of the functions can be toggled in main()

### About Bot Token:
Create a text file named "bottoken" at the same folder as the script and put your token in it.

### About Status
Use command "/status" to check server status. Including CPU, memory usage and network latency.

### About welcome message:  
Bot would send a **welcome message** to any new user entered the group chat.  
Use "/groupwelcome \<parameter\>" to set welcome message, filter and verification message. Only group admins can change these settings.  
Usages (Also try "/groupwelcome" for usages in chat):  
/groupwelcome <on/off> Toggle group welcome message.  
/groupwelcome setmsg <message> Set group welcome message.  
/groupwelcome verify <on/off> Toggle group verify.  
/groupwelcome vffilter <regex> Set group verify filter.  
/groupwelcome setvfmsg <message> Set group verify message.  
/groupwelcome setvffailmsg <message> Set group verify fail message.  
In **welcome message**, you can use {new_member_username}, {new_member_first_name} and {and new_member_last_name} in the message.  
Verify message would be sent if verify is enabled.  
After the new user send a message matches the filter by regex, then the bot will send **verify message**.  
If the new user doesn't send it, bot would notify group admin. (Define your own method in notifyAdmin.notify_admin())  
All welcome messages and settings are stored in welcome_msg_config.json.  

### About quotes:
Create a file named "quotes.json" and put quotes like this:
```json
[
    {
        "speaker": "Speaker_Name1",
        "quote": "Quote_Text1"
    },
    {
        "speaker": "Speaker_Name2",
        "quote": "Quote_Text2"
    }
]
```
You can also use EditQuotes.py to edit it with an interface.  
If you want to send your customized quote, @bot and type "\>\>\[your content\]". In this way you can send any text "via bot".

### About 拱火:  
A lot of members in StarLight Tea House are doing such thing:  
Reply a random message with "羡慕" or react it with "🔥".  
For **every message**, bot would have a probability to do such thing.  
Use "/xmfire <parameter>" to configure this function.  
Usages (Also try "/xmfire" for usages in chat):  
/xmfire <on/off> Toggle function.  
/xmfire set <probability> Set probability of triggering the function.  
When the function is triggered, bot would reply "羡慕"(50%) or react "🔥"(50%) to the message.  
Manual 羡慕 and fire reaction are also supported. Use /xm \<message link\> or /fire \<message link\>. Or just reply /xm or /fire to the message.  
~~\[Not finished\] If you think the bot is too annoying, you can use /xmfire suppress <minutes> to suppress it temporarily.~~  

### About sticker file id query:  
Send a sticker to bot in pm. It would return the file id.

### About what to eat today:
Put food names in a file named "foodlist.txt", one food name per line.
When triggered "/eattoday" or message contain words like "今天吃什么", bot would randomly choose one food name from the list.  
Easter egg: 5% chance eat "themselves"(sender's name)

### About jm comic download:
Use "/jmcomic \<comic name\>" to download jm comic.

### About LLM
Chat with LLM with "/llm \<message\>" or reply a message with "/llm" to send the message.  
All chats are single-turn with no context saved.
Also use "/llm" to get usages.

