from discord.ext import commands
from bot import Vivum

class Web(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot
    
    @commands.hybrid_command()
    async def web(self, ctx: commands.Context):
        """Sends the link to the website"""
        await ctx.send(f"Please see {self.bot.config.website} for a superior experience running certain basic commands (finance etc.)")

async def setup(bot: Vivum):
    await bot.add_cog(Web(bot))