import time
from dataclasses import dataclass

import discord
from discord.ext import commands

from .complete import Completer
from .intervener import Chat
from .intervener import Intervener
from .slow_chat_packager import Handler


@dataclass
class Trigger:
    needed: float
    time: float


class ModerationHandler(Handler):
    def __init__(self, completer: Completer, embed: discord.Embed, treshold=0.5, questions=None, prompt_head=""):
        self.completer = completer
        self.questions = questions
        self.treshold = treshold
        self.prompt_head = prompt_head
        self.embed = embed
        self.cooldown = 60 * 15
        self.last_activated = {}
        self.results: dict[int, Trigger] = {}

    async def handle(self, release, trigger):
        last_use = self.last_activated.get(trigger.channel.id)
        if last_use is None:
            last_use = self.last_activated[trigger.channel.id] = time.time()
        if time.time() - last_use < self.cooldown:
            # So that it doesn't react twice to the same message
            print("We're on cooldown")
            return
        chat = Chat()
        for message in release:
            chat.send(message.author.display_name, message.content)
        intervener = Intervener(self.completer, chat=chat, questions=self.questions, prompt_head=self.prompt_head)
        needed = intervener.needed
        print(needed)
        self.results[trigger.channel.id] = Trigger(needed=needed, time=time.time())
        if needed > self.treshold:
            await self.respond(trigger.channel)
            self.last_activated[trigger.channel.id] = time.time()

    async def respond(self, channel):
        await channel.send(embed=self.embed)
