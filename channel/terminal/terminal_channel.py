from channel.channel import Channel
from common import log

import sys

class TerminalChannel(Channel):
    def startup(self):
        # close log
        log.close_log()
        context = {"from_user_id": "User", "stream": True}
        print("Please input your question\n")
        while True:
            try:
                prompt = self.get_input("User:\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()

            print("Bot:")
            sys.stdout.flush()
            for res in super().build_reply_content(prompt, context):
                print(res, end="")
                sys.stdout.flush()
            print("\n")


    def get_input(self, prompt):
        """
        Multi-line input function
        """
        print(prompt, end="")
        line = input()
        return line
