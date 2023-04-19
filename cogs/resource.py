import discord
from discord.ext import commands

from bot import Vivum

class Resource(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot

    @commands.hybrid_group()
    async def resource(self, _: commands.Context):
        ...
    
    @resource.command()
    @commands.has_guild_permissions(administrator=True)
    async def add(self, ctx: commands.Context, name: str, description: str, url: str):
        await self.bot.pool.execute("""
            INSERT INTO resources (name, description, url) VALUES ($1, $2, $3)
        """, name, description, url)
        await ctx.send("Resource added!")

async def setup(bot: Vivum):
    await bot.add_cog(Resource(bot))