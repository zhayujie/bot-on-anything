# encoding:utf-8

import json
from channel.http import auth
from flask import Flask, request, render_template, make_response
from datetime import timedelta
from common import const
from config import channel_conf
from channel.channel import Channel
http_app = Flask(__name__,)
# 自动重载模板文件
http_app.jinja_env.auto_reload = True
http_app.config['TEMPLATES_AUTO_RELOAD'] = True

# 设置静态文件缓存过期时间
http_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)


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
    response = make_response("<html></html>",301)
    response.headers.add_header('content-type','text/plain')
    response.headers.add_header('location','./')
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
    response.headers.set('location','./login?err=登录失败')
    return response

class HttpChannel(Channel):
    def startup(self):
        http_app.run(host='0.0.0.0', port=channel_conf(const.HTTP).get('port'))

    def handle(self, data):
        context = dict()
        id = data["id"]
        context['from_user_id'] = str(id)
        return super().build_reply_content(data["msg"], context)

