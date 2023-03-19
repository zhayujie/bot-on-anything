# encoding:utf-8

import jwt
import datetime
import time
from flask import jsonify, request
from common import const
from config import channel_conf


class Auth():
    def __init__(self, login):
    # argument 'privilegeRequired' is to set up your method's privilege
    # name
        self.login = login
        super(Auth, self).__init__()

    @staticmethod
    def encode_auth_token(user_id, login_time):
        """
        生成认证Token
        :param user_id: int
        :param login_time: datetime
        :return: string
        """
        try:
            payload = {
                'iss': 'ken',  # 签名
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=10),  # 过期时间
                'iat': datetime.datetime.utcnow(),  # 开始时间
                'data': {
                    'id': user_id,
                    'login_time': login_time
                }
            }
            return jwt.encode(
                payload,
                channel_conf(const.HTTP).get('http_auth_secret_key'),
                algorithm='HS256'
            )  # 加密生成字符串
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        验证Token
        :param auth_token:
        :return: integer|string
        """
        try:
            # 取消过期时间验证
            payload = jwt.decode(auth_token, channel_conf(const.HTTP).get(
                'http_auth_secret_key'), algorithms='HS256')  # options={'verify_exp': False} 加上后不验证token过期时间
            if ('data' in payload and 'id' in payload['data']):
                return payload
            else:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return 'Token过期'
        except jwt.InvalidTokenError:
            return '无效Token'


def authenticate(password):
    """
    用户登录，登录成功返回token
    :param password:
    :return: json
    """
    authPassword = channel_conf(const.HTTP).get('http_auth_password')
    if (authPassword != password):
        return False
    else:
        login_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        token = Auth.encode_auth_token(password, login_time)
        return token


def identify(request):
    """
    用户鉴权
    :return: list
    """
    try:
        authPassword = channel_conf(const.HTTP).get('http_auth_password')
        if (not authPassword):
            return True
        if (request is None):
            return False
        authorization = request.cookies.get('Authorization')
        if (authorization):
            payload = Auth.decode_auth_token(authorization)
            if not isinstance(payload, str):
                authPassword = channel_conf(
                    const.HTTP).get('http_auth_password')
                password = payload['data']['id']
                if (password != authPassword):
                    return False
                else:
                    return True
        return False
 
    except jwt.ExpiredSignatureError:
        #result = 'Token已更改，请重新登录获取'
        return False
 
    except jwt.InvalidTokenError:
        #result = '没有提供认证token'
        return False
