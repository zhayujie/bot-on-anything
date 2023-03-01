# 简介

将 **AI 模型** 接入各类 **消息应用**，开发者通过轻量配置即可在二者之间选择一条连线，运行起一个智能对话机器人，在一个项目中轻松完成多条链路的切换。该架构扩展性强，每接入一个应用可复用已有的算法能力，同样每接入一个模型也可作用于所有应用之上。

**模型：**

- [x] [ChatGPT](https://github.com/zhayujie/bot-on-anything#1chatgpt)

**应用：**

- [x] [终端](https://github.com/zhayujie/bot-on-anything#1%E5%91%BD%E4%BB%A4%E8%A1%8C%E7%BB%88%E7%AB%AF)
- [ ] Web
- [x] [个人微信](https://github.com/zhayujie/bot-on-anything#2%E4%B8%AA%E4%BA%BA%E5%BE%AE%E4%BF%A1)
- [x] [订阅号](https://github.com/zhayujie/bot-on-anything#3%E4%B8%AA%E4%BA%BA%E8%AE%A2%E9%98%85%E5%8F%B7)
- [x] [服务号](https://github.com/zhayujie/bot-on-anything#4%E4%BC%81%E4%B8%9A%E6%9C%8D%E5%8A%A1%E5%8F%B7)
- [ ] 企业微信
- [x] [Telegram](https://github.com/zhayujie/bot-on-anything#6telegram)
- [x] [QQ](https://github.com/zhayujie/bot-on-anything#5qq)
- [ ] 钉钉
- [ ] 飞书
- [x] [Gmail](https://github.com/zhayujie/bot-on-anything#7gmail)
- [x] [Slack](https://github.com/zhayujie/bot-on-anything#8slack)

# 快速开始

## 一、准备

### 1.运行环境

支持 Linux、MacOS、Windows 系统（Linux 服务器上可长期运行)。同时需安装 Python，建议 Python 版本在 3.7.1~3.10 之间。

项目代码克隆：

```bash
git clone https://github.com/zhayujie/bot-on-anything
cd bot-on-anything/
```

> 或在 Realase 直接手动下载源码。

### 2.配置说明

核心配置文件为 `config.json`，在项目中提供了模板文件 `config-template.json` ，可以从模板复制生成最终生效的 `config.json` 文件：

```bash
cp config-template.json config.json
```

每一个模型和应用都有自己的配置块，最终组成完整的配置文件，整体结构如下：

```bash
{
  "model": {
    "type" : "openai",              # 选用的算法模型
    "openai": {
      # openAI配置
    }
  },
  "channel": {
    "type": "wechat_mp",            # 需要接入的应用
    "wechat": {
        # 个人微信配置
    },
    "wechat_mp": {
        # 公众号配置
    }
  }
}
```

配置文件在最外层分成 `model` 和 `channel` 两部分，model 部分为模型配置，其中的 `type` 指定了选用哪个模型；channel 部分包含了应用渠道的配置，`type` 字段指定了接入哪个应用。

在使用时只需要更改 model 和 channel 配置块下的 type 字段，即可在任意模型和应用间完成切换，连接不同的通路。下面将依次介绍各个 模型 及 应用 的配置和运行过程。

## 二、选择模型

### 1.ChatGPT

#### 1.1 注册 OpenAI 账号

前往 [OpenAI 注册页面](https://beta.openai.com/signup) 创建账号，参考这篇 [教程](https://www.cnblogs.com/damugua/p/16969508.html) 可以通过虚拟手机号来接收验证码。创建完账号则前往 [API 管理页面](https://beta.openai.com/account/api-keys) 创建一个 API Key 并保存下来，后面需要在项目中配置这个 key。

> 项目中使用的对话模型是 davinci，计费方式是约每 750 字 (包含请求和回复) 消耗 $0.02，图片生成是每张消耗 $0.016，账号创建有免费的 $18 额度，使用完可以更换邮箱重新注册。

#### 1.2 安装依赖

```bash
pip3 install --upgrade openai
```

> 注： 如果安装失败可先升级 pip， `pip3 install --upgrade pip`

#### 1.3 配置项说明

```bash
{
  "model": {
    "type" : "openai",

    "openai": {
      "api_key": "YOUR API KEY",
      "conversation_max_tokens": 1000,
      "character_desc": "你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。"
    }
}
```

- `api_key`：填入上面注册账号时创建的 `OpenAI API KEY`
- `conversation_max_tokens`：表示能够记忆的上下文最大字数（一问一答为一组对话，如果累积的对话字数超出限制，就会优先移除最早的一组对话）
- `character_desc` 配置中保存着你对机器人说的一段话，他会记住这段话并作为他的设定，你可以为他定制任何人格

## 三、选择应用

### 1.命令行终端

配置模板中默认启动的应用即是终端，无需任何额外配置，直接在项目目录下通过命令行执行 `python3 app.py` 便可启动程序。用户通过命令行的输入与对话模型交互，且支持流式响应效果。

![terminal_demo.png](docs/images/terminal_demo.png)

### 2.个人微信

与项目 [chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat) 的使用方式相同，目前接入个人微信可能导致账号被限制，暂时不建议使用。

配置项说明：

```bash
"channel": {
    "type": "wechat",

    "single_chat_prefix": ["bot", "@bot"],
    "single_chat_reply_prefix": "[bot] ",
    "group_chat_prefix": ["@bot"],
    "group_name_white_list": ["ChatGPT测试群"],
    "image_create_prefix": ["画", "看", "找一张"],

    "wechat": {
    }
}
```

个人微信的配置项放在和 `type` 同级的层次，表示这些为公共配置，会复用于其他应用。配置加载时会优先使用模块内的配置，如果未找到便使用公共配置。

在项目根目录下执行 `python3 app.py` 即可启动程序，用手机扫码后完成登录，使用详情参考 [chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat)。

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

**服务器地址 (URL) 配置**： 如果在浏览器上通过配置的 URL 能够访问到服务器上的 Python 程序 (默认监听 8088 端口)，则说明配置有效。由于公众号只能配置 80/443 端口，可以修改配置为直接监听 80 端口 (需要 sudo 权限)，或者使用反向代理进行转发 (如 nginx)。 根据官方文档说明，此处填写公网 ip 或域名均可。

**令牌 (Token) 配置**：需和 `config.json` 配置中的 token 一致。

详细操作过程参考 [官方文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html)

#### 2.3 使用

用户关注订阅号后，发送消息即可。

> 注：用户发送消息后，微信后台会向配置的 URL 地址推送，但如果 5s 内未回复就会断开连接，同时重试 3 次，但往往请求 openai 接口不止 5s。本项目中通过异步和缓存将 5s 超时限制优化至 15s，但超出该时间仍无法正常回复。 同时每次 5s 连接断开时 web 框架会报错，待后续优化。

### 4.企业服务号

**需要：** 一个服务器、一个已微信认证的服务号

在企业服务号中，通过先异步访问 openai 接口，再通过客服接口主动推送给用户的方式，解决了个人订阅号的 15s 超时问题。服务号的开发者模式配置和上述订阅号类似，详情参考 [官方文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Getting_Started_Guide.html)。

企业服务号的 `config.json` 配置只需修改 type 为`wechat_mp_service`，但配置块仍复用 `wechat_mp`，在此基础上需要增加 `app_id` 和 `app_secret` 两个配置项。

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

注意：需将服务器 ip 地址配置在 "IP 白名单" 内，否则用户将收不到主动推送的消息。

### 5.QQ

需要：一台 PC 或服务器 (国内网络)、一个 QQ 号

运行 qq 机器人 需要额外运行一个`go-cqhttp` 程序，cqhttp 程序负责接收和发送 qq 消息， 我们的`bot-on-anything`程序负责访问`openai`生成对话内容。

#### 5.1 下载 go-cqhttp

在 [go-cqhttp 的 Release](https://github.com/Mrs4s/go-cqhttp/releases) 中下载对应机器的程序，解压后将 `go-cqhttp` 二进制文件放置在我们的 `bot-on-anything/channel/qq` 目录下。 同时这里已经准备好了一个 `config.yml` 配置文件，仅需要填写其中的 QQ 账号配置 (account-uin)。

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

首先进入 `bot-on-anything` 项目根目录，在 终端 1 运行：

```bash
python3 app.py    # 此时会监听8080端口
```

第二步打开 终端 2，进入到放置 `cqhttp` 的目录并运行：

```bash
cd channel/qq
./go-cqhttp
```

注意：目前未设置任何 关键词匹配 及 群聊白名单，对所有私聊均会自动回复，在群聊中只要被@也会自动回复。

### 6.Telegram

Contributor: [brucelt1993](https://github.com/brucelt1993)

**6.1 获取 token**

telegram 机器人申请可以自行谷歌下，很简单，重要的是获取机器人的 token id。

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

### 7.Gmail

需要: 一个服务器、一个 Gmail account

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

### 8.Slack

**需要：** 服务器、 Slack 应用

**Contributor:** [amao](https://github.com/amaoo)

**依赖**

```bash
pip3 install slack_bolt flask
```

**配置**

```bash
"channel": {
    "type": "slack",
    "slack": {
      "slack_bot_token": "xoxb-xxxx",
      "slack_signing_secret": "xxxx"
    }
  }
```

需要 80 端口,可以在 **channel/slack/slack_channel.py:45** 修改相应端口

将范围设置为机器人令牌范围 OAuth & Permission:

```
app_mentions:read
channels:join
chat:write
im:history
im:read
im:writ
```

在事件订阅中设置范围 - Subscribe to bot events

```
app_mention
```

订阅 URL，如果端口是 80 ，可不填

```
http:/你的固定公网ip或者域名:端口/slack/events
```

参考文档

```
https://slack.dev/bolt-python/tutorial/getting-started
```
