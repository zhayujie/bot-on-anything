# encoding:utf-8

from model.model import Model
from config import model_conf
from common import const
from common.log import logger
import requests
import time

sessions = {}

class YiyanModel(Model):
    def __init__(self):
        self.acs_token = model_conf(const.BAIDU).get('acs_token')
        self.cookie = model_conf(const.BAIDU).get('cookie')
        self.base_url = 'https://yiyan.baidu.com/eb'

    def reply(self, query, context=None):
        logger.info("[BAIDU] query={}".format(query))
        user_id = context.get('session_id') or context.get('from_user_id')
        context['query'] = query

        # 1.create session
        chat_session_id = sessions.get(user_id)
        if not chat_session_id:
            self.new_session(context)
            sessions[user_id] = context['chat_session_id']
        else:
            context['chat_session_id'] = chat_session_id

        # 2.create chat
        flag = self.new_chat(context)
        if not flag:
            return "创建会话失败，请稍后再试"

        # 3.query
        context['reply'] = ''
        self.query(context, 0, 0)

        return context['reply']


    def new_session(self, context):
        data = {
            "sessionName": context['query'],
            "timestamp": int(time.time() * 1000),
            "deviceType": "pc"
        }
        res = requests.post(url=self.base_url+'/session/new', headers=self._create_header(), json=data)
        # print(res.headers)
        context['chat_session_id'] = res.json()['data']['sessionId']
        logger.info("[BAIDU] newSession: id={}".format(context['chat_session_id']))


    def new_chat(self, context):
        headers = self._create_header()
        headers['Acs-Token'] = self.acs_token
        data = {
            "sessionId": context.get('chat_session_id'),
            "text": context['query'],
            "parentChatId": 0,
            "type": 10,
            "timestamp": int(time.time() * 1000),
            "deviceType": "pc",
            "code": 0,
            "msg": ""
        }
        res = requests.post(url=self.base_url+'/chat/new', headers=headers, json=data).json()
        if res['code'] != 0:
            logger.error("[BAIDU] New chat error, msg={}", res['msg'])
            return False
        context['chat_id'] = res['data']['botChat']['id']
        context['parent_chat_id'] = res['data']['botChat']['parent']
        return True


    def query(self, context, sentence_id, count):
        headers = self._create_header()
        headers['Acs-Token'] = self.acs_token
        data = {
            "chatId": context['chat_id'],
            "parentChatId": context['parent_chat_id'],
            "sentenceId": sentence_id,
            "stop": 0,
            "timestamp": 1679068791405,
            "deviceType": "pc"
        }
        res = requests.post(url=self.base_url + '/chat/query', headers=headers, json=data)
        logger.debug("[BAIDU] query: sent_id={}, count={}, res={}".format(sentence_id, count, res.text))

        res = res.json()
        if res['data']['text'] != '':
            context['reply'] += res['data']['text']
            # logger.debug("[BAIDU] query: sent_id={}, reply={}".format(sentence_id, res['data']['text']))

        if res['data']['is_end'] == 1:
            return

        if count > 10:
            return

        time.sleep(1)
        if not res['data']['text']:
            return self.query(context, sentence_id, count+1)
        else:
            return self.query(context, sentence_id+1, count+1)


    def _create_header(self):
        headers = {
            'Host': 'yiyan.baidu.com',
            'Origin': 'https://yiyan.baidu.com',
            'Referer': 'https://yiyan.baidu.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Cookie': self.cookie
        }
        return headers
