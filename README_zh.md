# StarLightTeaHouseBot
这是为星星小茶馆✨开发的一个telegram机器人。

[README](README.md) | [中文文档](README_zh.md)  
中文文档由 [BiancoCat](https://github.com/BiancoCat) 维护，可能不是最新版本。

# 使用方法：  
### 大多数功能可以在 .env 中切换

### 开始之前...
在 .env 文件中设置您的机器人令牌为 TELEGRAM_BOT_TOKEN。向 BotFather 获取一个令牌。  
如果您想使用 LLM 功能，请在 .env 中设置您的 Deepseek 令牌为 DEEPSEEK_API_KEY。

### 关于状态查询
使用命令"/status"检查服务器状态。包括CPU、内存使用情况和网络延迟。

### 关于欢迎消息：  
Bot会向任何进入群聊的新用户发送**欢迎消息**。  
使用"/groupwelcome \<参数\>"设置欢迎消息、过滤器和验证消息。只有群管理员可以更改这些设置。  
使用方法（也可以在聊天中尝试"/groupwelcome"查看使用方式）：  

- 切换群欢迎消息：  
  `/groupwelcome <on/off>`  
- 设置群欢迎消息：  
  `/groupwelcome setmsg <message>`  
- 切换群验证：  
  `/groupwelcome verify <on/off>`  
- 设置群验证过滤器：  
  `/groupwelcome vffilter <regex>`  
- 设置群验证消息：  
  `/groupwelcome setvfmsg <message>`  
- 设置群验证失败消息：  
  `/groupwelcome setvffailmsg <message>`  
- 批准所有等待用户：  
  `/groupwelcome approve`  

在**欢迎消息**中，您可以使用 {new_member_username}、{new_member_first_name} 和 {new_member_last_name}。  
如果启用了验证，将发送验证消息。  
新用户发送符合正则表达式过滤器的消息后，机器人将发送**验证消息**。  
如果新用户没有发送符合要求的消息，机器人会通知群管理员。（在 notifyAdmin.notify_admin() 中定义您自己的方法）  
所有欢迎消息和设置都存储在 welcome_msg_config.json 中。  

### 关于名言：
创建一个名为"quotes.json"的文件，格式如下：
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
您也可以使用 tools 中的 edit_quotes.py 通过界面编辑。  
如果您想发送自定义名言，@bot 并输入"\>\>[您的内容]"。通过这种方式可以"通过机器人"发送任何文本。

### 关于拱火：  
星星小茶馆的很多成员都在做这样的事：  
用"羡慕"回复随机消息或用"🔥"表情反应。  
对于**每条消息**，机器人都有概率执行此操作。  
使用"/xmfire <参数>"配置此功能。  
使用方法（也可以在聊天中尝试"/xmfire"查看使用方式）：  

- 切换功能：  
  `/xmfire <on/off>`  
- 设置触发功能的概率：  
  `/xmfire set <probability>`  

当功能被触发时，机器人会回复"羡慕"（50%）或反应"🔥"（50%）。  
也支持手动羡慕和火焰反应。使用 /xm \<消息链接\> 或 /fire \<消息链接\>。或直接回复 /xm 或 /fire。  
您也可以使用 /unxm <消息链接> 或回复 /unxm 来取消反应。  
~~\[未完成\] 如果您觉得机器人太烦人，可以使用 /xmfire suppress <分钟> 来暂时禁用。~~  

### 关于贴纸文件ID查询：  
在私聊中向机器人发送贴纸。它会返回文件ID。

### 关于今天吃什么：
在 config 中创建名为"foodlist.txt"的文件，每行一个食物名称。
当触发"/eattoday"或消息包含"今天吃什么"等词语时，机器人会随机选择一个食物名称。  
彩蛋：5% 概率吃"自己"（发送者姓名）

### 关于 denno mienmien mao：  
\\non non!/

### 关于禁漫天堂漫画下载：
使用"/jmcomic \<漫画名称\>"下载禁漫天堂漫画。下载的漫画将转换为PDF文件并发送到聊天中。  
**警告：此功能可能需要大量时间和资源。如果您的机器性能不足，机器人可能会崩溃。**  

### 关于 LLM
默认模型是 Deepseek。目前只支持 Deepseek。欢迎修改 modules/LLM 中的代码来添加更多模型。
使用"/llm \<消息\>"与 LLM 聊天，或回复消息时使用"/llm"发送该消息。  
所有聊天都是单轮对话，不保存上下文。
也可以使用"/llm"获取使用方法。

