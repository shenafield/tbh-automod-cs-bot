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
    keyword_frequency: float = 20  # However, when we see a keyword we will not wait
    keywords: tuple[str] = ()
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
        frequency = (
            self.keyword_frequency
            if any(keyword in messages[-1].content for keyword in self.keywords)
            else self.frequency
        )
        # Make sure we aren't analyzing too frequently
        if last_message_date.timestamp() - self.last_release < frequency:
            return
        # Trigger the release
        self.last_release = last_message_date.timestamp()
        return messages


class PackagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, handler: Handler, keywords: tuple[str] = ()):
        self.bot = bot
        self.packages = {}
        self.handler = handler
        self.keywords = keywords

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            package = self.packages.get(
                message.channel.id, Package(keywords=self.keywords)
            )
            release = await package.release(message.channel)
            self.packages[message.channel.id] = package
            if release is not None:
                await self.handler.handle(release, message)
