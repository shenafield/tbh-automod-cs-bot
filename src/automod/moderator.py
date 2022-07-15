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


class UnsubscribeView(discord.ui.View):
    def __init__(self, config, config_reader, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.config_reader = config_reader

    @discord.ui.button(label="Unsubscribe", style=discord.ButtonStyle.gray, emoji="🔕")
    async def unsubscribe(self, button, interaction):
        self.config.moderators[f"<@{interaction.user.id}>"] = 1
        self.config_reader.write_config(self.config)
        await interaction.response.send_message("Unsubscribed", ephemeral=True)
        print(f"[moderator] {interaction.user.name} unsubscribed", flush=True)



class ModerationHandler(Handler):
    def __init__(self, completer: Completer, embed: discord.Embed, config, config_reader, treshold=0.5, questions=None, mod_channel=None, prompt_head=""):
        self.completer = completer
        self.questions = questions
        self.treshold = treshold
        self.prompt_head = prompt_head
        self.embed = embed
        self.cooldown = 60 * 15
        self.last_activated = {}
        self.results: dict[int, Trigger] = {}

        self.config = config
        self.config_reader = config_reader
        self.mod_tresholds = config.moderators
        self.mod_channel = mod_channel

    async def handle(self, release, trigger, bot=None):
        last_use = self.last_activated.get(trigger.channel.id)
        if last_use is None:
            last_use = self.last_activated[trigger.channel.id] = time.time()
        if time.time() - last_use < self.cooldown:
            # So that it doesn't react twice to the same message
            print(f"[automod] {trigger.channel.name} is on cooldown", flush=True)
            return
        chat = Chat()
        for message in release:
            chat.send(message.author.display_name, message.content)
        intervener = Intervener(self.completer, chat=chat, questions=self.questions, prompt_head=self.prompt_head)
        needed = intervener.needed
        print(f"[moderator] {trigger.chanel.name} {needed}", flush=True)
        self.results[trigger.channel.id] = Trigger(needed=needed, time=time.time())
        if needed > self.treshold:
            await self.respond(trigger.channel)
            self.last_activated[trigger.channel.id] = time.time()
            print(f"[moderator] {trigger.chanel.name} triggered", flush=True)
        if self.mod_channel is not None:
            if bot:
                for moderator, treshold in self.mod_tresholds.items():
                    if needed > treshold:
                        channel = await bot.fetch_channel(self.mod_channel)
                        await channel.send(f"{moderator} needs to intervene on {trigger.channel.mention} ({needed*100:.2f}%)", view=UnsubscribeView(self.config, self.config_reader))
                        print(f"[moderator] {moderator} pinged for {trigger.channel.name}", flush=True)

    async def respond(self, channel):
        await channel.send(embed=self.embed)
