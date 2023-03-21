import requests
from  config import conf

class SensitiveWord:
    def __init__(self):
        # 读取配置文件
        try:
            self.config = conf()  # 加载配置文件
            #print(self.config) # 输出配置文件内容以进行调试
        except Exception as e:
            print(e)  # 打印错误信息

        # 设置请求 URL
        self.url = "https://aip.baidubce.com/rest/2.0/antispam/v2/spam"

        # 获取 access token
        self.access_token = self.get_access_token()

    def get_access_token(self):
        """
        获取百度云接口的 access token

        :return: str access token
        
        """
        
        #检测敏感词配置是否存在
        if self.config is not None and "common" in self.config and "type" in self.config["common"] and self.config["common"]["type"]:

            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.config["common"]["client_id"],
                "client_secret": self.config["common"]["client_secret"]
            }
            response = requests.post(url, params=params)
            response_json = response.json()

            access_token = response_json.get("access_token")

            if not access_token:
                raise ValueError(f"获取 access_token 失败: {response_json.get('error_description')}")
            
            print(f"Access token: {access_token}")  # 输出访问令牌以进行调试
            return access_token


    def process_text(self, text):

        #检测敏感词配置是否存在
        if self.config is not None and "common" in self.config and "sensitive" in self.config["common"] and self.config["common"]["sensitive"]:
            #存在则执行正常检测流程
            url = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"  # API 请求地址
            access_token = self.get_access_token()
            headers = {"content-type": "application/x-www-form-urlencoded"}
            params = {
                "text": text.encode("utf-8"),
                "access_token": access_token
            }
            response = requests.post(url, data=params, headers=headers)

            if response.status_code != 200:
                raise ValueError(f"无法连接到接口，请检查你的网络: {response.json().get('error_msg')}")

            conclusion_type = response.json().get("conclusionType")


            print(response.json())  # 输出完整的 API 响应结果

            if conclusion_type in [1, None]:
                return False
            else:
                return True
        #不存在则直接返回无敏感词
        else:
            return False
