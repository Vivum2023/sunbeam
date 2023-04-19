import uuid
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
        count = await self.bot.pool.fetchval("SELECT COUNT(*) FROM resources")

        if count >= 10:
            return await ctx.send("You can only have 10 resources at a time due to embed limitations.")

        id = uuid.uuid4()
        await self.bot.pool.execute("""
            INSERT INTO resources (id, name, description, url) VALUES ($1, $2, $3, $4)
        """, id, name, description, url)
        await ctx.send("Resource added!")
    
    @resource.command()
    @commands.has_guild_permissions(administrator=True)
    async def listid(self, ctx: commands.Context):
        ids = await self.bot.pool.fetch("SELECT id, name, description, url FROM resources")

        embeds = []
        for id in ids:
            embed = discord.Embed(title=id["name"], description=id["description"])   
            embed.add_field(name="ID", value=id["id"])  
            embed.add_field(name="Description", value=id["description"])
            embed.add_field(name="URL", value=id["url"])
            embeds.append(embed)
        
        await ctx.send(embeds=embeds)
    
    @resource.command()
    async def list(self, ctx: commands.Context):
        res = await self.bot.pool.fetch("SELECT name, description, url FROM resources")

        msg = ""
        for r in res:
            msg += f"**{r['name']}:**\n*{r['description']}*\n\n{r['url']}\n\n\n"
        
        await ctx.send(msg, suppress_embeds=True)

    @resource.command()
    @commands.has_guild_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, id: uuid.UUID):
        await self.bot.pool.execute("DELETE FROM resources WHERE id = $1", id)
        await ctx.send("Resource removed!")

async def setup(bot: Vivum):
    await bot.add_cog(Resource(bot))