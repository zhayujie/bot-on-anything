<p align="center"><img src= "https://github.com/user-attachments/assets/6e931057-e09f-4742-9fbd-2417cf6bc2f3" alt="Bot-On-Anything" width="600" /></p>

<p align="center">
   <a href="https://github.com/zhayujie/bot-on-anything/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/bot-on-anything" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/bot-on-anything/blob/master/LICENSE"><img src="https://img.shields.io/github/license/zhayujie/bot-on-anything" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/bot-on-anything"><img src="https://img.shields.io/github/stars/zhayujie/bot-on-anything?style=flat-square" alt="Stars"></a> <br/>
    [<a href="/README.md">English</a>] | [<a href="/docs/README-CN.md">中文</a>]
</p>

**Bot on Anything** is a powerful AI chatbot builder that allows you to quickly build chatbots and run them anywhere.

# Introduction

Developers can build and run an intelligent dialogue robot by selecting a connection between various AI large models and application channels with lightweight configuration. It supports easy switching between multiple paths within a single project. This architecture has strong scalability; each application can reuse existing model capabilities, and each new model can run on all application channels.

**Models:**

 - [x] [ChatGPT](https://github.com/zhayujie/bot-on-anything#1-chatgpt)
 - [ ] [Claude](https://github.com/zhayujie/bot-on-anything)
 - [ ] [Gemini](https://github.com/zhayujie/bot-on-anything)

**Applications:**

 - [x] [Terminal](https://github.com/zhayujie/bot-on-anything#1%E5%91%BD%E4%BB%A4%E8%A1%8C%E7%BB%88%E7%AB%AF)
 - [x] [Web](https://github.com/zhayujie/bot-on-anything#9web)
 - [x] [Subscription Account](https://github.com/zhayujie/bot-on-anything#3%E4%B8%AA%E4%BA%BA%E8%AE%A2%E9%98%85%E5%8F%B7)
 - [x] [Service Account](https://github.com/zhayujie/bot-on-anything#4%E4%BC%81%E4%B8%9A%E6%9C%8D%E5%8A%A1%E5%8F%B7)
 - [x] [Enterprise WeChat](https://github.com/zhayujie/bot-on-anything#12%E4%BC%81%E4%B8%9A%E5%BE%AE%E4%BF%A1)
 - [x] [Telegram](https://github.com/zhayujie/bot-on-anything#6telegram)
 - [x] [QQ](https://github.com/zhayujie/bot-on-anything#5qq)
 - [x] [DingTalk](https://github.com/zhayujie/bot-on-anything#10%E9%92%89%E9%92%89)
 - [x] [Feishu](https://github.com/zhayujie/bot-on-anything#11%E9%A3%9E%E4%B9%A6)
 - [x] [Gmail](https://github.com/zhayujie/bot-on-anything#7gmail)
 - [x] [Slack](https://github.com/zhayujie/bot-on-anything#8slack)

# Quick Start

### 1. Runtime Environment

Supports Linux, MacOS, and Windows systems, and Python must be installed. It is recommended to use Python version between 3.7.1 and 3.10.

Clone the project code and install dependencies:

```bash
git clone https://github.com/zhayujie/bot-on-anything
cd bot-on-anything/
pip3 install -r requirements.txt
```

### 2. Configuration Instructions

The core configuration file is `config.json`, and a template file `config-template.json` is provided in the project, which can be copied to generate the final effective `config.json` file:

```bash
cp config-template.json config.json
```

Each model and channel has its own configuration block, which together form a complete configuration file. The overall structure is as follows:

```bash
{
  "model": {
    "type" : "openai",             # Selected AI model
    "openai": {
      # openAI configuration
    }
  },
  "channel": {
    "type": "slack",            # Channel to be integrated
    "slack": {
        # slack configuration
    },
    "telegram": {
        # telegram configuration
    }
  }
}
```
The configuration file is divided into `model` and `channel` sections at the outermost level. The model section is for model configuration, where the `type` specifies which model to use; the channel section contains the configuration for application channels, and the `type` field specifies which application to integrate.

When using, you only need to change the `type` field under the model and channel configuration blocks to switch between any model and application, connecting different paths. Below, each model and application configuration and running process will be introduced in turn.

### 3. Running

Run the following command in the project root directory, with the default channel being the terminal:

```bash
python3 app.py
```

## II. Choose a Model

### 1. ChatGPT

The default model is `gpt-3.5-turbo`. For details, refer to the [official documentation](https://platform.openai.com/docs/guides/chat). It also supports `gpt-4.0`, just modify the model type parameter.

#### (1) Install Dependencies

```bash
pip3 install --upgrade openai
```
> Note: The openai version needs to be above `0.27.0`. If installation fails, you can first upgrade pip with `pip3 install --upgrade pip`.

#### (2) Configuration Item Instructions

```bash
{
  "model": {
    "type" : "chatgpt",
    "openai": {
      "api_key": "YOUR API KEY",
      "model": "gpt-3.5-turbo",                         # Model name
      "proxy": "http://127.0.0.1:7890",                 # Proxy address
      "character_desc": "You are ChatGPT, a large language model trained by OpenAI, aimed at answering and solving any questions people have, and can communicate in multiple languages. When asked who you are, you should also tell the questioner that entering #clear_memory can start a new topic exploration. Entering draw xx can create a picture for you.",
      "conversation_max_tokens": 1000,                  # Maximum number of characters in the reply, total for input and output
      "temperature":0.75,     # Entropy, between [0,1], the larger the value, the more random the selected candidate words, the more uncertain the reply, it is recommended to use either this or the top_p parameter, the greater the creativity task, the better, the smaller the precision task
      "top_p":0.7,            # Candidate word list. 0.7 means only considering the top 70% of candidate words, it is recommended to use either this or the temperature parameter
      "frequency_penalty":0.0,            # Between [-2,2], the larger this value, the more it reduces the repetition of words in the model's output, leaning towards producing different content
      "presence_penalty":1.0,             # Between [-2,2], the larger this value, the less restricted by the input, encouraging the model to generate new words not present in the input, leaning towards producing different content
    }
}
```
 + `api_key`: Fill in the `OpenAI API KEY` created when registering your account.
 + `model`: Model name, currently supports `gpt-3.5-turbo`, `gpt-4`, `gpt-4-32k` (the gpt-4 API is not yet open).
 + `proxy`: The address of the proxy client, refer to [#56](https://github.com/zhayujie/bot-on-anything/issues/56) for details.
 + `character_desc`: This configuration saves a piece of text you say to ChatGPT, and it will remember this text as its setting; you can customize any personality for it.
 + `max_history_num`[optional]: Maximum memory length of the conversation, exceeding this length will clear the previous memory.

---

### 2. LinkAI

#### Configuration Item Instructions
```bash
{
  "model": {
    "type" : "linkai",
    "linkai": {
      "api_key": "",
      "api_base": "https://api.link-ai.tech",
      "app_code":  "",
      "model": "",
      "conversation_max_tokens": 1000,
      "temperature":0.75,
      "top_p":0.7,
      "frequency_penalty":0.0,
      "presence_penalty":1.0,
      "character_desc": "You are an intelligent assistant."
    },
}
```

+ `api_key`: The key for calling the LinkAI service, which can be created in the [console](https://link-ai.tech/console/interface).
+ `app_code`: The code for the LinkAI application or workflow, optional, refer to [Application Creation](https://docs.link-ai.tech/platform/create-app).
+ `model`: Supports common models from both domestic and international sources, refer to [Model List](https://docs.link-ai.tech/platform/api/chat#models). It can be left blank, and the default model of the application can be modified in the [LinKAI platform](https://link-ai.tech/console/factory).
+ Other parameters have the same meaning as those in the ChatGPT model.

## III. Choose a Channel

### 1. Command Line Terminal

The application that starts by default in the configuration template is the terminal, which requires no additional configuration. You can start the program by executing `python3 app.py` directly in the project directory. Users interact with the dialogue model through command line input, and it supports streaming response effects.

![terminal_demo.png](docs/images/terminal_demo.png)

---

### 2. Web

**Contributor:** [RegimenArsenic](https://github.com/RegimenArsenic)

**Dependencies**

```bash
pip3 install PyJWT flask flask_socketio
```

**Configuration**

```bash
"channel": {
    "type": "http",
    "http": {
      "http_auth_secret_key": "6d25a684-9558-11e9-aa94-efccd7a0659b",    // JWT authentication secret key
      "http_auth_password": "6.67428e-11",        // Authentication password, just for personal use, a preliminary defense against others scanning ports and DDOS wasting tokens
      "port": "80"       // Port
    }
  }
```

Run locally: After running `python3 app.py`, access `http://127.0.0.1:80`.

Run on a server: After deployment, access `http://public domain or IP:port`.

---

### 3. Personal Subscription Account

**Requirements:** A server and a subscription account.

#### 3.1 Dependency Installation

Install the [werobot](https://github.com/offu/WeRoBot) dependency:

```bash
pip3 install werobot
```

#### 3.2 Configuration

```bash
"channel": {
    "type": "wechat_mp",

    "wechat_mp": {
      "token": "YOUR TOKEN",           # Token value
      "port": "8088"                   # Port the program listens on
    }
}
```

#### 3.3 Run the Program

Run `python3 app.py` in the project directory. If the terminal displays the following, it indicates successful operation:

```
[INFO][2023-02-16 01:39:53][app.py:12] - [INIT] load config: ...
[INFO][2023-02-16 01:39:53][wechat_mp_channel.py:25] - [WX_Public] Wechat Public account service start!
Bottle v0.12.23 server starting up (using AutoServer())...
Listening on http://127.0.0.1:8088/
Hit Ctrl-C to quit.
```

#### 2.2 Set the Callback URL for the Subscription Account

Go to the personal subscription account in the [WeChat Official Platform](https://mp.weixin.qq.com/) and enable server configuration:

![wx_mp_config.png](docs/images/wx_mp_config.png)

**Server Address (URL) Configuration**: If you can access the Python program on the server through the configured URL in the browser (default listening on port 8088), it indicates that the configuration is valid. Since the subscription account can only configure ports 80/443, you can modify the configuration to listen directly on port 80 (requires sudo permissions) or use reverse proxy forwarding (like nginx). According to the official documentation, you can fill in either the public IP or domain name here.

**Token Configuration**: Must be consistent with the token in the `config.json` configuration.

For detailed operation processes, refer to the [official documentation](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html).

#### 2.3 Usage

After users follow the subscription account, they can send messages.

> Note: After users send messages, the WeChat backend will push to the configured URL address, but if there is no reply within 5 seconds, the connection will be disconnected, and it will retry 3 times. However, the request to the OpenAI interface often takes more than 5 seconds. In this project, asynchronous and caching methods have optimized the 5-second timeout limit to 15 seconds, but exceeding this time will still not allow normal replies. At the same time, each time the connection is disconnected after 5 seconds, the web framework will report an error, which will be optimized later.

---

### 4. Enterprise Service Account

**Requirements:** A server and a certified service account.

In the enterprise service account, the 15-second timeout issue of the personal subscription account is resolved by first asynchronously accessing the OpenAI interface and then proactively pushing to the user through the customer service interface. The developer mode configuration of the service account is similar to that of the subscription account. For details, refer to the [official documentation](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html).

The `config.json` configuration for the enterprise service account only needs to change the type to `wechat_mp_service`, but the configuration block still reuses `wechat_mp`, and in addition, you need to add two configuration items: `app_id` and `app_secret`.

```bash
"channel": {
    "type": "wechat_mp_service",

    "wechat_mp": {
      "token": "YOUR TOKEN",            # Token value
      "port": "8088",                   # Port the program listens on
      "app_id": "YOUR APP ID",          # App ID
      "app_secret": "YOUR APP SECRET"   # App secret
    }
}
```

Note: The server IP address must be configured in the "IP Whitelist"; otherwise, users will not receive proactively pushed messages.

---

### 5. QQ

Requirements: A PC or server (domestic network) and a QQ account.

Running the QQ bot requires additionally running a `go-cqhttp` program, which is responsible for receiving and sending QQ messages, while our `bot-on-anything` program is responsible for accessing OpenAI to generate dialogue content.

#### 5.1 Download go-cqhttp

Download the corresponding machine program from the [go-cqhttp Release](https://github.com/Mrs4s/go-cqhttp/releases), unzip it, and place the `go-cqhttp` binary file in our `bot-on-anything/channel/qq` directory. A `config.yml` configuration file is already prepared here; you only need to fill in the QQ account configuration (account-uin).

#### 5.2 Install aiocqhttp

Use [aiocqhttp](https://github.com/nonebot/aiocqhttp) to interact with go-cqhttp, execute the following command to install the dependency:

```bash
pip3 install aiocqhttp
```

#### 5.3 Configuration

Simply change the `type` in the `config.json` configuration file's channel block to `qq`:

```bash
"channel": {
    "type": "qq"
}
```

#### 5.4 Running

First, go to the root directory of the `bot-on-anything` project and run in Terminal 1:

```bash
python3 app.py    # This will listen on port 8080
```

In the second step, open Terminal 2, navigate to the directory where `cqhttp` is located, and run:

```bash
cd channel/qq
./go-cqhttp
```
Note:
+ Currently, no keyword matching or group chat whitelist is set; all private chats will automatically reply, and in group chats, as long as you are @mentioned, it will also automatically reply.
+ If you encounter exceptions such as account freezing, you can change the value of `protocol` in the `device.json` file in the same directory as go-cqhttp from 5 to 2, refer to this [Issue](https://github.com/Mrs4s/go-cqhttp/issues/1942).

---

### 6. Telegram

Contributor: [brucelt1993](https://github.com/brucelt1993)

**6.1 Get Token**

Applying for a Telegram bot can be easily found on Google; the important thing is to obtain the bot's token ID.

**6.2 Dependency Installation**

```bash
pip install pyTelegramBotAPI
```

**6.3 Configuration**

```bash
"channel": {
    "type": "telegram",
    "telegram":{
      "bot_token": "YOUR BOT TOKEN ID"
    }
}
```
---

### 7. Gmail

Requirements: A server and a Gmail account.

**Contributor:** [Simon](https://github.com/413675377)

Follow the [official documentation](https://support.google.com/mail/answer/185833?hl=en) to create an APP password for your Google account, configure as below, then cheers!!!

```bash
"channel": {
    "type": "gmail",
    "gmail": {
      "subject_keyword": ["bot", "@bot"],
      "host_email": "xxxx@gmail.com",
      "host_password": "GMAIL ACCESS KEY"
    }
  }
```
---

### 8. Slack

**❉ No longer requires a server or public IP**

**Contributor:** [amaoo](https://github.com/amaoo)

**Dependencies**

```bash
pip3 install slack_bolt
```

**Configuration**

```bash
"channel": {
    "type": "slack",
    "slack": {
      "slack_bot_token": "xoxb-xxxx",
      "slack_app_token": "xapp-xxxx"
    }
  }
```

**Set Bot Token Scope - OAuth & Permission**

Write the Bot User OAuth Token into the configuration file `slack_bot_token`.

```
app_mentions:read
chat:write
```

**Enable Socket Mode - Socket Mode**

If you have not created an application-level token, you will be prompted to create one. Write the created token into the configuration file `slack_app_token`.

**Event Subscription (Event Subscriptions) - Subscribe to Bot Events**

```
app_mention
```

**Reference Documentation**

```
https://slack.dev/bolt-python/tutorial/getting-started
```

---

### 10. DingTalk

**Requirements:**

- Enterprise internal development robot.

**Dependencies**

```bash
pip3 install requests flask
```
**Configuration**

```bash
"channel": {
    "type": "dingtalk",
    "dingtalk": {
      "image_create_prefix": ["draw", "draw", "Draw"],
      "port": "8081",                  # External port
      "dingtalk_token": "xx",          # Access token of the webhook address
      "dingtalk_post_token": "xx",     # Verification token carried in the header when DingTalk posts back messages
      "dingtalk_secret": "xx"          # Security encryption signature string in the group robot
    }
  }
```
**Reference Documentation**:

- [DingTalk Internal Robot Tutorial](https://open.dingtalk.com/document/tutorial/create-a-robot#title-ufs-4gh-poh)
- [Custom Robot Access Documentation](https://open.dingtalk.com/document/tutorial/create-a-robot#title-ufs-4gh-poh)
- [Enterprise Internal Development Robot Tutorial Documentation](https://open.dingtalk.com/document/robots/enterprise-created-chatbot)

**Generate Robot**

Address: https://open-dev.dingtalk.com/fe/app#/corp/robot
Add a robot, set the server's outbound IP in the development management, and the message receiving address (the external address in the configuration, such as https://xx.xx.com:8081).

---

### 11. Feishu

**Dependencies**

```bash
pip3 install requests flask
```
**Configuration**

```bash
"channel": {
    "type": "feishu",
    "feishu": {
        "image_create_prefix": [
            "draw",
            "draw",
            "Draw"
        ],
        "port": "8082",                  # External port
        "app_id": "xxx",                 # Application app_id
        "app_secret": "xxx",             # Application Secret
        "verification_token": "xxx"      # Event subscription Verification Token
    }
}
```

**Generate Robot**

Address: https://open.feishu.cn/app/
1. Add a self-built application for the enterprise.
2. Enable permissions:
    - im:message
    - im:message.group_at_msg
    - im:message.group_at_msg:readonly
    - im:message.p2p_msg
    - im:message.p2p_msg:readonly
    - im:message:send_as_bot
3. Subscribe to the menu to add events (receive messages v2.0) and configure the request address (the external address in the configuration, such as https://xx.xx.com:8081).
4. In version management and publishing, launch the application, and the app will receive review information. After passing the review, add the self-built application in the group.

---

### 12. Enterprise WeChat

**Requirements:** A server and a certified Enterprise WeChat.

The `config.json` configuration for Enterprise WeChat only needs to change the type to `wechat_com`, with the default message receiving server URL: http://ip:8888/wechat.

```bash
"channel": {
    "type": "wechat_com",
    "wechat_com": {
      "wechat_token": "YOUR TOKEN",            # Token value
      "port": "8888",                          # Port the program listens on
      "app_id": "YOUR APP ID",                 # App ID
      "app_secret": "YOUR APP SECRET",          # App secret
      "wechat_corp_id": "YOUR CORP ID",
      "wechat_encoding_aes_key": "YOUR AES KEY"
    }
}
```

Note: The server IP address must be configured in the "Enterprise Trusted IP" list; otherwise, users will not receive proactively pushed messages.

**Reference Documentation**:

- [Enterprise WeChat Configuration Tutorial](https://www.wangpc.cc/software/wechat_com-chatgpt/)

### General Configuration

+ `clear_memory_commands`: Dialogue internal commands to actively clear previous memory, the string array can customize command aliases.
  + default: ["#clear_memory"]
