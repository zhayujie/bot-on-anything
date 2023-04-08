
import json
import random
import requests
import re
class BardBot:
    BARD_URL = "https://bard.google.com/"
    BARD_CHAT_URL = (
        "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
    )
    HEADERS = {
        "Host": "bard.google.com",
        "X-Same-Domain": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://bard.google.com",
        "Referer": "https://bard.google.com/",
    }

    def __init__(self, session_id: str):
        self._reqid = random.randrange(10000,99999)
        self.conversation_id = ""
        self.response_id = ""
        self.choice_id = ""
        self.session = requests.Session()
        self.session.headers = self.HEADERS
        self.session.cookies.set("__Secure-1PSID", session_id)
        self.SNlM0e = self.__get_snlm0e()

    def __get_snlm0e(self) -> str:
        resp = self.session.get(url=self.BARD_URL, timeout=10)
        if resp.status_code != 200:
            raise Exception("Failed to connect Google Bard")
        try:
            SNlM0e = re.search(r"SNlM0e\":\"(.*?)\"", resp.text).group(1)
            return SNlM0e
        except Exception as e:
            raise Exception(f"Cookies may be wrong:{e}")

    def ask(self, message: str) -> dict[str, str]:
        params = {
            "bl": "boq_assistant-bard-web-server_20230326.21_p0",
            "_reqid": str(self._reqid),
            "rt": "c",
        }
        message_struct = [[message], None, [self.conversation_id, self.response_id, self.choice_id]]
        data = {"f.req": json.dumps([None, json.dumps(message_struct)]), "at": self.SNlM0e}
        try:
            resp = self.session.post(self.BARD_CHAT_URL, params=params, data=data)
            content = json.loads(resp.content.splitlines()[3])[0][2]
            if not (content := json.loads(resp.content.splitlines()[3])[0][2]):
                return {"content": f"Bard encountered an error: {resp.content}."} 
            json_data = json.loads(content)
            results = {
                "content": json_data[0][0],
                "conversation_id": json_data[1][0],
                "response_id": json_data[1][1],
                "reference": json_data[3],
                "choices": [{"id": i[0], "content": i[1]} for i in json_data[4]],
            }
            self.conversation_id = results['conversation_id']
            self.response_id = results['response_id']
            self.choice_id = results["choices"][0]["id"]
            self._reqid += 100000
            return results
        except Exception as e:
            raise Exception(f"Failed to ask Google Bard:{e}")