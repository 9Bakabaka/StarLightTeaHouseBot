# StarLightTeaHouseBot
This is a telegram bot developed for StarLight Tea house.  

# Usage:  
### About Bot Token:
Create a file named "bottoken" at the same folder as the script and put your token in it.  

### About welcome message:  
Bot would send a welcome message to any new user entered the group chat.  
If the new user send message starts with "@" [@.*], bot would send another confirmation message.
If the new user doesn't send the verification message, bot would notify group admin. (Define your own method in NewUserVerify.verify_timer())

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

### About sticker file id query:  
Send a sticker to bot dm. It would return the file id.
