# StarLightTeaHouseBot
这是为星星小茶馆✨开发的一个telegram机器人。

[README](README.md) | [中文文档](README_zh.md)  

---
## 部署 Bot：  

- 大多数功能可以在 main() 中切换  
- 在 bottoken 文件中写入您的Bot Token  

### 使用 docker-compose 部署  

---  

1.  按照本指南在您的服务器上安装 docker：  

    https://docs.docker.com/engine/install/
2.  按照本指南在您的服务器上安装 docker-compose：  

    https://docs.docker.com/compose/install/
3. 使用以下命令克隆库到本地并进入目录：  
    ```bash  
    git clone https://github.com/LTLAE/StarLightTeaHouseBot.git
    cd StarLightTeaHouseBot
    ```
4. 将您的Bot Token写入 bottoken 文件中
5. 使用以下命令构建并启动容器：  
    ```bash  
    docker-compose up -d
    ```  

### 使用 Python 部署  

---  

1. 确保您的服务器已经安装了 Python 3.10 或更高版本。
2. 使用以下命令克隆库到本地并进入目录：  
    ```bash  
    git clone https://github.com/LTLAE/StarLightTeaHouseBot.git
    cd StarLightTeaHouseBot
    ```  
3. 将您的Bot Token写入 bottoken 文件中
4. 安装依赖：  
    ```bash  
    pip install -r requirements.txt
    ```
5. 运行Bot：  
    ```bash
    python3 main.py
    ```
   
---
## 功能：

### 1. 查看服务器状态：
使用命令"/status"检查服务器状态，包括CPU、内存使用情况和网络延迟。

### 2. 发送欢迎信息：
Bot会向任何进入群聊的新用户发送**欢迎信息**。
使用"/groupwelcome \<参数\>"设置欢迎信息、过滤器和验证信息。只有群管理员可以更改这些设置。
使用方法（也可以在聊天中尝试"/groupwelcome"查看使用方式）：
/groupwelcome <on/off> 切换群欢迎信息开关。  
/groupwelcome setmsg <消息> 设置群欢迎信息。  
/groupwelcome verify <on/off> 切换群验证功能。  
/groupwelcome vffilter <正则表达式> 设置群验证过滤器。  
/groupwelcome setvfmsg <消息> 设置群验证信息。  
/groupwelcome setvffailmsg <消息> 设置群验证失败信息。  
在**欢迎消息**中，您可以使用 {new_member_username}、{new_member_first_name} 和 {new_member_last_name} 来构建消息。
如果启用了验证，将会发送验证消息。
当新用户发送符合正则表达式的消息时，机器人将发送**验证消息**。
如果新用户没有发送符合要求的消息，机器人会通知群管理员。（可以在 notifyAdmin.notify_admin() 中定义您自己的方法）
所有欢迎消息和设置都存储在 welcome_msg_config.json 文件中。

### 3. 发送名言：
创建一个名为"quotes.json"的文件，并按以下格式添加名言：
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
您也可以使用EditQuotes.py通过界面进行编辑。
如果您想发送自定义的名言，可以@bot并输入"\>\>[您的内容]"。通过这种方式，您可以通过Bot发送任何文本。

### 4. 拱火：
星星小茶馆✨的很多成员做这样一件事：
用"羡慕"回复随机消息或用"🔥"进行反应。
对于**每一条消息**，Bot都有概率进行这种操作。
使用"/xmfire <参数>"配置此功能。
使用方法（也可以在聊天中尝试"/xmfire"查看使用方式）：
/xmfire <on/off> 切换功能开关。  
/xmfire set <概率> 设置触发功能的概率。  
当功能被触发时，Bot会回复"羡慕"（50%）或反应"🔥"（50%）到消息中。
也支持手动进行羡慕和"🔥"回复。使用/xm \<消息链接\> 或 /fire \<消息链接\>。或者直接回复/xm或/fire到消息中。
~~\[未完成\]如果您觉得Bot太烦人，您可以使用/xmfire suppress <分钟>来暂时压制它。~~

### 5.贴纸文件ID查询：
将贴纸发送到Bot的私聊中，它会返回文件ID。

### 6.今天吃什么（roll 饭）：
将食物名称放入名为"foodlist.txt"的文件中，每行一个食物名称。
当触发"/eattoday"或消息包含类似"今天吃什么"的内容时，Bot会从列表中随机选择一个食物名称。
彩蛋：5%的概率选择"自己"（发送者的名字）。  

---
