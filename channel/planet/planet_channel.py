# encoding:utf-8

import requests
import time
from channel.channel import Channel
from common.log import  logger
from config import channel_conf, channel_conf_val
from common import const

MENTION_STR = '<e type=\"mention\" uid=\"815111251481452\" title=\"@ueno\" \/>'
MENTION_STR2 = '<e type="mention" uid="815111251481452" title="@ueno" />'

class PlanetChannel(Channel):
    def startup(self):
        self.group_id = channel_conf_val(const.PLANTE, "group_id")
        self.cookie = channel_conf_val(const.PLANTE, "cookie")
        self.bot_user_id = channel_conf_val(const.PLANTE, "bot_user_id")
        self._fetch_and_handle_topics()

    def _fetch_and_handle_topics(self):
        while True:
            try:
                questions = self._get_topics("unanswered_questions")
                if questions and len(questions) > 0:
                    logger.info("[Planet] find new question, content={}".format(questions))

                    # 遍历未解决问题列表，回答问题
                    for question in questions:
                        question_id = question["topic_id"]
                        question_text = question["question"]['text']
                        user_id = question["question"]["owner"]["user_id"]
                        logger.info("[Planet] find new question, content={}, user_id={}".format(question_text, user_id))

                        # 获取答案
                        context = {"from_user_id": user_id}
                        reply_txt = super().build_reply_content(question_text, context)

                        # 发布答案
                        self._send_reply(question_id, reply_txt)
                    time.sleep(10)

                # 处理主题
                topics = self._get_topics("all")
                for topic in topics:
                    try:
                        self._handle_topic(topic)
                    except Exception as e:
                        logger.warn("[Planet] process topic failed, exception={}".format(e))
                    time.sleep(0.5)
                time.sleep(30)

            except Exception as e:
                logger.exception("[Planet] process failed, exception={}".format(e))


    def _handle_topic(self, topic):
        if not topic.get('talk'):
            return
        talk_content = topic['talk']['text']
        talk_user_id = str(topic['talk']['owner']['user_id'])
        logger.info("[Planet] handle topic, user_id={}, content={}".format(talk_user_id, talk_content))
        # 主题自动回复
        if talk_content.find(self.bot_user_id) != -1 and not self._has_topic_reply(topic):
            logger.info("[Planet] find new topic, topic={}".format(topic))
            # 场景一：用户直接在主题上艾特
            query = talk_content.replace(MENTION_STR, '')
            query = query.replace(MENTION_STR2, '')

            # 此时system_prompt使用全局配置, query为主题中的问题
            context = {"from_user_id": talk_user_id}
            reply_txt = super().build_reply_content(query, context)

            # 直接回复主题
            self._send_comment(topic['topic_id'], reply_txt)
            return

        comment_list = topic.get('show_comments')
        if not comment_list or len(comment_list) <= 0:
            return

        comment_map = {}
        for comment in comment_list:
            comment_map[str(comment['comment_id'])] = comment

        # 评论自动回复
        for comment in comment_list:
            # 场景二：机器人自己发的帖子，只要有没有被回复的，都立即回复
            # 场景三：用户发的帖子，评论中有艾特机器人，且没有被回复的
            query = comment['text']
            comment_user_id = str(comment['owner']['user_id'])
            # 是机器人的主题 || @了机器人 || 回复了机器人
            if talk_user_id == self.bot_user_id or query.find(self.bot_user_id) != -1 or self._is_reply_bot(comment_map, comment):
                if self._has_comment_reply(comment_list, comment) or self.bot_user_id == comment_user_id:
                    # 已经被评论过 或 是自己的评论
                    continue
                if query.find(self.bot_user_id) != -1:
                    query = query.replace(MENTION_STR, '')
                    query = query.replace(MENTION_STR2, '')

                context = {"from_user_id": comment_user_id}
                reply_txt = super().build_reply_content(query, context)
                self._send_comment(topic['topic_id'], reply_txt, comment['comment_id'])
                logger.info("[Planet] comment success, id={}".format(comment['comment_id']))
                return


        logger.info("[Planet] no topic need reply")

    def _is_reply_bot(self, comment_map, comment):
        # 是否是回复机器人的评论
        if comment.get('repliee'):
            return str(comment['repliee']['user_id']) == self.bot_user_id
        return False

    def _has_topic_reply(self, topic):

        if not topic.get('show_comments') or len(topic['show_comments']) <= 0:
            return False

        for comment in topic['show_comments']:
            if str(comment['owner']['user_id']) == self.bot_user_id:
                return True

        return False

    def _has_comment_reply(self, comment_list, cur_comment):
        user_id = cur_comment['owner']['user_id']
        for i in range(0, len(comment_list)):
            if cur_comment['comment_id'] == comment_list[i]['comment_id']:
                for j in range(i+1, len(comment_list)):
                    comment = comment_list[j]
                    if comment['owner']['user_id'] == int(self.bot_user_id) and comment.get('repliee') and \
                        comment.get('repliee')['user_id'] == user_id:
                        # 在用户回复机器人的后面，有一条机器人回复用户的，则表示已经回复过了
                        return True
        return False


    # 访问知识星球API，获取问题列表
    def _get_topics(self, scope):
        questions_url = f"https://api.zsxq.com/v2/groups/{self.group_id}/topics?scope={scope}&count=20"
        response = requests.get(questions_url, headers=self._create_header())
        if response.status_code == 200:
            try:
                questions_data = response.json()["resp_data"]["topics"]
            except:
                logger.error("[Planet] get topic failed, res={}".format(response.text))
                questions_data = []
            return questions_data
        else:
            print("Unable to get questions data.")
            return []


    # 访问知识星球API，回答问题
    def _send_reply(self, question_id, answer):
        post_answer_url = f"https://api.zsxq.com/v2/topics/{question_id}/answer"
        response = requests.post(post_answer_url, headers=self._create_header(), json={
            "req_data":{
                "image_ids": [],
                "silenced": True,
                "text": answer
            }
        })
        if (response.status_code == 200) and (response.json()['succeeded']):
            logger.info("[Planet] Answer posted successfully!")
        else:
            logger.info("Unable to post answer, res=" + response.text)


    # 访问知识星球API，评论
    def _send_comment(self, topic_id, answer, replied_comment_id=None):
        data = {
            "req_data": {
                "image_ids": [],
                "mentioned_user_ids": [],
                "text": answer
            }
        }
        if replied_comment_id:
            data['req_data']['replied_comment_id'] = replied_comment_id
        post_answer_url = f"https://api.zsxq.com/v2/topics/{topic_id}/comments"
        response = requests.post(post_answer_url, headers=self._create_header(), json=data)
        if (response.status_code == 200) and (response.json()['succeeded']):
            logger.info("[Planet] Comment posted successfully!")
        else:
            logger.info("Unable to post comment, res=" + response.text)


    def _create_header(self):
        return {"cookie": f"{self.cookie}",
                   "origin": "https://wx.zsxq.com",
                   "referer": "https://wx.zsxq.com/",
                   "sec-ch-ua-platform": "Windows",
                   "Content-Type": "application/json; charset=UTF-8",
                   "user_agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36"
                }
