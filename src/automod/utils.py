import time

import discord
import humanize
from discord.ext import commands

from .slow_chat_packager import Handler


class UtilsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, handler: Handler):
        self.bot = bot
        self.handler = handler

    @commands.slash_command(description="Get the last evaluation for this channel")
    async def check(self, context):
        evaluation = self.handler.results.get(context.channel.id)
        if evaluation is None:
            embed = discord.Embed(
                title="Evaluation",
                description=f"There haven't been any recent evaluations",
            )
            await context.respond(embed=embed, ephemeral=True)
            return
        delta_seconds = time.time() - evaluation.time
        delta = humanize.naturaldelta(delta_seconds)
        embed = discord.Embed(
            title="Evaluation",
            description=f"Last evaluation: {round(evaluation.needed*100, 2)}% ({delta} ago)",
        )
        await context.respond(embed=embed, ephemeral=True)
