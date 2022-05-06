from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta

import discord
from discord.ext import commands


class Handler(ABC):
    @abstractmethod
    async def handle(self, release, message):
        pass


class PingHandler(Handler):
    async def handle(self, release, message):
        await message.channel.send("handled")


@dataclass
class Package:
    last_release: float = 0
    max_wait: float = 15 * 60  # We will not consider messages older than 15 minutes
    min_wait: float = 30  # We will not consider chats that lasted under half a minute
    frequency: float = 120  # We will not evaluate more than once every two minutes
    min_messages: int = 5  # We will not analyze dead chats

    async def release(self, channel):
        messages = await channel.history(
            oldest_first=True, after=datetime.now() - timedelta(seconds=self.max_wait)
        ).flatten()
        if len(messages) < self.min_messages:
            return
        last_message_date = messages[-1].created_at
        # Make sure there's enough to analyze
        if (last_message_date - messages[0].created_at).total_seconds() < self.min_wait:
            return
        # Make sure we aren't analyzing too frequently
        if last_message_date.timestamp() - self.last_release < self.frequency:
            return
        # Trigger the release
        self.last_release = last_message_date.timestamp()
        return messages


class PackagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, handler: Handler):
        self.bot = bot
        self.packages = {}
        self.handler = handler

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            package = self.packages.get(message.channel.id, Package())
            release = await package.release(message.channel)
            self.packages[message.channel.id] = package
            if release is not None:
                await self.handler.handle(release, message)
