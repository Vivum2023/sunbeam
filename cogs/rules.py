from discord.ext import commands
from discord.utils import find

class Rules(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command
    async def rules(self, ctx: commands.Context):
        general_chan = find(lambda x: x.name.startswith("general"), ctx.guild.channels)
        spam = find(lambda x: x.name.startswith("spam"), ctx.guild.channels)

        await ctx.send(f"""
**1.** Do not leak invites to this server without permission yet
**2.** Follow Discord Terms Of Service (https://discord.com/terms) at ALL times
**3.** This server is right now purely for VIVUM planning and communication

__**HODS**__

HOD's have extra permissions given to them. Please do not abuse these permissions. Also, please try to listen to what HOD's tell you

If you want a specific role, just ping anyone with the "Admin" role and ask. Right now, they are manually given out (though a bot may be made if required/other arrangements are possible)


__**IMPORTANT NOTES**__

- Each department has their own category with voice and text channel which can only be accessed by those departments
- The "feedback" channels can be used by anyone in case of doubts or for cross department communication
- Please keep the <#{general_chan.id}> channel as clear as possible, keep spam to the <#{spam.id}>channel
- The general voice channels are if departments need to work together 
- Note that normal users do not have "Create Invite" permissions. This is to protect against raids+invite spam and to allow more effective moderation if required (so we dont have to go through everyone's invites)

**Have fun, stay organized**
        """)

async def setup(bot: commands.Bot):
    await bot.add_cog(Rules(bot))