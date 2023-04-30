from channel.channel import Channel
from common import log

import sys

class TerminalChannel(Channel):
    def startup(self):
        # close log
        log.close_log()
        context = {"from_user_id": "User", "stream": True}
        print("\nPlease input your question")
        while True:
            try:
                prompt = self.get_input("User:\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit()
            
            if prompt.startswith("#绘画："):
                context['type'] = 'IMAGE_CREATE'
                prompt = prompt.replace("#绘画：","",1)

            print("Bot:")
            sys.stdout.flush()
            if context.get('type', None) == 'IMAGE_CREATE':
                print("\n")
                for res in super().build_reply_content(prompt, context):
                    print(res)
                    sys.stdout.flush()
            else:
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
