import discord
from discord.ext import commands

from bot import Vivum

class Admin(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def buildserver(self, ctx: commands.Context):
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
            "everyone",
            "vc"
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

async def setup(bot: Vivum):
    await bot.add_cog(Admin(bot))