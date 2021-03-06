import time

import discord
import humanize
from discord.ext import commands

from .slow_chat_packager import Handler
from .config import ConfigReader, Config


class SetSensitivityModal(discord.ui.Modal):
    def __init__(self, config, config_reader, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.__config = config
        self.__config_reader = config_reader
        self.add_item(discord.ui.InputText(label="Sensitivity  threshold (0-100)"))

    async def callback(self, interaction: discord.Interaction):
        try:
            result = float(self.children[0].value)/100
            if result < 0 or result > 1:
                raise ValueError("Sensitivity threshold must be between 0 and 100")
        except ValueError:
            await interaction.response.send_message("Invalid sensitivity threshold", ephemeral=True)
            return
        original = self.__config.moderators.get(f"<@{interaction.user.id}>")
        self.__config.moderators[f"<@{interaction.user.id}>"] = result
        self.__config_reader.write_config(self.__config)
        await interaction.response.send_message(f"Sensitivity threshold set to {result} (previously {original})", ephemeral=True)
        print(f"[moderator] {interaction.user} set sensitivity threshold to {result}", flush=True)


class SetSensitivityView(discord.ui.View):
    def __init__(self, config, config_reader, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.config_reader = config_reader

    @discord.ui.button(label="Set alert sensitivity", style=discord.ButtonStyle.primary, emoji="🔔")
    async def set_sensitivity(self, button, interaction):
        await interaction.response.send_modal(SetSensitivityModal(self.config, self.config_reader, title="Set alert sensitivity"))


class UtilsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, handler: Handler, config: Config, config_reader: ConfigReader, mod_announcement_channel):
        self.bot = bot
        self.handler = handler
        self.config = config
        self.config_reader = config_reader
        self.mod_announcement_channel = mod_announcement_channel

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

    @commands.Cog.listener()
    async def on_ready(self):
        if self.mod_announcement_channel:
            view = SetSensitivityView(self.config, self.config_reader)
            mod_announcement_channel = await self.bot.fetch_channel(self.mod_announcement_channel)
            if self.config.mod_message:
                try:
                    message = await mod_announcement_channel.fetch_message(self.config.mod_message)
                    await message.edit(view=view)
                    return
                except discord.NotFound:
                    pass
            mod_announcement_message_text = "Click here to be alerted about me detecting a suspicious message\n\n" + \
                    "This will prompt you to set a sensitivity threshold for the detection.\n" + \
                    "The lower the sensitivity threshold, the more sensitive the detection is.\n" + \
                    "The higher the sensitivity threshold, the less sensitive the detection is.\n" + \
                    "You'd usually want to set it to somewhere around 40-50%.\n" + \
                    "You can set it to 100 to disable the detection entirely.\n" + \
                    "You can see how the detection is currently working by using the `/check` command."
            message = await mod_announcement_channel.send(mod_announcement_message_text, view=view)
            self.config.mod_message = message.id
            self.config_reader.write_config(self.config)
