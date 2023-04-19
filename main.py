import os
import ruamel.yaml
import discord
from discord.ext import commands
import config as config
import logging 

logging.getLogger().setLevel(logging.INFO)

yaml = ruamel.yaml.YAML()

with open("config.yaml") as f:
    config.CONFIG = config.Config.parse_obj(yaml.load(f))

bot = commands.Bot(command_prefix=config.CONFIG.prefix, intents=discord.Intents.all())

@bot.event
async def on_ready():
    try:
        await bot.load_extension("jishaku")
    except commands.ExtensionAlreadyLoaded:
        pass

    # For every file in the cogs folder, load it
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            try:
                logging.info(f"Loading extension {file}...")
                await bot.load_extension(f"cogs.{file[:-3]}")
            except commands.ExtensionAlreadyLoaded:
                pass
            except Exception as e:
                logging.info(f"Failed to load extension {file}: {e}")

    logging.info("Ready!")

@bot.check
async def enabled(ctx: commands.Context):
    if not config.CONFIG.disabled:
        return True
    if ctx.command.name in config.CONFIG.disabled:
        return False
    return True

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CheckFailure):
        return await ctx.send("This command is disabled.")
    raise error

@bot.hybrid_command(name="buildserver") 
@commands.is_owner()
async def buildserver(ctx: commands.Context):
    await ctx.send("Building server channels, please wait...")

    chans = {
        "Logistics": "logistics",
        "Security": "security",
        "Vendor Acquisition": "vendor",
        "Sports": "sports",
        "Dance": "dance",
        "Stage Management": "stage",
        "Finance": "finance",
        "Music": "music",
        "Fun Activities": "fun",
        "Drama": "drama",
        "Fundraising": "fundraising",
        "Distribution": "dist",
        "Social Media": "smm",
        "Merchandise": "merch",
    }

    protected_cats = [
        "information",
        "general"
    ]

    protected_roles = [
        "sudo",
        "admin",
        "tech support",
        "everyone"
    ]

    # Delete all channels not in protected_cats
    await ctx.send("**Step 1: Cleanup Channels**")
    for chan in ctx.guild.channels:
        if isinstance(chan, discord.CategoryChannel):
            if chan.name.lower() not in protected_cats:
                await chan.delete()
            continue

        if chan.category is not None and chan.category.name.lower() in protected_cats:
            continue
        await chan.delete()
    
    # Cleanup roles as well
    await ctx.send("**Step 1.5: Cleanup Roles**")
    for role in ctx.guild.roles:
        if role.name.lower() in protected_roles or role == ctx.guild.default_role:
            continue     

        try:
            await role.delete()
        except Exception as e:
            await ctx.send(f"Failed to delete role {role.name} [cleanup]: {e}, likely normal")

    await ctx.send("**Step 2: Create new roles and channels**")

    await ctx.guild.create_role(name="HOD")

    for name, chan_name in chans.items():
        await ctx.send(f"Creating department {name}...")
        role = await ctx.guild.create_role(name=name)

        cat = await ctx.guild.create_category(name, overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=False,
                connect=False
            ),
            role: discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=True,
                connect=True
            ),
        })
        your_dep = await ctx.guild.create_text_channel(f"in-{chan_name}", category=cat, overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        })

        await your_dep.send(f"If you can see this channel, it means that you are a part of the '{name}' department!")

        await ctx.guild.create_text_channel(chan_name, category=cat)
        await ctx.guild.create_voice_channel(name, category=cat)
        await ctx.guild.create_text_channel(f"{chan_name}-feedback", category=cat, overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        })

bot.run(config.CONFIG.token)