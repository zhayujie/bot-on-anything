# encoding:utf-8

"""
discord channel
Python discord - https://github.com/Rapptz/discord.py.git
"""
from channel.channel import Channel
from common.log import logger
from config import conf, common_conf_val, channel_conf
import ssl
import discord
from discord.ext import commands

class DiscordChannel(Channel):

    def __init__(self):
        config = conf()
        
        self.token = channel_conf('discord').get('app_token')
        self.discord_channel_name = channel_conf('discord').get('channel_name')
        self.discord_channel_session = channel_conf('discord').get('channel_session', 'author')
        self.voice_enabled = channel_conf('discord').get('voice_enabled', False)
        self.cmd_clear_session = common_conf_val('clear_memory_commands', ['#清除记忆'])[0]
        self.sessions = []
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.guilds = True
        self.intents.members = True
        self.intents.messages = True
        self.intents.voice_states = True
        
        context = ssl.create_default_context()
        context.load_verify_locations(common_conf_val('certificate_file'))
        self.bot = commands.Bot(command_prefix='!', intents=self.intents, ssl=context)
        self.bot.add_listener(self.on_ready)

        logger.debug('cmd_clear_session %s', self.cmd_clear_session)

    def startup(self):
        self.bot.add_listener(self.on_message)
        self.bot.add_listener(self.on_guild_channel_delete)
        self.bot.add_listener(self.on_guild_channel_create)
        self.bot.add_listener(self.on_private_channel_delete)
        self.bot.add_listener(self.on_private_channel_create)
        self.bot.add_listener(self.on_channel_delete)
        self.bot.add_listener(self.on_channel_create)
        self.bot.add_listener(self.on_thread_delete)
        self.bot.add_listener(self.on_thread_create)
        self.bot.run(self.token)

    async def on_ready(self):
        logger.info('Bot is online user:{}'.format(self.bot.user))
        if self.voice_enabled == False: 
            logger.debug('disable music')
            await self.bot.remove_cog("Music")
    
    async def join(self, ctx):
        logger.debug('join %s', repr(ctx))
        channel = ctx.author.voice.channel
        await channel.connect()

    async def _do_on_channel_delete(self, channel):
        if not self.discord_channel_name or channel.name != self.discord_channel_name:
            logger.debug('skip _do_on_channel_delete %s', channel.name)
            return
        
        for name in self.sessions:
            try:
                response = self.send_text(name, self.cmd_clear_session)
                logger.debug('_do_on_channel_delete %s %s', channel.name, response)
            except Exception as e:
                logger.warn('clear session except, id:%s', name)

        self.sessions.clear()

    async def on_guild_channel_delete(self, channel):
        logger.debug('on_guild_channel_delete %s', repr(channel))
        await self._do_on_channel_delete(channel)
    
    async def on_guild_channel_create(self, channel):
        logger.debug('on_guild_channel_create %s', repr(channel))

    async def on_private_channel_delete(self, channel):
        logger.debug('on_channel_delete %s', repr(channel))
        await self._do_on_channel_delete(channel)
    
    async def on_private_channel_create(self, channel):
        logger.debug('on_channel_create %s', repr(channel))

    async def on_channel_delete(self, channel):
        logger.debug('on_channel_delete %s', repr(channel))
    
    async def on_channel_create(self, channel):
        logger.debug('on_channel_create %s', repr(channel))

    async def on_thread_delete(self, thread):
        print('on_thread_delete', thread)
        if self.discord_channel_session != 'thread' or thread.parent.name != self.discord_channel_name:
            logger.debug('skip on_thread_delete %s', thread.id)
            return
        
        try:
            response = self.send_text(thread.id, self.cmd_clear_session)
            if thread.id in self.sessions:
                self.sessions.remove(thread.id)
            logger.debug('on_thread_delete %s %s', thread.id, response)
        except Exception as e:
            logger.warn('on_thread_delete except %s', thread.id)
            raise e
            

    async def on_thread_create(self, thread):
        logger.debug('on_thread_create %s', thread.id) 
        if self.discord_channel_session != 'thread' or thread.parent.name != self.discord_channel_name:
            logger.debug('skip on_channel_create %s', repr(thread))
            return
        
        self.sessions.append(thread.id)

    async def on_message(self, message):
        """
        listen for message event
        """
        await self.bot.wait_until_ready()
        if not self.check_message(message):
            return
 
        prompt = message.content.strip();
        logger.debug('author: %s', message.author)
        logger.debug('prompt: %s', prompt)

        session_id = message.author
        if self.discord_channel_session == 'thread' and isinstance(message.channel, discord.Thread):
            logger.debug('on_message thread id %s', message.channel.id)
            session_id = message.channel.id

        await message.channel.send('...')
        response = response = self.send_text(session_id, prompt)
        await message.channel.send(response)


    def check_message(self, message):
        if message.author == self.bot.user:
            return False
        
        prompt = message.content.strip();
        if not prompt:
            logger.debug('no prompt author: %s', message.author)
            return False
   
        if self.discord_channel_name:
            if isinstance(message.channel, discord.Thread) and message.channel.parent.name == self.discord_channel_name:
                return True
            if not isinstance(message.channel, discord.Thread) and self.discord_channel_session != 'thread' and message.channel.name == self.discord_channel_name:
                return True
            
            logger.debug("The accessed channel does not meet the discord channel configuration conditions.")
            return False
        else:
            return True
        
    def send_text(self, id, content):
        context = dict()
        context['type'] = 'TEXT'
        context['from_user_id'] = id
        context['content'] = content
        return super().build_reply_content(content, context)