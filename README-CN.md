<p align="center"><img src= "https://github.com/user-attachments/assets/8db79567-3cc5-47cc-9855-296ef20130e8" alt="Bot-On-Anything" width="600" /></p>

<p align="center">
   <a href="https://github.com/zhayujie/bot-on-anything/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/bot-on-anything" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/bot-on-anything/blob/master/LICENSE"><img src="https://img.shields.io/github/license/zhayujie/bot-on-anything" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/bot-on-anything"><img src="https://img.shields.io/github/stars/zhayujie/bot-on-anything?style=flat-square" alt="Stars"></a> <br/>
    [<a href="/README.md">English</a>] | [<a href="/docs/README-CN.md">中文</a>]
</p>

**Bot on Anything** 是一个开箱即用的AI对话机器人构建引擎，可以基于各种大模型快速构建智能助手，并集成到各种应用渠道中。

# 介绍

开发者通过轻量的配置即可在多种AI大模型和应用渠道之间选择一条连线，构建并运行起一个智能对话机器人，支持在一个项目中轻松完成多条链路的切换。该架构具有很强的扩展性，每接入一个应用可复用已有的模型能力，同样每一个新的模型也可运行于所有应用q渠道之上。

**模型：**

 - [x] [ChatGPT](https://github.com/zhayujie/bot-on-anything#1-chatgpt)
 - [ ] [Claude](https://github.com/zhayujie/bot-on-anything)
 - [ ] [Gemini](https://github.com/zhayujie/bot-on-anything)

**应用：**

 - [x] [终端](https://github.com/zhayujie/bot-on-anything#1%E5%91%BD%E4%BB%A4%E8%A1%8C%E7%BB%88%E7%AB%AF)
 - [x] [Web](https://github.com/zhayujie/bot-on-anything#9web)
 - [x] [订阅号](https://github.com/zhayujie/bot-on-anything#3%E4%B8%AA%E4%BA%BA%E8%AE%A2%E9%98%85%E5%8F%B7)
 - [x] [服务号](https://github.com/zhayujie/bot-on-anything#4%E4%BC%81%E4%B8%9A%E6%9C%8D%E5%8A%A1%E5%8F%B7)
 - [x] [企业微信](https://github.com/zhayujie/bot-on-anything#12%E4%BC%81%E4%B8%9A%E5%BE%AE%E4%BF%A1)
 - [x] [Telegram](https://github.com/zhayujie/bot-on-anything#6telegram)
 - [x] [QQ](https://github.com/zhayujie/bot-on-anything#5qq)
 - [x] [钉钉](https://github.com/zhayujie/bot-on-anything#10%E9%92%89%E9%92%89)
 - [x] [飞书](https://github.com/zhayujie/bot-on-anything#11%E9%A3%9E%E4%B9%A6)
 - [x] [Gmail](https://github.com/zhayujie/bot-on-anything#7gmail)
 - [x] [Slack](https://github.com/zhayujie/bot-on-anything#8slack)

# 快速开始

### 1.运行环境

支持 Linux、MacOS、Windows 系统，同时需安装 Python，建议Python版本在 3.7.1~3.10 之间。

项目代码克隆和安装依赖：

```bash
git clone https://github.com/zhayujie/bot-on-anything
cd bot-on-anything/
pip3 install -r requirements.txt
```

### 2.配置说明

核心配置文件为 `config.json`，在项目中提供了模板文件 `config-template.json` ，可以从模板复制生成最终生效的 `config.json` 文件：

```bash
cp config-template.json config.json
```

每一个模型和渠道都有自己的配置块，最终组成完整的配置文件，整体结构如下：

```bash
{
  "model": {
    "type" : "openai",             # 选用的AI模型
    "openai": {
      # openAI配置
    }
  },
  "channel": {
    "type": "slack",            # 需要接入的渠道
    "slack": {
        # slack配置
    },
    "telegram": {
        # telegram配置
    }
  }
}
```
配置文件在最外层分成 `model` 和 `channel` 两部分，model部分为模型配置，其中的 `type` 指定了选用哪个模型；channel部分包含了应用渠道的配置，`type` 字段指定了接入哪个应用。

在使用时只需要更改 model 和 channel 配置块下的 type 字段，即可在任意模型和应用间完成切换，连接不同的通路。下面将依次介绍各个 模型 及 应用 的配置和运行过程。

### 3.运行

在项目根目录下运行以下指令，默认渠道为终端：

```bash
python3 app.py
```



## 二、选择模型

### 1. ChatGPT

默认模型是 `gpt-3.5-turbo`，详情参考[官方文档](https://platform.openai.com/docs/guides/chat)，同样支持`gpt-4.0`，只需修改model type参数即可。

#### (1) 安装依赖

```bash
pip3 install --upgrade openai
```
> 注： openai版本需要`0.27.0`以上。如果安装失败可先升级pip，`pip3 install --upgrade pip`


#### (2) 配置项说明

```bash
{
  "model": {
    "type" : "chatgpt",
    "openai": {
      "api_key": "YOUR API KEY",
      "model": "gpt-3.5-turbo",                         # 模型名称
      "proxy": "http://127.0.0.1:7890",                 # 代理地址
      "character_desc": "你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。当问起你是谁的时候，要附加告诉提问人，输入 #清除记忆 可以开始新的话题探索。输入 画xx 可以为你画一张图片。",
      "conversation_max_tokens": 1000,                  # 回复最大的字符数，为输入和输出的总数
      "temperature":0.75,     # 熵值，在[0,1]之间，越大表示选取的候选词越随机，回复越具有不确定性，建议和top_p参数二选一使用，创意性任务越大越好，精确性任务越小越好
      "top_p":0.7,            #候选词列表。0.7 意味着只考虑前70%候选词的标记，建议和temperature参数二选一使用
      "frequency_penalty":0.0,            # [-2,2]之间，该值越大则越降低模型一行中的重复用词，更倾向于产生不同的内容
      "presence_penalty":1.0,             # [-2,2]之间，该值越大则越不受输入限制，将鼓励模型生成输入中不存在的新词，更倾向于产生不同的内容
    }
}
```
 + `api_key`: 填入上面注册账号时创建的 `OpenAI API KEY`
 + `model`: 模型名称，目前支持填入 `gpt-3.5-turbo`, `gpt-4`, `gpt-4-32k`  (其中gpt-4 api暂未开放)
 + `proxy`: 代理客户端的地址，详情参考  [#56](https://github.com/zhayujie/bot-on-anything/issues/56)
 + `character_desc`: 配置中保存着你对chatgpt说的一段话，他会记住这段话并作为他的设定，你可以为他定制任何人格
 + `max_history_num`[optional]: 对话最大记忆长度，超过该长度则清理前面的记忆。

---

### 2.LinkAI

#### 配置项说明
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
      "character_desc": "你是一位智能助手。"
    },
}
```

+ `api_key`: LinkAI服务调用的密钥，可在 [控制台](https://link-ai.tech/console/interface) 创建
+ `app_code`: LinkAI 应用或工作流的code，选填，参考[应用创建](https://docs.link-ai.tech/platform/create-app)
+ `model`: 支持国内外常见模型，参考[模型列表](https://docs.link-ai.tech/platform/api/chat#models) ，可以留空，在[LinKAI平台](https://link-ai.tech/console/factory) 修改应用的默认模型即可
+ 其他参数含义与ChatGPT模型一致

## 三、选择渠道

### 1.命令行终端

配置模板中默认启动的应用即是终端，无需任何额外配置，直接在项目目录下通过命令行执行 `python3 app.py` 便可启动程序。用户通过命令行的输入与对话模型交互，且支持流式响应效果。

![terminal_demo.png](docs/images/terminal_demo.png)

---

### 2.Web

**Contributor:** [RegimenArsenic](https://github.com/RegimenArsenic)

**依赖**

```bash
pip3 install PyJWT flask flask_socketio
```

**配置**

```bash
"channel": {
    "type": "http",
    "http": {
      "http_auth_secret_key": "6d25a684-9558-11e9-aa94-efccd7a0659b",    //jwt认证秘钥
      "http_auth_password": "6.67428e-11",        //认证密码,仅仅只是自用,最初步的防御别人扫描端口后DDOS浪费tokens
      "port": "80"       //端口
    }
  }
```

本地运行：`python3 app.py`运行后访问 `http://127.0.0.1:80`

服务器运行：部署后访问 `http://公网域名或IP:端口`

---

### 3.个人订阅号

**需要：** 一台服务器，一个订阅号

#### 3.1 依赖安装

安装 [werobot](https://github.com/offu/WeRoBot) 依赖：

```bash
pip3 install werobot
```

#### 3.2 配置

```bash
"channel": {
    "type": "wechat_mp",

    "wechat_mp": {
      "token": "YOUR TOKEN",           # token值
      "port": "8088"                   # 程序启动监听的端口
    }
}
```

#### 3.3 运行程序

在项目目录下运行 `python3 app.py`，终端显示如下则表示已成功运行：

```
[INFO][2023-02-16 01:39:53][app.py:12] - [INIT] load config: ...
[INFO][2023-02-16 01:39:53][wechat_mp_channel.py:25] - [WX_Public] Wechat Public account service start!
Bottle v0.12.23 server starting up (using AutoServer())...
Listening on http://127.0.0.1:8088/
Hit Ctrl-C to quit.
```

#### 2.2 设置公众号回调地址

在 [微信公众平台](https://mp.weixin.qq.com/) 中进入个人订阅号，启用服务器配置：

![wx_mp_config.png](docs/images/wx_mp_config.png)

**服务器地址 (URL) 配置**： 如果在浏览器上通过配置的URL 能够访问到服务器上的Python程序 (默认监听8088端口)，则说明配置有效。由于公众号只能配置 80/443端口，可以修改配置为直接监听 80 端口 (需要sudo权限)，或者使用反向代理进行转发 (如nginx)。 根据官方文档说明，此处填写公网ip或域名均可。

**令牌 (Token) 配置**：需和 `config.json` 配置中的token一致。

详细操作过程参考 [官方文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html)


#### 2.3 使用

用户关注订阅号后，发送消息即可。

> 注：用户发送消息后，微信后台会向配置的URL地址推送，但如果5s内未回复就会断开连接，同时重试3次，但往往请求openai接口不止5s。本项目中通过异步和缓存将5s超时限制优化至15s，但超出该时间仍无法正常回复。 同时每次5s连接断开时web框架会报错，待后续优化。

---

### 4.企业服务号

**需要：** 一个服务器、一个已微信认证的服务号

在企业服务号中，通过先异步访问openai接口，再通过客服接口主动推送给用户的方式，解决了个人订阅号的15s超时问题。服务号的开发者模式配置和上述订阅号类似，详情参考 [官方文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html)。

企业服务号的 `config.json` 配置只需修改type为`wechat_mp_service`，但配置块仍复用 `wechat_mp`，在此基础上需要增加 `app_id` 和 `app_secret` 两个配置项。

```bash
"channel": {
    "type": "wechat_mp_service",

    "wechat_mp": {
      "token": "YOUR TOKEN",            # token值
      "port": "8088",                   # 程序启动监听的端口
      "app_id": "YOUR APP ID",          # app ID
      "app_secret": "YOUR APP SECRET"   # app secret
    }
}
```

注意：需将服务器ip地址配置在 "IP白名单" 内，否则用户将收不到主动推送的消息。

---

### 5.QQ

需要：一台PC或服务器 (国内网络)、一个QQ号

运行qq机器人 需要额外运行一个`go-cqhttp` 程序，cqhttp程序负责接收和发送qq消息， 我们的`bot-on-anything`程序负责访问`openai`生成对话内容。

#### 5.1 下载 go-cqhttp

在 [go-cqhttp的Release](https://github.com/Mrs4s/go-cqhttp/releases) 中下载对应机器的程序，解压后将 `go-cqhttp` 二进制文件放置在我们的 `bot-on-anything/channel/qq` 目录下。 同时这里已经准备好了一个 `config.yml` 配置文件，仅需要填写其中的 QQ 账号配置 (account-uin)。

#### 5.2 安装 aiocqhttp

使用 [aiocqhttp](https://github.com/nonebot/aiocqhttp) 来与 go-cqhttp 交互， 执行以下语句安装依赖：

```bash
pip3 install aiocqhttp
```

#### 5.3 配置

只需修改 `config.json` 配置文件 channel 块中的 type 为 `qq`：

```bash
"channel": {
    "type": "qq"
}
```

#### 5.4 运行

首先进入 `bot-on-anything` 项目根目录，在 终端1 运行：

```bash
python3 app.py    # 此时会监听8080端口
```

第二步打开 终端2，进入到放置 `cqhttp` 的目录并运行：

```bash
cd channel/qq
./go-cqhttp
```
注意：
+ 目前未设置任何 关键词匹配 及 群聊白名单，对所有私聊均会自动回复，在群聊中只要被@也会自动回复。
+ 如果出现 账号被冻结 等异常提示，可将 go-cqhttp 同目录下的 device.json 文件中`protocol`的值由5改为2，参考该[Issue](https://github.com/Mrs4s/go-cqhttp/issues/1942)。

---

### 6.Telegram

Contributor: [brucelt1993](https://github.com/brucelt1993)

**6.1 获取token**

telegram 机器人申请可以自行谷歌下，很简单，重要的是获取机器人的token id。



**6.2 依赖安装**

pip install pyTelegramBotAPI

**6.3 配置**

```bash
"channel": {
    "type": "telegram",
    "telegram":{
      "bot_token": "YOUR BOT TOKEN ID"
    }
}
```
---

### 7.Gmail

需要: 一个服务器、一个Gmail account

**Contributor:** [Simon](https://github.com/413675377)

Follow [官方文档](https://support.google.com/mail/answer/185833?hl=en) to create APP password for google account, config as below, then cheers!!!

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

### 8.Slack

**❉不再需要服务器以及公网 IP**

**Contributor:** [amaoo](https://github.com/amaoo)

**依赖**

```bash
pip3 install slack_bolt
```

**配置**

```bash
"channel": {
    "type": "slack",
    "slack": {
      "slack_bot_token": "xoxb-xxxx",
      "slack_app_token": "xapp-xxxx"
    }
  }
```

**设置机器人令牌范围 - OAuth & Permission**

将 Bot User OAuth Token 写入配置文件 slack_bot_token

```
app_mentions:read
chat:write
```


**开启 Socket 模式 - Socket Mode**

如未创建应用级令牌，会提示创建
将创建的 token 写入配置文件 slack_app_token


**事件订阅(Event Subscriptions) - Subscribe to bot events**

```
app_mention
```


**参考文档**

```
https://slack.dev/bolt-python/tutorial/getting-started
```

---

### 10.钉钉

**需要：**

- 企业内部开发机器人

**依赖**

```bash
pip3 install requests flask
```
**配置**

```bash
"channel": {
    "type": "dingtalk",
    "dingtalk": {
      "image_create_prefix": ["画", "draw", "Draw"],
      "port": "8081",                  # 对外端口
      "dingtalk_token": "xx",          # webhook地址的access_token
      "dingtalk_post_token": "xx",     # 钉钉post回消息时header中带的检验token
      "dingtalk_secret": "xx"          # 安全加密加签串,群机器人中
    }
  }
```
**参考文档**：

- [钉钉内部机器人教程](https://open.dingtalk.com/document/tutorial/create-a-robot#title-ufs-4gh-poh)
- [自定义机器人接入文档](https://open.dingtalk.com/document/tutorial/create-a-robot#title-ufs-4gh-poh)
- [企业内部开发机器人教程文档](https://open.dingtalk.com/document/robots/enterprise-created-chatbot)

**生成机器人**

地址: https://open-dev.dingtalk.com/fe/app#/corp/robot
添加机器人,在开发管理中设置服务器出口 ip (在部署机执行`curl ifconfig.me`就可以得到)和消息接收地址(配置中的对外地址如 https://xx.xx.com:8081)

添加机器人,在开发管理中设置服务器出口ip(在部署机执行curl ifconfig.me就可以得到)和消息接收地址(配置中的对外地址如 https://xx.xx.com:8081)

---

### 11.飞书

**依赖**

```bash
pip3 install requests flask
```
**配置**

```bash
"channel": {
    "type": "feishu",
    "feishu": {
        "image_create_prefix": [
            "画",
            "draw",
            "Draw"
        ],
        "port": "8082",                  # 对外端口
        "app_id": "xxx",                 # 应用app_id
        "app_secret": "xxx",             # 应用Secret
        "verification_token": "xxx"      # 事件订阅 Verification Token
    }
}
```

**生成机器人**

地址: https://open.feishu.cn/app/
1. 添加企业自建应用
2. 开通权限
    - im:message
    - im:message.group_at_msg
    - im:message.group_at_msg:readonly
    - im:message.p2p_msg
    - im:message.p2p_msg:readonly
    - im:message:send_as_bot
3. 订阅菜单添加事件(接收消息v2.0) 配置请求地址(配置中的对外地址如 https://xx.xx.com:8081)
4. 版本管理与发布中上架应用,app中会收到审核信息,通过审核后在群里添加自建应用

---

### 12.企业微信

**需要：** 一个服务器、一个已认证的企业微信。

企业微信的 `config.json` 配置只需修改type为`wechat_com`，默认接收消息服务器URL：http://ip:8888/wechat

```bash
"channel": {
    "type": "wechat_com",
    "wechat_com": {
      "wechat_token": "YOUR TOKEN",            # token值
      "port": "8888",                          # 程序启动监听的端口
      "app_id": "YOUR APP ID",                 # app ID
      "app_secret": "YOUR APP SECRET"          # app secret
      "wechat_corp_id": "YOUR CORP ID"
      "wechat_encoding_aes_key": "YOUR AES KEY"
    }
}
```

注意：需将服务器ip地址配置在 "企业可信IP" 内，否则用户将收不到主动推送的消息。

**参考文档**：

- [企业微信配置教程](https://www.wangpc.cc/software/wechat_com-chatgpt/)

### 通用配置

+ `clear_memory_commands`: 对话内指令，主动清空前文记忆，字符串数组可自定义指令别名。
  + default: ["#清除记忆"]

# 教程

1.视频教程 (微信、QQ、公众号、Web网页)：https://www.bilibili.com/video/BV1KM4y167e8

2.视频教程 (企业微信、钉钉、飞书)：https://www.bilibili.com/video/BV1yL411a7DP
