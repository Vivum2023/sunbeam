import asyncio
import logging
import discord
from discord.ext import commands, tasks

from bot import Vivum
from config import roles, protected_roles

class Admin(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot
        self.sanity_check.start()
    
    @commands.hybrid_command()
    @commands.has_guild_permissions(administrator=True)
    async def userlist(self, ctx: commands.Context):
        users = await self.bot.pool.fetch("SELECT user_id, name, role_name FROM users")

        for user in users:
            user_id, name, role_name = user["user_id"], user["name"], user["role_name"]
            await ctx.send(f"{user_id} | <@{user_id}> | {name} | {role_name}")
        
        await ctx.send(f"**Done ({len(users)} users)**")
    
    @commands.hybrid_command()
    @commands.has_guild_permissions(administrator=True)
    async def remuser(self, ctx: commands.Context, user: discord.User):
        await ctx.defer(ephemeral=False)

        # Check that the user is in the DB
        user_db = await self.bot.pool.fetchval("SELECT user_id FROM users WHERE user_id = $1", str(user.id))

        if not user_db:
            return await ctx.send("User is not in the database")

        await self.bot.pool.execute("DELETE FROM users WHERE user_id = $1", str(user.id))

        await ctx.send(f"Removed user {user.mention} from the database", allowed_mentions=None)
    
    @commands.hybrid_command()
    @commands.has_guild_permissions(administrator=True)
    async def editname(self, ctx: commands.Context, user: discord.Member, name: str):
        await ctx.defer(ephemeral=False)

        if len(name.split(" ")) != 2:
            return await ctx.send("Name must be in the format ``<first name> <last name>``")
        
        name = name.title()

        await self.bot.pool.execute("UPDATE users SET name = $1 WHERE user_id = $2", name, str(user.id))

        await ctx.send(f"Updated name for {user.mention} to {name}", allowed_mentions=None)

    @tasks.loop(minutes=15)
    async def sanity_check(self):
        logging.info("Checking member names")

        # Get all members
        members = await self.bot.pool.fetch("SELECT user_id, name FROM users")

        if len(self.bot.guilds) > 1:
            # Leave all guilds
            for guild in self.bot.guilds:
                if guild.id != self.bot.config.guild_id:
                    await guild.leave()

        guild = self.bot.guilds[0]

        for member in members:
            user_id, name = member["user_id"], member["name"]

            user = guild.get_member(int(user_id))

            if not user:
                continue

            if user.nick != name:
                if guild.owner_id == user.id:
                    logging.warn(f"Skipping guild owner {user.name} [{user.nick}] -> {name}")
                    continue

                logging.info(f"Changed {user.nick} to {name} (mismatched name and nick)")
                await user.edit(nick=name)

        logging.info("Done checking member names")

    @sanity_check.before_loop
    async def before_sanity_check(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command()
    @commands.has_guild_permissions(administrator=True)
    @discord.app_commands.choices(
        dept=[
            discord.app_commands.Choice(name=name, value=name) for name in roles.keys()
        ]
    )
    @discord.app_commands.describe(
        name="The name of the person in real life"
    )
    async def assign(
        self, 
        ctx: commands.Context, 
        user: discord.Member, 
        name: str,
        dept: str, 
        hod: bool,
        reassign: bool = False
    ):
        await ctx.defer(ephemeral=False)

        if len(name.split(" ")) != 2:
            return await ctx.send("Name must be in the format ``<first name> <last name>``")

        name = name.title()

        name_db = await self.bot.pool.fetchval("SELECT name FROM users WHERE user_id = $1", str(user.id))

        if name_db and name_db != name:
            return await ctx.send(f"User already has a name in the DB: {name_db}. Set ``/editname`` to True to change a users name.")

        if reassign:
            # Delete from DB
            await self.bot.pool.execute("DELETE FROM users WHERE user_id = $1", str(user.id))

            # Remove all roles
            roles_to_rem = []
            for role in user.roles:
                if role.name.lower() not in protected_roles:
                    roles_to_rem.append(role)
            
            await user.remove_roles(*roles_to_rem, reason="Reassigning user department")            

        # Find HOD role by name
        hod_role: discord.Role = discord.utils.get(ctx.guild.roles, name="HOD")

        if not hod_role:
            return await ctx.send("HOD role not found on discord")
        
        if not roles.get(dept):
            return await ctx.send(f"Department {dept} not found")

        role: discord.Role = discord.utils.get(ctx.guild.roles, name=dept)

        if not role:
            return await ctx.send("Role not found on discord")

        # Check db to see if a user is alr in another dept
        row = await self.bot.pool.fetchval("SELECT role_name FROM users WHERE user_id = $1", str(user.id))

        if row and row != dept:
            return await ctx.send(f"User is already in another department ({row}). Set ``reassign`` to True to change a users department or HOD status.")

        # Save to DB
        await self.bot.pool.execute("INSERT INTO users (user_id, role_name, is_hod, name) VALUES ($1, $2, $3, #4)", str(user.id), dept, hod, name)    

        give_roles = [role]
        if hod:
            give_roles.append(hod_role)
        
        await user.add_roles(*give_roles, reason=f"Dept assigned: {dept} (hod={hod})")

        await ctx.send(f"Assigned {user.mention} to {dept} department, hod={hod}", allowed_mentions=None)

    @commands.hybrid_command()
    @commands.is_owner()
    async def buildserver(self, ctx: commands.Context):
        await ctx.send("Building server channels, please wait...")

        protected_cats = [
            "information",
            "general",
            "admin"
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

        hod = await ctx.guild.create_role(name="HOD")

        for name, chan_name in self.bot.roles.items():
            await ctx.send(f"Creating department {name}...")
            role = await ctx.guild.create_role(name=name, hoist=True)

            cat = await ctx.guild.create_category(name, overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=False,
                    connect=False
                ),
                hod: discord.PermissionOverwrite(
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

            await your_dep.send(f"""If you can see this channel, it means that you are a part of the '{name}' department!
            
**This channel is a system channel created by the bot and as such no one (other than admins), not even HOD's can send messages here**""")

            await ctx.guild.create_text_channel(f"{chan_name}-announce", category=cat, overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                hod: discord.PermissionOverwrite(send_messages=True),
            }, topic=f"Announcements for the '{name}' department")
            await ctx.guild.create_text_channel(chan_name, category=cat)
            await ctx.guild.create_voice_channel(name, category=cat)
            await ctx.guild.create_text_channel(f"{chan_name}-input", category=cat, overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            })

        # Select all user roles
        await ctx.send("**Step 3: Assign roles to users**")

        rows = await self.bot.pool.fetch("SELECT user_id, role_name, name, is_hod FROM users")

        assigned = 1

        for row in rows:
            if assigned % 10 == 0:
                await ctx.send(f"Sleeping for 3 seconds to avoid rl's [{assigned}/{len(rows)}]")
                await asyncio.sleep(3)

            await ctx.send(f"Assigning {row['user_id']} to {row['role_name']} (hod={row['is_hod']}) [{assigned}/{len(rows)}]")
            try:
                user = ctx.guild.get_member(int(row["user_id"]))
                if not user:
                    continue
                
                if not user.nick or user.nick != row["name"]:
                    await user.edit(nick=row["name"], reason="Nickname mismatch")

            except:
                continue

            if not roles.get(row["role_name"]):
                await ctx.send(f"Department {row['role_name']} not found, skipping...")

            role: discord.Role = discord.utils.get(ctx.guild.roles, name=row["role_name"])

            if not role:
                continue   

            give_roles = [role]
            if row["is_hod"]:
                give_roles.append(hod)

            await user.add_roles(*give_roles, reason="Rebuilding server")

            assigned += 1

        await ctx.send(f"Assigned {len(rows)} users to their respective departments")

        await ctx.send("**Done!**")

async def setup(bot: Vivum):
    await bot.add_cog(Admin(bot))