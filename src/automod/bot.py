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
from .config import JsonConfigReader, Config


def main():
    load_dotenv(find_dotenv(usecwd=True))

    head_path = os.getenv("PRPOMPT_HEAD")
    if head_path is None:
        head = ""
    else:
        head = open(head_path).read()

    embed = discord.Embed(
        color=0x3B4252,
        title=os.getenv("EMBED_TITLE"),
        description=os.getenv("EMBED_DESCRIPTION"),
    )
    embed.set_footer(text=os.getenv("EMBED_FOOTER"))

    config_reader = JsonConfigReader(os.getenv("CONFIG_PATH", "config.json"))
    config = config_reader.read_config()

    bot = commands.Bot("!", intents=discord.Intents.all())
    completer = Completer(os.getenv("AI21_TOKEN"), "j1-jumbo")
    handler = ModerationHandler(
        completer,
        embed,
        config,
        config_reader,
        treshold=float(os.getenv("TRESHOLD", 0.5)),
        questions=os.getenv("EMBED_QUESTION"),
        mod_channel=os.getenv("MOD_CHANNEL"),
        prompt_head=head,
    )
    bot.add_cog(
        PackagerCog(bot, handler, keywords=tuple(os.getenv("KEYWORDS", "").split(", ")))
    )
    bot.add_cog(UtilsCog(bot, handler, config, config_reader, os.getenv("MOD_ANNOUNCEMENT_CHANNEL")))
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
