import time

import discord
from discord.ext import commands

from .complete import Completer
from .intervener import Chat
from .intervener import Intervener
from .slow_chat_packager import Handler


class ModerationHandler(Handler):
    def __init__(self, completer: Completer, embed, treshold=0.5, questions=None):
        self.completer = completer
        self.questions = questions
        self.treshold = treshold
        self.embed = embed
        self.cooldown = 60 * 15
        self.last_activated = {}

    async def handle(self, release, trigger):
        if time.time() - self.last_activated.get(trigger.channel.id, 0) < self.cooldown:
            # So that it doesn't react twice to the same message
            print("We're on cooldown")
            return
        chat = Chat()
        for message in release:
            chat.send(message.author.display_name, message.content)
        intervener = Intervener(self.completer, chat=chat, questions=self.questions)
        needed = intervener.needed
        print(needed)
        if needed > self.treshold:
            await self.respond(trigger.channel)
            self.last_activated[trigger.channel.id] = time.time()

    async def respond(self, channel):
        await channel.send(embed=self.embed)
