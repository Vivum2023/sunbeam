import discord
from discord.ext import commands
from bot import Vivum

class Listeners(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        admin_chat = discord.utils.get(member.guild.text_channels, name="admin-chat")

        if not admin_chat:
            return await member.send("Welcome to the server! Seems like something critical is going on with channels right now. Please DM any 'Tech Support' user that 'admin-chat' is non-existant :eyes:")

        # Check if they are in a assigned department
        row = await self.bot.pool.fetchrow("SELECT name, role_name, is_hod FROM users WHERE user_id = $1", str(member.id))

        if not row:
            # Send a message in #general pinging them and return
            welcome_channel: discord.TextChannel | None = discord.utils.get(member.guild.text_channels, name="welcome")

            request_roles: discord.TextChannel | None = discord.utils.get(member.guild.text_channels, name="request-roles")

            if welcome_channel:
                if request_roles:
                    await welcome_channel.send(f"Welcome {member.mention}! Please head to {request_roles.mention} to request a role!")
                else:
                    await admin_chat.send(f"Error handling {member.mention}! Seems like somethings going on with channels right now ('request-roles' not found @Sudo @Tech Support @Admin :eyes:)")
            else:
                await admin_chat.send(f"Error handling {member.mention}! Seems like somethings going on with channels right now. ('welcome' not found @Sudo @Tech Support @Admin :eyes:)")
        else:
            # Assign them the role
            roles_to_add = []

            role: discord.Role | None = discord.utils.get(member.guild.roles, name=row["role_name"])

            if role:
                roles_to_add.append(role)
            else:
                await admin_chat.send(f"Error handling {member.mention}! Seems like somethings going on with roles right now (the '{row['role_name']}' role is non-existant @Sudo @Tech Support @Admin :eyes:)")

            if row["is_hod"]:
                hod: discord.Role | None = discord.utils.get(member.guild.roles, name="HOD")

                if hod:
                    roles_to_add.append(hod)
                else:
                    await admin_chat.send(f"Error handling {member.mention}! Seems like somethings going on with roles right now. (the 'HOD' role is non-existant @Sudo @Tech Support @Admin :eyes:)")

            await member.add_roles(*roles_to_add, reason="Auto-assigning roles")

            await member.edit(nick=row["name"], reason="Set nickname properly")

            # Send a message in #general pinging them and return
            welcome_channel: discord.TextChannel | None = discord.utils.get(member.guild.text_channels, name="welcome")
            
            if welcome_channel:
                await welcome_channel.send(f"Welcome {member.mention}! DW, as you are already in the '{row['role_name']}' department with hod={row['is_hod']}, you have already been assigned your roles :heart:")
            else:
                await admin_chat.send(f"Error handling {member.mention}! Seems like somethings going on with channels right now. ('welcome' not found @Sudo @Tech Support @Admin :eyes:)")

async def setup(bot: Vivum):
    await bot.add_cog(Listeners(bot))