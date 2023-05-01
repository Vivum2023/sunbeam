import ruamel.yaml
import discord
from discord.ext import commands
import config
from cogs.data.layout import Layout
from bot import Vivum

discord.utils.setup_logging(root=True)

yaml = ruamel.yaml.YAML()

with open("config.yaml") as f:
    cfg = config.Config.parse_obj(yaml.load(f))

with open("cogs/data/layout.yaml") as f:
    layout_obj = Layout.parse_obj(yaml.load(f))

bot = Vivum(cfg, layout_obj)

@bot.check
async def enabled(ctx: commands.Context):
    if not bot.config.disabled:
        return True

    if not ctx.command:
        return True

    if ctx.command.name in bot.config.disabled:
        return False
    return True

bot.run(bot.config.token, log_handler=None)