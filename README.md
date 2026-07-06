[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/zhayujie-bot-on-anything-badge.png)](https://mseep.ai/app/zhayujie-bot-on-anything)

<p align="center"><img src= "https://github.com/user-attachments/assets/6e931057-e09f-4742-9fbd-2417cf6bc2f3" alt="Bot-On-Anything" width="600" /></p>

<p align="center">
   <a href="https://github.com/zhayujie/bot-on-anything/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/bot-on-anything" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/bot-on-anything/blob/master/LICENSE"><img src="https://img.shields.io/github/license/zhayujie/bot-on-anything" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/bot-on-anything"><img src="https://img.shields.io/github/stars/zhayujie/bot-on-anything?style=flat-square" alt="Stars"></a> <br/>
    [English] | [<a href="/docs/README-CN.md">中文</a>]
</p>

**Bot on Anything** is a lightweight framework for building AI chatbots. With a bit of configuration you can connect various large models to different application channels — a great fit for quickly spinning up bots on overseas channels like Telegram, Slack, Discord, and Gmail.

> Need a more complete Agent — task planning, long-term memory, skills, MCP, self-evolution and more? Check out our other project **[CowAgent](https://github.com/zhayujie/CowAgent)**. See [Related Projects](#related-projects).

<br/>

## Introduction

With a single config file, you pick one connection between a large model and an application channel, get a chatbot running, and switch between different paths anytime within the same project. Models and channels are independent: adding a channel reuses existing models, and adding a model works across all channels.

<br/>

## 🌟 Highlights

| Capability | Description |
| :--- | :--- |
| Multiple models | OpenAI (GPT-5.5 / GPT-4.1, etc.), LinkAI (one key for 100+ models: DeepSeek, Claude, Gemini...), ERNIE Bot, New Bing, Bard — switch by changing the `type` field |
| Multiple channels | Terminal, Web, WeChat Subscription / Service Account, Enterprise WeChat, QQ, Telegram, Gmail, Slack, DingTalk, Feishu, Discord — 12 channels |
| Decoupled models & channels | Models and channels are not bound together; any model runs on any channel, and adding one side reuses the other |
| Parallel channels | List multiple channels in one config and start them together as separate processes without interference |
| Plugin support | Compatible with the plugin model of [chatgpt-on-wechat](https://github.com/zhayujie/CowAgent/tree/master/plugins) — extend with image generation, model selectors, and more |
| Lightweight deploy | Pure Python, runs with just a few lines of config |

<br/>

## 🚀 Quick Start

### 1. Runtime Environment

Works on Linux, MacOS, and Windows. Python is required — version 3.7.1~3.10 is recommended.

Clone the code and install dependencies:

```bash
git clone https://github.com/zhayujie/bot-on-anything
cd bot-on-anything/
pip3 install -r requirements.txt
```

### 2. Configuration

The core config file is `config.json`. The project ships with a template `config-template.json` — just copy it to get the actual config:

```bash
cp config-template.json config.json
```

Each model and channel has its own config block, which together form the full config file. The overall structure looks like this:

```bash
{
  "model": {
    "type" : "openai",             # the AI model to use
    "openai": {
      # openAI config
    }
  },
  "channel": {
    "type": "slack",            # the channel to connect
    "slack": {
        # slack config
    },
    "telegram": {
        # telegram config
    }
  }
}
```

At the top level the config splits into `model` and `channel`: `model` is the model config, whose `type` picks which model to use; `channel` is the channel config, whose `type` picks which channel to connect (it can also be an array to start several channels at once).

Day to day, you just change these two `type` fields to switch between different models and channels. Each model and channel is described below, with configuration and how to run it (click to expand).

### 3. Running

Run the following in the project root — the default channel is the terminal:

```bash
python3 app.py
```

<br/>

## 🤖 Models

| Model | Description |
| :--- | :--- |
| [OpenAI](#openai) | Works with the OpenAI-compatible chat API — GPT-5.5 / GPT-4.1 and other models, or any compatible gateway via `api_base` |
| [LinkAI](#linkai) | One key for 100+ models including DeepSeek, Claude, Gemini, Qwen, GLM, and more |
| [ERNIE Bot](#ernie-bot) | Based on Baidu ERNIE Bot's web version |
| [New Bing](#new-bing) | Based on Bing chat, supports jailbreak mode |
| [Bard](#bard) | Based on Google Bard's web version |

> For models from other providers (DeepSeek, Claude, Gemini...), use **LinkAI** — one key covers them all — or [CowAgent](https://github.com/zhayujie/CowAgent).

<a id="openai"></a>
<details>
<summary><b>OpenAI</b></summary>

Uses the OpenAI-compatible chat API. Set `model` to any model your endpoint supports (e.g. `gpt-5.5`, `gpt-4.1`), or point `api_base` to a compatible gateway to use other providers. See the [official docs](https://platform.openai.com/docs/guides/chat) for details.

**Install dependencies**

```bash
pip3 install "openai<1.0.0"
```
> Note: this project uses the legacy `openai` SDK (`0.27.x`+ but below `1.0.0`) — `requirements.txt` already pins a compatible version. If installation fails, upgrade pip first with `pip3 install --upgrade pip`.

**Configuration**

```bash
{
  "model": {
    "type" : "chatgpt",
    "openai": {
      "api_key": "YOUR API KEY",
      "api_base": "",                                   # optional, an OpenAI-compatible endpoint
      "model": "gpt-5.5",                               # model name
      "proxy": "http://127.0.0.1:7890",                 # proxy address
      "character_desc": "You are ChatGPT, a large language model trained by OpenAI...",
      "conversation_max_tokens": 1000,                  # max reply length, total of input and output
      "temperature":0.75,     # entropy in [0,1]; higher means more random word choices
      "top_p":0.7,            # candidate word list; 0.7 means only the top 70% of candidates are considered
      "frequency_penalty":0.0,            # in [-2,2]; higher reduces word repetition in a line
      "presence_penalty":1.0,             # in [-2,2]; higher is less constrained by the input
    }
}
```
+ `api_key`: the `OpenAI API KEY` created when you registered your account
+ `api_base` (optional): an OpenAI-compatible endpoint; leave empty for the official API, or point it to a compatible gateway to use other providers
+ `model`: any model your endpoint supports, e.g. `gpt-5.5`, `gpt-4.1`, `gpt-4o` (GPT-5 / o-series only accept default sampling params; this project skips them automatically)
+ `proxy`: proxy client address, see [#56](https://github.com/zhayujie/bot-on-anything/issues/56)
+ `character_desc`: the bot's persona; the model plays this role, feel free to customize it
+ `max_history_num` (optional): max length of conversation memory; older memory is cleared beyond this

</details>

<a id="linkai"></a>
<details>
<summary><b>LinkAI</b></summary>

**Configuration**

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

+ `api_key`: the key for calling LinkAI, created in the [console](https://link-ai.tech/console/interface)
+ `app_code`: the code of a LinkAI app or workflow, optional, see [Creating an App](https://docs.link-ai.tech/platform/create-app)
+ `model`: one key gives access to 100+ models (DeepSeek, Claude, Gemini, Qwen, GLM, GPT, etc.), see the [model list](https://docs.link-ai.tech/platform/api/chat#models); can be left empty and set the app's default model on the [LinkAI platform](https://link-ai.tech/console/factory)
+ Other parameters have the same meaning as in the OpenAI model

</details>

<a id="ernie-bot"></a>
<details>
<summary><b>ERNIE Bot</b></summary>

Based on Baidu ERNIE Bot's web version, needs a Cookie obtained manually.

```bash
{
  "model": {
    "type" : "baidu",
    "baidu": {
      "acs_token": "YOUR ACS TOKEN",
      "cookie": "YOUR COOKIE"
    }
  }
}
```

+ `cookie`: after logging into [ERNIE Bot](https://yiyan.baidu.com/) in the browser, grab it from the developer tools
+ `acs_token`: same as above, grab it from the request parameters; search for a tutorial if needed

</details>

<a id="new-bing"></a>
<details>
<summary><b>New Bing</b></summary>

Based on Bing chat, depends on the `EdgeGPT` library, needs a Cookie after logging into Bing.

```bash
{
  "model": {
    "type" : "bing",
    "bing":{
      "jailbreak": true,
      "jailbreak_prompt": "...",
      "cookies": []
    }
  }
}
```

+ `cookies`: the array of cookies exported from the browser after logging into [Bing](https://www.bing.com/)
+ `jailbreak`: whether to enable jailbreak (Sydney) mode, which bypasses some of the official restrictions

</details>

<a id="bard"></a>
<details>
<summary><b>Bard</b></summary>

Based on Google Bard's web version, needs a Cookie after logging in.

```bash
{
  "model": {
    "type" : "bard",
    "bard": {
      "cookie": "YOUR COOKIE"
    }
  }
}
```

</details>

<br/>

## 💬 Channels

| Channel | Description |
| :--- | :--- |
| [Terminal](#terminal) | Default channel, no extra config needed |
| [Web](#web) | Web-based chat, built on flask + socketio |
| [Subscription Account](#subscription-account) | Auto-reply for a personal WeChat subscription account |
| [Service Account](#service-account) | Verified WeChat service account, gets around the 5s timeout |
| [QQ](#qq) | Depends on go-cqhttp, supports private and group chat |
| [Telegram](#telegram) | Telegram bot |
| [Gmail](#gmail) | Chat over email |
| [Slack](#slack) | Slack bot, Socket Mode needs no public IP |
| [DingTalk](#dingtalk) | DingTalk enterprise internal bot |
| [Feishu](#feishu) | Feishu enterprise self-built app |
| [Enterprise WeChat](#enterprise-wechat) | Enterprise WeChat self-built app |
| [Discord](#discord) | Discord bot |

<a id="terminal"></a>
<details>
<summary><b>Terminal</b></summary>

The config template starts the terminal by default — no extra config needed. Run `python3 app.py` in the project directory to start it. Type right in the terminal to chat with the model, with streaming output supported.

![terminal_demo.png](images/terminal_demo.png)

</details>

<a id="web"></a>
<details>
<summary><b>Web</b></summary>

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
      "http_auth_secret_key": "6d25a684-9558-11e9-aa94-efccd7a0659b",    // JWT auth secret key
      "http_auth_password": "6.67428e-11",        // auth password, for personal use, a basic defense against port scanning and DDOS wasting tokens
      "port": "80"       // port
    }
  }
```

Run locally: after `python3 app.py`, visit `http://127.0.0.1:80`.

Run on a server: after deploying, visit `http://your-domain-or-IP:port`.

</details>

<a id="subscription-account"></a>
<details>
<summary><b>Subscription Account</b></summary>

**Requirements:** a server and a subscription account.

**1. Install dependencies**

Install [werobot](https://github.com/offu/WeRoBot):

```bash
pip3 install werobot
```

**2. Configuration**

```bash
"channel": {
    "type": "wechat_mp",
    "wechat_mp": {
      "token": "YOUR TOKEN",           # token value
      "port": "8088"                   # port the program listens on
    }
}
```

**3. Run the program**

Run `python3 app.py` in the project directory. If the terminal shows the following, it started successfully:

```
[INFO][2023-02-16 01:39:53][app.py:12] - [INIT] load config: ...
[INFO][2023-02-16 01:39:53][wechat_mp_channel.py:25] - [WX_Public] Wechat Public account service start!
Bottle v0.12.23 server starting up (using AutoServer())...
Listening on http://127.0.0.1:8088/
Hit Ctrl-C to quit.
```

**4. Set the callback URL**

Go to your subscription account in the [WeChat Official Platform](https://mp.weixin.qq.com/) and enable server configuration:

![wx_mp_config.png](images/wx_mp_config.png)

**Server address (URL)**: if you can reach the program on your server through this URL in a browser (default port 8088), the config is valid. Since subscription accounts only allow ports 80/443, either make the program listen on port 80 directly (needs sudo) or forward it with a reverse proxy like nginx. A public IP or a domain both work here.

**Token**: must match the token in `config.json`.

For the detailed process, see the [official docs](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html).

> Note: after a user sends a message, WeChat pushes it to the configured URL, but if there's no reply within 5 seconds it disconnects and retries 3 times, while model requests often take longer than 5s. This project uses async and caching to stretch the limit to 15s, but beyond that it still can't reply in time. For time-sensitive scenarios, use the "Service Account" instead.

</details>

<a id="service-account"></a>
<details>
<summary><b>Service Account</b></summary>

**Requirements:** a server and a WeChat-verified service account.

The service account calls the model asynchronously first, then pushes the result to the user via the customer-service API, which gets around the subscription account's 15s timeout. Its developer-mode config is similar to the subscription account's — see the [official docs](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html).

In the config, just change `type` to `wechat_mp_service`, keep reusing the `wechat_mp` block, and add `app_id` and `app_secret`:

```bash
"channel": {
    "type": "wechat_mp_service",
    "wechat_mp": {
      "token": "YOUR TOKEN",            # token value
      "port": "8088",                   # port the program listens on
      "app_id": "YOUR APP ID",          # app ID
      "app_secret": "YOUR APP SECRET"   # app secret
    }
}
```

> Note: add the server IP to the "IP whitelist", otherwise users won't receive pushed messages.

</details>

<a id="qq"></a>
<details>
<summary><b>QQ</b></summary>

**Requirements:** a PC or server (mainland China network) and a QQ account.

Running a QQ bot also needs a separate `go-cqhttp` process, which handles sending and receiving QQ messages, while this project requests the model and generates replies.

**1. Download go-cqhttp**

Download the build for your system from the [go-cqhttp Release](https://github.com/Mrs4s/go-cqhttp/releases), unzip it, and put the `go-cqhttp` binary in `bot-on-anything/channel/qq`. There's already a `config.yml` there — just fill in your QQ account (account-uin).

**2. Install aiocqhttp**

Use [aiocqhttp](https://github.com/nonebot/aiocqhttp) to talk to go-cqhttp:

```bash
pip3 install aiocqhttp
```

**3. Configuration**

Just change the channel `type` in `config.json` to `qq`:

```bash
"channel": {
    "type": "qq"
}
```

**4. Running**

Terminal 1, in the project root (listens on port 8080):

```bash
python3 app.py
```

Terminal 2, in the `go-cqhttp` directory:

```bash
cd channel/qq
./go-cqhttp
```

> Note: there's no keyword matching or group whitelist yet, so all private chats get auto-replies, and in group chats it replies whenever it's @-mentioned. If you hit issues like a frozen account, change `protocol` in `device.json` from 5 to 2, see this [Issue](https://github.com/Mrs4s/go-cqhttp/issues/1942).

</details>

<a id="telegram"></a>
<details>
<summary><b>Telegram</b></summary>

Contributor: [brucelt1993](https://github.com/brucelt1993)

**1. Get the token**

You can search for how to create a Telegram bot — the key thing is getting the bot's token id.

**2. Install dependencies**

```bash
pip install pyTelegramBotAPI
```

**3. Configuration**

```bash
"channel": {
    "type": "telegram",
    "telegram":{
      "bot_token": "YOUR BOT TOKEN ID"
    }
}
```

</details>

<a id="gmail"></a>
<details>
<summary><b>Gmail</b></summary>

**Requirements:** a server and a Gmail account.

**Contributor:** [Simon](https://github.com/413675377)

Follow the [official docs](https://support.google.com/mail/answer/185833?hl=en) to create an APP password for your Google account, then configure it like below:

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

</details>

<a id="slack"></a>
<details>
<summary><b>Slack</b></summary>

**❉ No longer needs a server or public IP**

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

**Set bot token scopes** - OAuth & Permission:

```
app_mentions:read
chat:write
```

**Enable Socket Mode** - Socket Mode: if you don't have an app-level token yet, you'll be prompted to create one; put it in `slack_app_token`.

**Event Subscriptions** - Subscribe to bot events:

```
app_mention
```

Reference: [Slack Bolt for Python](https://slack.dev/bolt-python/tutorial/getting-started)

</details>

<a id="dingtalk"></a>
<details>
<summary><b>DingTalk</b></summary>

**Requirements:** an enterprise internal development bot.

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
      "port": "8081",                  # external port
      "dingtalk_token": "xx",          # access_token of the webhook URL
      "dingtalk_post_token": "xx",     # verification token in the header when DingTalk posts back
      "dingtalk_secret": "xx"          # security signing secret for the group bot
    }
  }
```

**Create the bot**

At https://open-dev.dingtalk.com/fe/app#/corp/robot , add a bot, then in the development settings fill in the server's outbound IP (run `curl ifconfig.me` on the host to get it) and the message-receiving address (the external address in your config, e.g. `https://xx.xx.com:8081`).

Reference: [DingTalk internal bot tutorial](https://open.dingtalk.com/document/tutorial/create-a-robot#title-ufs-4gh-poh) · [Enterprise internal bot tutorial](https://open.dingtalk.com/document/robots/enterprise-created-chatbot)

</details>

<a id="feishu"></a>
<details>
<summary><b>Feishu</b></summary>

**Dependencies**

```bash
pip3 install requests flask
```

**Configuration**

```bash
"channel": {
    "type": "feishu",
    "feishu": {
        "image_create_prefix": ["draw", "draw", "Draw"],
        "port": "8082",                  # external port
        "app_id": "xxx",                 # app_id
        "app_secret": "xxx",             # app secret
        "verification_token": "xxx"      # event subscription verification token
    }
}
```

**Create the bot**

At https://open.feishu.cn/app/ :

1. Add an enterprise self-built app
2. Grant permissions: `im:message`, `im:message.group_at_msg`, `im:message.group_at_msg:readonly`, `im:message.p2p_msg`, `im:message.p2p_msg:readonly`, `im:message:send_as_bot`
3. In the event subscription menu, add the event (Receive messages v2.0) and set the request URL (the external address in your config, e.g. `https://xx.xx.com:8081`)
4. Publish the app in version management; once approved, add the self-built app to your group

</details>

<a id="enterprise-wechat"></a>
<details>
<summary><b>Enterprise WeChat</b></summary>

**Requirements:** a server and a verified Enterprise WeChat.

Just change `type` in `config.json` to `wechat_com`; the default message-receiving URL is `http://ip:8888/wechat`:

```bash
"channel": {
    "type": "wechat_com",
    "wechat_com": {
      "wechat_token": "YOUR TOKEN",            # token value
      "port": "8888",                          # port the program listens on
      "app_id": "YOUR APP ID",                 # app ID
      "app_secret": "YOUR APP SECRET",         # app secret
      "wechat_corp_id": "YOUR CORP ID",
      "wechat_encoding_aes_key": "YOUR AES KEY"
    }
}
```

> Note: add the server IP to the "Enterprise trusted IP" list, otherwise users won't receive pushed messages.

Reference: [Enterprise WeChat setup tutorial](https://www.wangpc.cc/software/wechat_com-chatgpt/)

</details>

<a id="discord"></a>
<details>
<summary><b>Discord</b></summary>

Depends on [discord.py](https://github.com/Rapptz/discord.py):

```bash
pip3 install "discord.py>=2.0.0"
```

**Configuration**

```bash
"channel": {
    "type": "discord",
    "discord": {
        "app_token": "xxx",
        "channel_name": "xxx",
        "channel_session": "xxx"
    }
}
```

+ `app_token`: the Discord bot's Bot Token
+ `channel_name`: restrict the bot to a specific channel; leave empty to listen to all channels
+ `channel_session`: session granularity, `author` (per user) or `thread` (per thread)

</details>

### General Configuration

+ `clear_memory_commands`: in-chat command to clear conversation memory; use a string array to define multiple aliases
  + default: `["#clear_memory"]`

<br/>

## 🔧 Plugin System

Following the plugin design of [chatgpt-on-wechat](https://github.com/zhayujie/CowAgent/tree/master/plugins), this project is also pluginized and stays as compatible as possible with its plugin event model, so you can extend it with image generation, model selectors, and other custom logic. See the [plugin docs](plugins/README.md).

<br/>

## 📺 Video Tutorials (Chinese)

- [WeChat, QQ, Official Account, Web](https://www.bilibili.com/video/BV1KM4y167e8)
- [Enterprise WeChat, DingTalk, Feishu](https://www.bilibili.com/video/BV1yL411a7DP)

<br/>

<a id="related-projects"></a>
## 🔗 Related Projects

- **[CowAgent](https://github.com/zhayujie/CowAgent)** — our other project, upgraded to 2.0 Agent capabilities: task planning, long-term memory, knowledge base, skills, MCP, and more, also covering channels like WeChat, Feishu, DingTalk, Enterprise WeChat, QQ, Telegram, Slack, and Discord. Give it a try if you want a more complete AI assistant
- **[Cow Skill Hub](https://github.com/zhayujie/cow-skill-hub)** — an open skill marketplace for AI Agents, works with CowAgent, OpenClaw, Claude Code, and more
- **[AgentMesh](https://github.com/MinimalFuture/AgentMesh)** — an open-source multi-agent framework that solves complex problems through team collaboration

<br/>

## ⚠️ Disclaimer

1. This project is under the [MIT License](/LICENSE) and is meant for technical research and learning. Please follow the laws and regulations in your area; you are responsible for any consequences of using this project.
2. ERNIE Bot, New Bing, and Bard are accessed through their web versions and may stop working when the official policies change — they're for learning only. For production use, prefer the official APIs or LinkAI.
