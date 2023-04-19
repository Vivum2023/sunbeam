import ruamel.yaml
import discord
from discord.ext import commands
import config
from bot import Vivum

discord.utils.setup_logging(root=True)

yaml = ruamel.yaml.YAML()

with open("config.yaml") as f:
    cfg = config.Config.parse_obj(yaml.load(f))

bot = Vivum(cfg)

@bot.check
async def enabled(ctx: commands.Context):
    if not bot.config.disabled:
        return True
    if ctx.command.name in config.CONFIG.disabled:
        return False
    return True

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CheckFailure):
        return await ctx.send("This command is disabled.")
    raise error

bot.run(bot.config.token, log_handler=None)