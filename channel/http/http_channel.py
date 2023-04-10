# encoding:utf-8

import asyncio
import json
from channel.http import auth
from flask import Flask, request, render_template, make_response
from datetime import timedelta
from common import const
from common import functions
from config import channel_conf
from config import channel_conf_val
from channel.channel import Channel
from flask_socketio import SocketIO
from common import log
from plugins.plugin_manager import *

http_app = Flask(__name__,)
socketio = SocketIO(http_app, close_timeout=5)
# 自动重载模板文件
http_app.jinja_env.auto_reload = True
http_app.config['TEMPLATES_AUTO_RELOAD'] = True

# 设置静态文件缓存过期时间
http_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)


async def return_stream(data):
    async for final, response in HttpChannel().handle_stream(data=data):
        try:
            if (final):
                socketio.server.emit(
                    'disconnect', {'result': response, 'final': final}, request.sid, namespace="/chat")
                disconnect()
            else:
                socketio.server.emit(
                    'message', {'result': response, 'final': final}, request.sid, namespace="/chat")
        except Exception as e:
            disconnect()
            log.warn("[http]emit:{}", e)
            break


@socketio.on('message', namespace='/chat')
def stream(data):
    if (auth.identify(request) == False):
        client_sid = request.sid
        socketio.server.disconnect(client_sid)
        return
    data = json.loads(data["data"])
    if (data):
        img_match_prefix = functions.check_prefix(
            data["msg"], channel_conf_val(const.HTTP, 'image_create_prefix'))
        if img_match_prefix:
            reply_text = HttpChannel().handle(data=data)
            socketio.emit(
                'disconnect', {'result': reply_text}, namespace='/chat')
            disconnect()
            return
        asyncio.run(return_stream(data))


@socketio.on('connect', namespace='/chat')
def connect():
    log.info('connected')
    socketio.emit('message', {'info': "connected"}, namespace='/chat')


@socketio.on('disconnect', namespace='/chat')
def disconnect():
    log.info('disconnect')
    socketio.server.disconnect(request.sid, namespace="/chat")


@http_app.route("/chat", methods=['POST'])
def chat():
    if (auth.identify(request) == False):
        return
    data = json.loads(request.data)
    if data:
        msg = data['msg']
        if not msg:
            return
        reply_text = HttpChannel().handle(data=data)
        return {'result': reply_text}


@http_app.route("/", methods=['GET'])
def index():
    if (auth.identify(request) == False):
        return login()
    return render_template('index.html')


@http_app.route("/login", methods=['POST', 'GET'])
def login():
    response = make_response("<html></html>", 301)
    response.headers.add_header('content-type', 'text/plain')
    response.headers.add_header('location', './')
    if (auth.identify(request) == True):
        return response
    else:
        if request.method == "POST":
            token = auth.authenticate(request.form['password'])
            if (token != False):
                response.set_cookie(key='Authorization', value=token)
                return response
        else:
            return render_template('login.html')
    response.headers.set('location', './login?err=登录失败')
    return response


class HttpChannel(Channel):
    def startup(self):
        http_app.run(host='0.0.0.0', port=channel_conf(const.HTTP).get('port'))

    def handle(self, data):
        context = dict()
        query = data["msg"]
        id = data["id"]
        context['from_user_id'] = str(id)
        e_context = PluginManager().emit_event(EventContext(Event.ON_HANDLE_CONTEXT, {
            'channel': self, 'context': query,  "args": context}))
        reply = e_context['reply']
        if not e_context.is_pass():
            reply = super().build_reply_content(e_context["context"], e_context["args"])
            e_context = PluginManager().emit_event(EventContext(Event.ON_DECORATE_REPLY, {
                'channel': self, 'context': context, 'reply': reply, "args": context}))
            reply = e_context['reply']
        return reply

    async def handle_stream(self, data):
        context = dict()
        id = data["id"]
        context['from_user_id'] = str(id)
        context['stream'] = True
        context['origin'] = data["msg"]
        e_context = PluginManager().emit_event(EventContext(Event.ON_HANDLE_CONTEXT, {
            'channel': self, 'context': data["msg"], 'reply': data["msg"], "args": context}))
        reply = e_context['reply']
        if not e_context.is_pass():
            async for final, reply in super().build_reply_stream(data["msg"], context):
                yield final, reply
        else:
            yield True, reply
