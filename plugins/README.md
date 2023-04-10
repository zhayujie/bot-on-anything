# 简介

按 **[chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins)** 插件的思路对 **bot-on-anything** 进行插件化，期望能实现插件的共享使用，但是由于两个项目的架构存在较大差异，只能尽最大可能兼容 **[chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins)** 的插件，部分功能还需进行适配。


 
## **插件监听的事件：**

事件顺序为 1、ON_HANDLE_CONTEXT  -->  2、ON_BRIDGE_HANDLE_CONTEXT(ON_BRIDGE_HANDLE_STREAM_CONTEXT)  -->  3、ON_DECORATE_REPLY


触发事件会产生事件的上下文EventContext，它可能包含了以下信息:

EventContext(Event事件类型, {'channel' : 本次消息的context, 'context': 本次消息用户的提问, 'reply': 当前AI回复, "args": 其他上下文参数})

插件处理函数可通过修改EventContext中的context、reply、args或者调用channel中对应的方法来实现功能。


```
class Event(Enum):

    ON_HANDLE_CONTEXT = 2   # 对应通道处理消息前
    """
    e_context = {  "channel": 消息channel,  "context" : 本次消息的context, "reply" : 目前的回复，初始为空 , "args": 其他上下文参数 }
    """

    ON_DECORATE_REPLY = 3   # 得到回复后准备装饰
    """
    e_context = {  "channel": 消息channel,  "context" : 本次消息的context, "reply" : 目前的回复 , "args": 其他上下文参数 }
    """

    ON_SEND_REPLY = 4       # 发送回复前
    """
    bot-on-anything 不支持ON_SEND_REPLY事件,请使用ON_BRIDGE_HANDLE_CONTEXT或者ON_BRIDGE_HANDLE_STREAM_CONTEXT事件
    """

    ON_BRIDGE_HANDLE_CONTEXT = 6   # 模型桥处理消息前
    """
    e_context = { "context" : 本次消息的context, "reply" : 目前的回复，初始为空 , "args": 其他上下文参数 , 模型桥会调用args.model指定的AI模型来进行回复 }
    """

    ON_BRIDGE_HANDLE_STREAM_CONTEXT = 7   # 模型桥处理流式消息前,流式对话的消息处理仅支持一次性返回,请直接返回结果
    """
    e_context = {  "context" : 本次消息的context, "reply" : 目前的回复，初始为空 , "args": 其他上下文参数 , 模型桥会调用args.model指定的AI模型来进行回复 }
    """

```

## 插件编写示例

以`plugins/selector`为例，其中编写了一个通过判断前缀调用不同模型的`Selector`插件。

### 1. 创建插件

在`plugins`目录下创建一个插件文件夹`selector`。然后，在该文件夹中创建同名``selector.py``文件。

```
plugins/
└── selector
    └── selector.py
```

### 2. 编写功能

在`selector.py`文件中，创建插件类`Selector`，它继承自`Plugin`。

在类定义之前需要使用`@plugins.register`装饰器注册插件，并填写插件的相关信息，其中`desire_priority`表示插件默认的优先级，越大优先级越高。`Selector`插件加载时读取了同目录下的`selector.json`文件,从中取出对应的模型和触发前缀，`Selector`插件为事件`ON_HANDLE_CONTEXT`和`ON_BRIDGE_HANDLE_STREAM_CONTEXT`绑定了一个处理函数`select_model`，它表示在模型桥调用指定模型之前，都会先由`select_model`函数预处理。

```python
@plugins.register(name="Selector", desire_priority=99, hidden=True, desc="A model selector", version="0.1", author="RegimenArsenic")
class Selector(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        try:
            self.config = functions.load_json_file(curdir, "selector.json")
        except Exception as e:
            log.warn("[Selector] init failed")
            raise e
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.select_model
        self.handlers[Event.ON_BRIDGE_HANDLE_STREAM_CONTEXT] = self.select_model
        log.info("[Selector] inited")
```

### 3. 编写事件处理函数

#### 修改事件上下文

事件处理函数接收一个`EventContext`对象`e_context`作为参数。`e_context`包含了事件相关信息，利用`e_context['key']`来访问这些信息。

`EventContext(Event事件类型, {'channel' : 消息channel, 'context': Context, 'reply': Reply , "args": 其他上下文参数})`

处理函数中通过修改`e_context`对象中的事件相关信息来实现所需功能，比如更改`e_context['reply']`中的内容可以修改回复，更改`e_context['context']`中的内容可以修改用户提问。

#### 决定是否交付给下个插件或默认逻辑

在处理函数结束时，还需要设置`e_context`对象的`action`属性，它决定如何继续处理事件。目前有以下三种处理方式：

- `EventAction.CONTINUE`: 事件未结束，继续交给下个插件处理，如果没有下个插件，则交付给默认的事件处理逻辑。
- `EventAction.BREAK`: 事件结束，不再给下个插件处理，交付给默认的处理逻辑。
- `EventAction.BREAK_PASS`: 事件结束，不再给下个插件处理，跳过默认的处理逻辑。

#### 示例处理函数

`Selector`插件通过判断前缀，如有`@bing`前缀,则修改调用模型为bing模型，若前缀为`@gpt`，则修改调用模型为chatgpt，否则就使用app里配置的原始模型插件，同时删去提问的前缀`@bing`或者`@gpt`

```python
    def select_model(self, e_context: EventContext):
        model=e_context['args'].get('model')
        for selector in self.config.get("selector", []):
            prefix = selector.get('prefix', [])
            check_prefix=functions.check_prefix(e_context["context"], prefix)
            if (check_prefix):
                model=selector.get('model')
                if isinstance(check_prefix, str):
                    e_context["context"] = e_context["context"].split(check_prefix, 1)[1].strip()
                break
        log.debug(f"[Selector] select model {model}")
        e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑
        e_context['args']['model']=model
        return e_context
```