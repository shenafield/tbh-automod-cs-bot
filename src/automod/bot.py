import json
import os

import discord
from discord.ext import commands
from dotenv import find_dotenv
from dotenv import load_dotenv

from .complete import Completer
from .moderator import ModerationHandler
from .slow_chat_packager import PackagerCog
from .utils import UtilsCog


def main():
    load_dotenv(find_dotenv(usecwd=True))

    embed = discord.Embed(
        color=0x3B4252,
        title=os.getenv("EMBED_TITLE"),
        description=os.getenv("EMBED_DESCRIPTION"),
    )
    embed.set_footer(text=os.getenv("EMBED_FOOTER"))

    bot = commands.Bot("!")
    completer = Completer(os.getenv("AI21_TOKEN"), "j1-jumbo")
    handler = ModerationHandler(
        completer,
        embed,
        treshold=float(os.getenv("TRESHOLD", 0.5)),
        questions=os.getenv("EMBED_QUESTION"),
    )
    bot.add_cog(
        PackagerCog(bot, handler, keywords=tuple(os.getenv("KEYWORDS", "").split(", ")))
    )
    bot.add_cog(UtilsCog(bot, handler))
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
